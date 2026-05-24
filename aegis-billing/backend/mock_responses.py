"""
Prepared mock responses (fallback) - used ONLY if MOCK_MODE=true in .env.
For the real demo we use the Gemini API. This is here as insurance in case
something breaks with the API during the live pitch.

12 responses total (3 agents x 4 scenarios). Dispatch by input content.
"""
from typing import List

from models import AuditIssue, BillLineItem, ContractRule, ExtractedClinicalFinding


def _scenario_from_cpts(cpt_codes: List[str]) -> str:
    if "76700" in cpt_codes:
        return "A"
    if "70551" in cpt_codes:
        return "C"
    if "97110" in cpt_codes:
        return "D"
    if any(c in cpt_codes for c in ("99396", "85025", "99397")):
        return "B"
    return "B"


def _scenario_from_note(text: str) -> str:
    t = text.lower()
    if "stomach" in t or "costal arch" in t or "abdomen" in t:
        return "A"
    if "headache" in t or "brain mri" in t:
        return "C"
    if "meniscus" in t or "therapeutic exercise" in t or "knee" in t:
        return "D"
    if "physical" in t or "routine" in t or "blood count" in t:
        return "B"
    return "B"


# ============================================================================
# AGENT 1 (Medical Coder) mocks
# ============================================================================

AGENT1_MOCKS = {
    "A": [
        ExtractedClinicalFinding(
            finding="Acute abdominal pain",
            suggested_icd10="R10.9",
            confidence=0.94,
            evidence_quote="sharp stabbing pain below the left costal arch lasting 3 days",
        ),
        ExtractedClinicalFinding(
            finding="Decreased appetite",
            suggested_icd10="R63.0",
            confidence=0.78,
            evidence_quote="Decreased appetite",
        ),
        ExtractedClinicalFinding(
            finding="Tenderness in the left hypochondrium",
            suggested_icd10="R10.12",
            confidence=0.88,
            evidence_quote="Palpation revealed tenderness in the left hypochondrium",
        ),
    ],
    "B": [
        ExtractedClinicalFinding(
            finding="Routine annual physical examination without complaints",
            suggested_icd10="Z00.00",
            confidence=0.97,
            evidence_quote="Routine annual physical examination. Patient reports no complaints.",
        ),
    ],
    "C": [
        ExtractedClinicalFinding(
            finding="Frequent headaches localized in the frontal region",
            suggested_icd10="R51",
            confidence=0.92,
            evidence_quote="frequent headaches over the past month. Headaches are dull, localized in the frontal region",
        ),
        ExtractedClinicalFinding(
            finding="No focal neurological deficits",
            suggested_icd10="Z01.84",
            confidence=0.71,
            evidence_quote="Neurological examination shows no focal deficits",
        ),
    ],
    "D": [
        ExtractedClinicalFinding(
            finding="Postoperative right knee meniscus rehabilitation",
            suggested_icd10="S83.241D",
            confidence=0.91,
            evidence_quote="3 weeks after arthroscopic repair of the right knee meniscus",
        ),
        ExtractedClinicalFinding(
            finding="Right knee pain and limited range of motion",
            suggested_icd10="M25.561",
            confidence=0.86,
            evidence_quote="stiffness, limited flexion to 95 degrees, and pain during stairs",
        ),
    ],
}


def agent1_mock(doctor_note: str) -> List[ExtractedClinicalFinding]:
    return AGENT1_MOCKS[_scenario_from_note(doctor_note)]


# ============================================================================
# AGENT 2 (Contract Lawyer) mocks
# ============================================================================

AGENT2_MOCKS = {
    "A": [
        ContractRule(
            rule_id="ART-4.2.1",
            procedure_cpt="76700",
            requires_icd10_categories=["R10.x", "R19.x", "K00-K93", "N00-N99"],
            additional_constraint=None,
            source_quote=(
                "Ultrasound procedures (CPT 76700-76770): at least ONE ICD-10 "
                "code is required to justify the indication"
            ),
        ),
        ContractRule(
            rule_id="ART-7.1",
            procedure_cpt="76700",
            requires_icd10_categories=["any-diagnostic"],
            additional_constraint="Generic requirement - all procedures must have a clinical indication",
            source_quote=(
                "All diagnostic procedures must be supported by at least one "
                "diagnostic ICD-10 code medically related to the procedure"
            ),
        ),
    ],
    "B": [
        ContractRule(
            rule_id="ART-4.2.3",
            procedure_cpt="99396",
            requires_icd10_categories=["Z00.00"],
            additional_constraint="Covered once per year for adults",
            source_quote=(
                "Routine annual physical examination (CPT 99396, 99397): covered once "
                "per year for adult patients, Z00.00 is accepted"
            ),
        ),
        ContractRule(
            rule_id="ART-5.1.1",
            procedure_cpt="85025",
            requires_icd10_categories=["Z00.00", "D50-D89", "B95-B97"],
            additional_constraint=None,
            source_quote=(
                "Complete blood count (CPT 85025): covered with a routine examination "
                "or a specific clinical reason"
            ),
        ),
    ],
    "C": [
        ContractRule(
            rule_id="ART-4.2.2",
            procedure_cpt="70551",
            requires_icd10_categories=["G00-G99", "R51", "S06.x"],
            additional_constraint="Maximum 1 brain MRI within 6 months per patient",
            source_quote=(
                "MRI procedures (CPT 70551-70553): limit of maximum ONE brain MRI "
                "within 6 months per patient"
            ),
        ),
        ContractRule(
            rule_id="ART-4.2.2-EXC",
            procedure_cpt="70551",
            requires_icd10_categories=["I60-I69"],
            additional_constraint="Exception to the 6-month limit",
            source_quote=(
                "EXCEPTION: does not apply if there is an ICD-10 code from category "
                "I60-I69 (cerebrovascular diseases)"
            ),
        ),
    ],
    "D": [
        ContractRule(
            rule_id="ART-6.3.1",
            procedure_cpt="97110",
            requires_icd10_categories=["S83.x", "M25.x", "Z47.x"],
            additional_constraint=(
                "Claim package must include physician referral and initial physical "
                "therapy evaluation with treatment plan; more than 4 sessions also "
                "require a progress report."
            ),
            source_quote=(
                "Every claim package must include the physician referral AND the initial "
                "physical therapy evaluation with treatment plan"
            ),
        ),
        ContractRule(
            rule_id="ART-6.3.1-PROGRESS",
            procedure_cpt="97110",
            requires_icd10_categories=["S83.x", "M25.x", "Z47.x"],
            additional_constraint="If billing more than 4 sessions, a progress report must also be attached",
            source_quote="If billing more than 4 sessions, a progress report must also be attached",
        ),
    ],
}


def agent2_mock(cpt_codes: List[str]) -> List[ContractRule]:
    return AGENT2_MOCKS[_scenario_from_cpts(cpt_codes)]


# ============================================================================
# AGENT 3 (Auditor) mocks
# ============================================================================

def agent3_mock(
    bill_items: List[BillLineItem],
    patient_history: dict,
    supporting_documents: List[str] | None = None,
) -> List[AuditIssue]:
    cpts = [b.cpt_code for b in bill_items]
    scn = _scenario_from_cpts(cpts)
    docs = [d.lower() for d in (supporting_documents or [])]

    if scn == "A":
        for item in bill_items:
            if item.cpt_code == "76700" and len(item.icd10_codes) == 0:
                return [
                    AuditIssue(
                        severity="error",
                        line_item_cpt="76700",
                        issue_type="missing_icd10_justification",
                        explanation=(
                            "The abdominal ultrasound line item (CPT 76700) has no linked "
                            "ICD-10 code. The contract (ART-4.2.1) requires at least one "
                            "diagnostic code. Agent 1 extracted R10.9 (abdominal pain) "
                            "from the note - suggest adding it."
                        ),
                        suggested_fix={
                            "action": "add_icd10",
                            "codes": ["R10.9"],
                            "to_cpt": "76700",
                        },
                    )
                ]
        return []

    if scn == "B":
        return []

    if scn == "C":
        prev = patient_history.get("previous_procedures", [])
        had_recent_mri = any(p.get("cpt") == "70551" for p in prev)
        if had_recent_mri:
            return [
                AuditIssue(
                    severity="error",
                    line_item_cpt="70551",
                    issue_type="contract_limit_violation",
                    explanation=(
                        "The patient already had a brain MRI (CPT 70551) on 2026-03-15 "
                        "(2 months ago). Contract ART-4.2.2 limits coverage to 1 MRI in 6 months. "
                        "The exception applies only with an ICD-10 code from category I60-I69, "
                        "which is not the case. Medical documentation or approval is required."
                    ),
                    suggested_fix={
                        "action": "request_documentation",
                        "details": (
                            "Request a written physician explanation for why the MRI "
                            "is repeated before 6 months have passed."
                        ),
                    },
                )
            ]
        return []

    if scn == "D":
        has_referral = any("referral" in d for d in docs)
        has_pt_eval = any(
            "physical_therapy_evaluation" in d
            or "physical therapy evaluation" in d
            or "pt_evaluation" in d
            for d in docs
        )
        has_progress = any("progress" in d for d in docs)
        quantity = sum(item.quantity for item in bill_items if item.cpt_code == "97110")

        missing = []
        if not has_referral:
            missing.append("physician referral")
        if not has_pt_eval:
            missing.append("initial physical therapy evaluation with treatment plan")
        if quantity > 4 and not has_progress:
            missing.append("progress report for more than 4 sessions")

        if missing:
            return [
                AuditIssue(
                    severity="error",
                    line_item_cpt="97110",
                    issue_type="missing_required_documentation",
                    explanation=(
                        "The therapeutic exercise claim has matching CPT and ICD-10 codes, "
                        "but the policy requires additional attachments before billing. "
                        f"Missing: {', '.join(missing)}. The insurer would deny this claim "
                        "as incomplete even though the medical indication is valid."
                    ),
                    suggested_fix={
                        "action": "attach_documents",
                        "documents": missing,
                        "to_cpt": "97110",
                    },
                )
            ]
        return []

    return []
