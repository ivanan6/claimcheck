"""
Agent 3: Auditor
Cross-checks what front-desk staff entered on the bill against what Agent 1 and
Agent 2 found. Makes the final approved/rejected decision with concrete fix
instructions.

It has two phases:
  1. Deterministic checks (Python code) - catch obvious errors reliably.
  2. LLM auditor - catches softer findings that require language interpretation.
Results are merged and deduplicated by (issue_type, line_item_cpt).
"""
import json
import time
from datetime import date
from typing import List

from models import (
    AuditIssue,
    BillLineItem,
    ContractRule,
    ExtractedClinicalFinding,
)

from .llm_client import call_json, is_mock_mode

# Default time limit for a duplicate procedure (in days) if it cannot be parsed
# from the contract. Covers rules like the MRI 6-month limit.
_DEFAULT_PROCEDURE_COOLDOWN_DAYS = 180

SYSTEM_PROMPT = """You are a healthcare claim auditor.

Return ONLY a valid JSON array. No markdown. No wrapper object.
Return at most 3 issues. If there are no issues, return [].

Allowed issue_type values:
- missing_icd10_justification
- icd10_procedure_mismatch
- contract_limit_violation
- duplicate_billing
- missing_required_documentation

Object shape:
{
  "severity": "error" or "warning",
  "line_item_cpt": "procedure code",
  "issue_type": "one allowed value",
  "explanation": "short English sentence",
  "suggested_fix": {"action": "..."}
}

Use missing_required_documentation when required attachments are missing."""


def _deterministic_checks(
    findings: List[ExtractedClinicalFinding],
    bill_items: List[BillLineItem],
    patient_history: dict,
    supporting_documents: List[str] | None = None,
) -> List[AuditIssue]:
    """Guaranteed checks the LLM must not miss: empty ICD-10 lists, procedures
    repeated before the cooldown period expires, etc."""
    issues: List[AuditIssue] = []
    docs = [d.lower() for d in (supporting_documents or [])]

    # Check 1: empty ICD-10 code list on any line item.
    suggested_codes = [
        f.suggested_icd10 for f in findings if f.suggested_icd10
    ]
    for item in bill_items:
        if not item.icd10_codes:
            issues.append(
                AuditIssue(
                    severity="error",
                    line_item_cpt=item.cpt_code,
                    issue_type="missing_icd10_justification",
                    explanation=(
                        f"Line item '{item.description}' (CPT {item.cpt_code}) "
                        "has no ICD-10 code. The insurance contract requires at least "
                        "one diagnostic code to justify the procedure."
                    ),
                    suggested_fix={
                        "action": "add_icd10",
                        "to_cpt": item.cpt_code,
                        "codes": suggested_codes[:3] or ["R10.9"],
                    },
                )
            )

    # Check 2: procedure from patient_history repeated before the cooldown period.
    today = date.today()
    for item in bill_items:
        for prev in patient_history.get("previous_procedures", []):
            if prev.get("cpt") != item.cpt_code:
                continue
            try:
                prev_date = date.fromisoformat(prev["date"])
            except (ValueError, KeyError, TypeError):
                continue
            days_ago = (today - prev_date).days
            if 0 <= days_ago < _DEFAULT_PROCEDURE_COOLDOWN_DAYS:
                issues.append(
                    AuditIssue(
                        severity="error",
                        line_item_cpt=item.cpt_code,
                        issue_type="contract_limit_violation",
                        explanation=(
                            f"Patient already had procedure '{item.description}' "
                            f"(CPT {item.cpt_code}) on {prev['date']} - only "
                            f"{days_ago} days ago. The contract requires a minimum "
                            f"gap of {_DEFAULT_PROCEDURE_COOLDOWN_DAYS} days. "
                            "Insurance will NOT cover this - the procedure must not "
                            "be scheduled without prior agreement with the patient."
                        ),
                        suggested_fix={
                            "action": "remove_line",
                            "cpt": item.cpt_code,
                        },
                    )
                )
                break  # one history hit per line item is enough

    # Check 3: physical therapy claims often fail because required attachments
    # are missing even when CPT and ICD-10 codes are correct.
    for item in bill_items:
        if item.cpt_code not in ("97110", "PROC-PT-THEREX"):
            continue

        missing_docs: list[str] = []
        has_referral = any("referral" in d for d in docs)
        has_pt_eval = any(
            "physical_therapy_evaluation" in d
            or "physical therapy evaluation" in d
            or "pt_evaluation" in d
            for d in docs
        )
        has_progress = any("progress" in d for d in docs)

        if not has_referral:
            missing_docs.append("physician referral")
        if not has_pt_eval:
            missing_docs.append("initial physical therapy evaluation with treatment plan")
        if item.quantity > 4 and not has_progress:
            missing_docs.append("progress report for more than 4 sessions")

        if missing_docs:
            issues.append(
                AuditIssue(
                    severity="error",
                    line_item_cpt=item.cpt_code,
                    issue_type="missing_required_documentation",
                    explanation=(
                        f"Line item '{item.description}' (CPT {item.cpt_code}) has valid "
                        "diagnosis codes, but the policy requires additional documents "
                        "before billing. Missing: "
                        f"{', '.join(missing_docs)}. Insurance would likely deny the claim "
                        "as incomplete."
                    ),
                    suggested_fix={
                        "action": "attach_documents",
                        "to_cpt": item.cpt_code,
                        "documents": missing_docs,
                    },
                )
            )

    return issues


def _merge_issues(*lists: List[AuditIssue]) -> List[AuditIssue]:
    """Merge issues from multiple sources and deduplicate by (issue_type, line_item_cpt)."""
    seen: set[tuple[str, str]] = set()
    missing_doc_cpts: set[str] = set()
    merged: List[AuditIssue] = []
    for issues in lists:
        for issue in issues:
            if (
                issue.issue_type == "contract_limit_violation"
                and issue.line_item_cpt in missing_doc_cpts
            ):
                continue
            key = (issue.issue_type, issue.line_item_cpt)
            if key in seen:
                continue
            seen.add(key)
            merged.append(issue)
            if issue.issue_type == "missing_required_documentation":
                missing_doc_cpts.add(issue.line_item_cpt)
    return merged


def _has_contract_limit_evidence(issue: AuditIssue, patient_history: dict) -> bool:
    previous = patient_history.get("previous_procedures", [])
    if any(prev.get("cpt") == issue.line_item_cpt for prev in previous):
        return True

    text = f"{issue.explanation} {issue.suggested_fix}".lower()
    return any(
        marker in text
        for marker in (
            "previous",
            "repeat",
            "already had",
            "180",
            "6 months",
            "six months",
            "prior authorization",
        )
    )


def run(
    findings: List[ExtractedClinicalFinding],
    rules: List[ContractRule],
    bill_items: List[BillLineItem],
    patient_history: dict,
    supporting_documents: List[str] | None = None,
) -> List[AuditIssue]:
    """Run Agent 3 with the previous two agents' output and the original bill."""
    deterministic = _deterministic_checks(
        findings, bill_items, patient_history, supporting_documents
    )

    # ---- MOCK MODE (fallback) ----
    if is_mock_mode():
        from mock_responses import agent3_mock

        time.sleep(0.8)
        return _merge_issues(
            deterministic,
            agent3_mock(bill_items, patient_history, supporting_documents),
        )

    # ---- LLM CALL ----
    payload = {
        "agent1_clinical_findings": [f.model_dump() for f in findings],
        "agent2_contract_rules": [r.model_dump() for r in rules],
        "actual_bill_items": [b.model_dump() for b in bill_items],
        "patient_history": patient_history,
        "supporting_documents": supporting_documents or [],
    }

    user_prompt = (
        "Here is all the data you need to cross-check:\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n\nMake a decision and return the list of problems (or an empty array if everything is fine)."
    )

    try:
        raw = call_json(SYSTEM_PROMPT, user_prompt, max_tokens=768)
    except Exception as e:
        # If the LLM fails, deterministic checks still proceed.
        print(f"[auditor] LLM call failed: {e}", flush=True)
        return deterministic

    if isinstance(raw, dict):
        if "issues" in raw:
            raw = raw["issues"]
        elif "problems" in raw:
            raw = raw["problems"]
        elif "errors" in raw:
            raw = raw["errors"]
    if not isinstance(raw, list):
        raw = [raw] if raw else []

    llm_issues: List[AuditIssue] = []
    for item in raw:
        try:
            issue = AuditIssue(**item)
            if (
                issue.issue_type == "contract_limit_violation"
                and not _has_contract_limit_evidence(issue, patient_history)
            ):
                continue
            llm_issues.append(issue)
        except Exception:
            continue

    return _merge_issues(deterministic, llm_issues)
