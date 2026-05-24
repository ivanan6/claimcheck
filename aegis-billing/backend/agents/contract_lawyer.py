"""
Agent 2: Contract Lawyer (Graph RAG)
Cita tekst ugovora osiguranja i izvlaci pravila relevantna za CPT kodove
iz datog racuna. U produkciji ovo ide kroz Amazon Neptune / Vertex AI Search.
"""
import time
from typing import List

from models import ContractRule

from .llm_client import call_json, is_mock_mode

SYSTEM_PROMPT = """Ti si pravnik specijalizovan za ugovore zdravstvenih osiguranja. \
Dobices tekst ugovora i listu CPT kodova procedura sa racuna. Tvoj zadatak je da pronadjes \
SVA pravila iz ugovora koja se odnose na te CPT kodove.

Vrati validan JSON niz objekata sa sledecim poljima:
- rule_id: kratak identifikator pravila (npr. "ART-4.2.1", "ART-4.2.2")
- procedure_cpt: CPT kod na koji se pravilo odnosi
- requires_icd10_categories: niz string-ova ICD-10 kategorija (npr. ["R10.x", "K00-K93"])
- additional_constraint: opcioni dodatni uslov (npr. "max 1 u 6 meseci" ili null)
- source_quote: doslovan citat iz ugovora koji potvrduje ovo pravilo"""


def run(contract_text: str, cpt_codes: List[str]) -> List[ContractRule]:
    """Pokrece Agent 2 nad ugovorom i listom CPT kodova."""
    # ---- MOCK MODE (fallback) ----
    if is_mock_mode():
        from mock_responses import agent2_mock

        time.sleep(0.9)
        return agent2_mock(cpt_codes)

    # ---- GEMINI POZIV ----
    user_prompt = (
        f"UGOVOR OSIGURANJA:\n\n{contract_text}\n\n"
        f"CPT KODOVI SA RACUNA: {', '.join(cpt_codes)}\n\n"
        f"Izvuci sva pravila koja se odnose na ove procedure."
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
