"""
Agent 1: Medical Coder
Cita slobodan tekst lekara i izvlaci klinicke nalaze + ICD-10 sifre.
"""
import time
from typing import List

from models import ExtractedClinicalFinding

from .llm_client import call_json, is_mock_mode

SYSTEM_PROMPT = """Ti si specijalizovani medicinski koder. Tvoj zadatak je da iz slobodnog teksta \
lekarskog nalaza (pisan na srpskom jeziku) izvuces sve klinicki relevantne nalaze i predlozis \
odgovarajuce ICD-10 sifre.

Vrati validan JSON niz objekata sa sledecim poljima:
- finding: kratak opis nalaza/simptoma (srpski)
- suggested_icd10: ICD-10 sifra (npr. "R10.9", "R51", "I63.9")
- confidence: broj 0.0-1.0 koji odrazava sigurnost
- evidence_quote: doslovan citat iz teksta koji opravdava ovu sifru

Primer:
[{"finding": "bol u stomaku", "suggested_icd10": "R10.9", "confidence": 0.95, \
"evidence_quote": "pacijent se zali na ostar bol u stomaku"}]"""


def run(doctor_note: str) -> List[ExtractedClinicalFinding]:
    """Pokrece Agent 1 nad lekarskim nalazom."""
    # ---- MOCK MODE (fallback) ----
    if is_mock_mode():
        from mock_responses import agent1_mock

        time.sleep(0.8)  # da animacija ima vremena
        return agent1_mock(doctor_note)

    # ---- GEMINI POZIV ----
    user_prompt = f"Lekarski nalaz:\n\n{doctor_note}\n\nIzvuci klinicke nalaze i ICD-10 sifre."
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
