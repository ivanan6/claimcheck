"""
Agent 2: Contract Lawyer (Graph RAG)
Reads the insurance contract text and extracts rules relevant to CPT codes from
the given bill. In production this goes through Amazon Neptune / Vertex AI Search.
"""
import time
from typing import List

from models import ContractRule

from .llm_client import call_json, is_mock_mode

SYSTEM_PROMPT = """You are a lawyer specializing in healthcare insurance contracts. \
You will receive contract text and a list of procedure CPT codes from a bill. Your task is to find \
ALL contract rules that apply to those CPT codes.

Return a valid JSON array of objects with the following fields:
- rule_id: short rule identifier (e.g. "ART-4.2.1", "ART-4.2.2")
- procedure_cpt: CPT code the rule applies to
- requires_icd10_categories: array of ICD-10 category strings (e.g. ["R10.x", "K00-K93"])
- additional_constraint: optional additional condition (e.g. "max 1 in 6 months" or null)
- source_quote: exact quote from the contract confirming this rule"""


def run(contract_text: str, cpt_codes: List[str]) -> List[ContractRule]:
    """Run Agent 2 on the contract and CPT code list."""
    # ---- MOCK MODE (fallback) ----
    if is_mock_mode():
        from mock_responses import agent2_mock

        time.sleep(0.9)
        return agent2_mock(cpt_codes)

    # ---- GEMINI CALL ----
    user_prompt = (
        f"INSURANCE CONTRACT:\n\n{contract_text}\n\n"
        f"CPT CODES FROM THE BILL: {', '.join(cpt_codes)}\n\n"
        f"Extract all rules that apply to these procedures."
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
