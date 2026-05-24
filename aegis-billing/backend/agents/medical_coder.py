"""
Agent 1: Medical Coder
Reads free-text physician notes and extracts clinical findings + ICD-10 codes.
"""
import time
from typing import List

from models import ExtractedClinicalFinding

from .llm_client import call_json, is_mock_mode

SYSTEM_PROMPT = """You are a specialized medical coder. Your task is to extract all clinically \
relevant findings from a free-text physician note and suggest the corresponding ICD-10 codes.

Return a valid JSON array of objects with the following fields:
- finding: short description of the finding/symptom in English
- suggested_icd10: ICD-10 code (e.g. "R10.9", "R51", "I63.9")
- confidence: number from 0.0 to 1.0 reflecting confidence
- evidence_quote: exact quote from the text that justifies this code

Example:
[{"finding": "abdominal pain", "suggested_icd10": "R10.9", "confidence": 0.95, \
"evidence_quote": "patient reports sharp abdominal pain"}]"""


def run(doctor_note: str) -> List[ExtractedClinicalFinding]:
    """Run Agent 1 on the physician note."""
    # ---- MOCK MODE (fallback) ----
    if is_mock_mode():
        from mock_responses import agent1_mock

        time.sleep(0.8)  # give the animation time
        return agent1_mock(doctor_note)

    # ---- GEMINI CALL ----
    user_prompt = f"Physician note:\n\n{doctor_note}\n\nExtract clinical findings and ICD-10 codes."
    raw = call_json(SYSTEM_PROMPT, user_prompt)

    if isinstance(raw, dict) and "findings" in raw:
        raw = raw["findings"]
    if not isinstance(raw, list):
        raw = [raw]

    findings = []
    for item in raw:
        try:
            findings.append(ExtractedClinicalFinding(**item))
        except Exception:
            continue
    return findings
