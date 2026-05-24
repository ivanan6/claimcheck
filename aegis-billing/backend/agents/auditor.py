"""
Agent 3: Auditor
Unakrsno proverava sta je sestra unela na racunu sa onim sto su Agent 1 i Agent 2 nasli.
Donosi konacnu odluku: approved ili rejected, sa konkretnim fix uputstvima.
"""
import json
import time
from typing import List

from models import (
    AuditIssue,
    BillLineItem,
    ContractRule,
    ExtractedClinicalFinding,
)

from .llm_client import call_json, is_mock_mode

SYSTEM_PROMPT = """Ti si revizor zdravstvenih racuna. Tvoj zadatak je da uporedis:
1. Klinicke nalaze izvucene iz lekarskog teksta (sta je STVARNO nadjeno kod pacijenta)
2. Pravila iz ugovora osiguranja (sta osiguranje ZAHTEVA za isplatu)
3. Stavke racuna koje je sestra unela (sta je STVARNO upisano na racun)
4. Istoriju pacijenta (prethodne procedure)

Tvoj cilj je da uocis DA LI postoji nesklad i da predlozis tacnu ispravku.

Vrati validan JSON niz objekata sa sledecim poljima:
- severity: "error" ili "warning"
- line_item_cpt: CPT kod stavke na koju se odnosi problem
- issue_type: jedan od: "missing_icd10_justification", "icd10_procedure_mismatch", \
"contract_limit_violation", "duplicate_billing"
- explanation: jasno objasnjenje sta nije u redu (na srpskom)
- suggested_fix: objekat sa konkretnom akcijom, npr:
    {"action": "add_icd10", "codes": ["R10.9"], "to_cpt": "76700"}
    {"action": "remove_line", "cpt": "70551"}
    {"action": "request_documentation", "details": "..."}

Ako NEMA problema, vrati prazan niz: []"""


def run(
    findings: List[ExtractedClinicalFinding],
    rules: List[ContractRule],
    bill_items: List[BillLineItem],
    patient_history: dict,
) -> List[AuditIssue]:
    """Pokrece Agent 3 sa output-om prethodna dva agenta + originalnim racunom."""
    # ---- MOCK MODE (fallback) ----
    if is_mock_mode():
        from mock_responses import agent3_mock

        time.sleep(0.8)
        return agent3_mock(bill_items, patient_history)

    # ---- GEMINI POZIV ----
    payload = {
        "agent1_clinical_findings": [f.model_dump() for f in findings],
        "agent2_contract_rules": [r.model_dump() for r in rules],
        "actual_bill_items": [b.model_dump() for b in bill_items],
        "patient_history": patient_history,
    }

    user_prompt = (
        "Evo svih podataka koje treba da unakrsno proveris:\n\n"
        + json.dumps(payload, ensure_ascii=False, indent=2)
        + "\n\nDonesi odluku i vrati listu problema (ili prazan niz ako je sve u redu)."
    )

    raw = call_json(SYSTEM_PROMPT, user_prompt, max_tokens=2048)

    if isinstance(raw, dict) and "issues" in raw:
        raw = raw["issues"]
    if not isinstance(raw, list):
        raw = [raw] if raw else []

    issues = []
    for item in raw:
        try:
            issues.append(AuditIssue(**item))
        except Exception:
            continue
    return issues
