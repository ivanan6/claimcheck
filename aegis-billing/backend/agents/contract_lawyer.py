"""
Agent 2: Contract Lawyer (Graph RAG)
Retrieves relevant payer policy chunks and extracts rules relevant to procedure
codes from the given bill. In production this can move to Chroma, Qdrant,
pgvector, Vertex AI Search, or Amazon Neptune.
"""
import time
from typing import List

from models import ContractRule
from rag.retriever import build_policy_context, retrieve_policy_chunks

from .llm_client import call_json, is_mock_mode

SYSTEM_PROMPT = """You are a lawyer specializing in healthcare insurance contracts. \
You will receive retrieved payer policy excerpts and a list of procedure codes from a bill. \
Your task is to find ALL policy rules that apply to those procedure codes.

Return a valid JSON array of objects with the following fields:
- rule_id: short rule identifier (e.g. "ART-4.2.1", "ART-4.2.2")
- procedure_cpt: procedure code the rule applies to
- requires_icd10_categories: array of diagnosis category strings (e.g. ["S83.x", "M25.x"])
- additional_constraint: optional additional condition (e.g. "max 1 in 6 months" or null)
- source_quote: exact quote from the retrieved policy excerpt confirming this rule"""


def _retrieve_context(
    *,
    payer: str,
    procedure_codes: List[str],
    diagnosis_codes: List[str] | None = None,
    supporting_documents: List[str] | None = None,
    doctor_note: str = "",
) -> str:
    results = retrieve_policy_chunks(
        payer=payer,
        procedure_codes=procedure_codes,
        diagnosis_codes=diagnosis_codes or [],
        supporting_documents=supporting_documents or [],
        doctor_note=doctor_note,
        top_k=5,
    )
    return build_policy_context(results)


def run(
    contract_text: str,
    cpt_codes: List[str],
    *,
    payer: str = "",
    diagnosis_codes: List[str] | None = None,
    supporting_documents: List[str] | None = None,
    doctor_note: str = "",
) -> List[ContractRule]:
    """Run Agent 2 using retrieved policy context and the procedure code list."""
    # ---- MOCK MODE (fallback) ----
    if is_mock_mode():
        from mock_responses import agent2_mock

        time.sleep(0.9)
        return agent2_mock(cpt_codes)

    retrieved_context = _retrieve_context(
        payer=payer,
        procedure_codes=cpt_codes,
        diagnosis_codes=diagnosis_codes,
        supporting_documents=supporting_documents,
        doctor_note=doctor_note,
    )
    policy_context = retrieved_context or contract_text.strip()

    # ---- LLM CALL ----
    user_prompt = (
        f"PAYER: {payer or 'Unknown'}\n\n"
        f"RETRIEVED POLICY EXCERPTS:\n\n{policy_context}\n\n"
        f"PROCEDURE CODES FROM THE BILL: {', '.join(cpt_codes)}\n\n"
        f"DIAGNOSIS CODES FROM THE BILL: {', '.join(diagnosis_codes or [])}\n\n"
        f"SUPPORTING DOCUMENTS ALREADY ATTACHED: {', '.join(supporting_documents or []) or 'none'}\n\n"
        f"Extract all rules that apply to these procedures. Include documentation requirements."
    )
    raw = call_json(SYSTEM_PROMPT, user_prompt, max_tokens=2048)

    if isinstance(raw, dict) and "rules" in raw:
        raw = raw["rules"]
    if not isinstance(raw, list):
        raw = [raw]

    rules = []
    for item in raw:
        try:
            if item.get("additional_constraint") in ("", "null", "None"):
                item["additional_constraint"] = None
            rules.append(ContractRule(**item))
        except Exception:
            continue
    return rules
