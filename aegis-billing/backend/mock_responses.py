"""
Pripremljeni mock odgovori (fallback) - koriste se SAMO ako MOCK_MODE=true
u .env-u. Za pravi demo koristimo Gemini API. Ovo je tu kao osiguranje
ako uzivo na pitch-u nesto pukne sa API-jem.

9 odgovora ukupno (3 agenta x 3 scenarija). Dispatch po sadrzaju ulaza.
"""
from typing import List

from models import AuditIssue, BillLineItem, ContractRule, ExtractedClinicalFinding


def _scenario_from_cpts(cpt_codes: List[str]) -> str:
    if "76700" in cpt_codes:
        return "A"
    if "70551" in cpt_codes:
        return "C"
    if any(c in cpt_codes for c in ("99396", "85025", "99397")):
        return "B"
    return "B"


def _scenario_from_note(text: str) -> str:
    t = text.lower()
    if "stomak" in t or "rebrani luk" in t or "abdomen" in t:
        return "A"
    if "glavobolj" in t or "mri mozga" in t:
        return "C"
    if "sistematski" in t or "rutinski" in t or "krvna slika" in t:
        return "B"
    return "B"


# ============================================================================
# AGENT 1 (Medical Coder) mocks
# ============================================================================

AGENT1_MOCKS = {
    "A": [
        ExtractedClinicalFinding(
            finding="Akutni abdominalni bol",
            suggested_icd10="R10.9",
            confidence=0.94,
            evidence_quote="ostrog probadajuceg bola ispod levog rebranog luka koji traje vec 3 dana",
        ),
        ExtractedClinicalFinding(
            finding="Smanjen apetit",
            suggested_icd10="R63.0",
            confidence=0.78,
            evidence_quote="apetit smanjen",
        ),
        ExtractedClinicalFinding(
            finding="Osetljivost leve hipohondrijske regije",
            suggested_icd10="R10.12",
            confidence=0.88,
            evidence_quote="palpacijom uocena osetljivost u levom hipohondrijumu",
        ),
    ],
    "B": [
        ExtractedClinicalFinding(
            finding="Rutinski sistematski pregled bez tegoba",
            suggested_icd10="Z00.00",
            confidence=0.97,
            evidence_quote="rutinski godisnji sistematski pregled, pacijentkinja se ne zali na tegobe",
        ),
    ],
    "C": [
        ExtractedClinicalFinding(
            finding="Ucestale glavobolje frontalne lokalizacije",
            suggested_icd10="R51",
            confidence=0.92,
            evidence_quote="ucestale glavobolje u poslednjih mesec dana, tupe, lokalizovane u frontalnoj regiji",
        ),
        ExtractedClinicalFinding(
            finding="Nema fokalnih neuroloskih ispada",
            suggested_icd10="Z01.84",
            confidence=0.71,
            evidence_quote="neuroloski pregled bez fokalnih ispada",
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
                "Ultrazvucne procedure (CPT 76700-76770): obavezna je najmanje "
                "JEDNA ICD-10 sifra koja opravdava indikaciju"
            ),
        ),
        ContractRule(
            rule_id="ART-7.1",
            procedure_cpt="76700",
            requires_icd10_categories=["any-diagnostic"],
            additional_constraint="Genericki uslov - sve procedure moraju imati klinicku indikaciju",
            source_quote=(
                "Sve dijagnosticke procedure moraju biti potkrepljene najmanje jednom "
                "dijagnostickom ICD-10 sifrom koja je medicinski povezana sa procedurom"
            ),
        ),
    ],
    "B": [
        ContractRule(
            rule_id="ART-4.2.3",
            procedure_cpt="99396",
            requires_icd10_categories=["Z00.00"],
            additional_constraint="Pokriven jednom godisnje za odrasle",
            source_quote=(
                "Rutinski godisnji pregled (CPT 99396, 99397): pokriven jednom godisnje "
                "za odrasle pacijente, prihvatljiva je Z00.00"
            ),
        ),
        ContractRule(
            rule_id="ART-5.1.1",
            procedure_cpt="85025",
            requires_icd10_categories=["Z00.00", "D50-D89", "B95-B97"],
            additional_constraint=None,
            source_quote=(
                "Kompletna krvna slika (CPT 85025): pokrivena uz rutinski pregled "
                "ili konkretan klinicki razlog"
            ),
        ),
    ],
    "C": [
        ContractRule(
            rule_id="ART-4.2.2",
            procedure_cpt="70551",
            requires_icd10_categories=["G00-G99", "R51", "S06.x"],
            additional_constraint="Maksimalno 1 MRI mozga u periodu od 6 meseci po pacijentu",
            source_quote=(
                "MRI procedure (CPT 70551-70553): ogranicenje maksimalno JEDAN MRI "
                "mozga u periodu od 6 meseci po pacijentu"
            ),
        ),
        ContractRule(
            rule_id="ART-4.2.2-EXC",
            procedure_cpt="70551",
            requires_icd10_categories=["I60-I69"],
            additional_constraint="Izuzetak od ogranicenja 6 meseci",
            source_quote=(
                "IZUZETAK: ne primenjuje se ako postoji ICD-10 sifra iz kategorije "
                "I60-I69 (cerebrovaskularne bolesti)"
            ),
        ),
    ],
}


def agent2_mock(cpt_codes: List[str]) -> List[ContractRule]:
    return AGENT2_MOCKS[_scenario_from_cpts(cpt_codes)]


# ============================================================================
# AGENT 3 (Auditor) mocks
# ============================================================================

def agent3_mock(bill_items: List[BillLineItem], patient_history: dict) -> List[AuditIssue]:
    cpts = [b.cpt_code for b in bill_items]
    scn = _scenario_from_cpts(cpts)

    if scn == "A":
        for item in bill_items:
            if item.cpt_code == "76700" and len(item.icd10_codes) == 0:
                return [
                    AuditIssue(
                        severity="error",
                        line_item_cpt="76700",
                        issue_type="missing_icd10_justification",
                        explanation=(
                            "Stavka ultrazvuk abdomena (CPT 76700) nema povezanu "
                            "ICD-10 sifru. Ugovor (ART-4.2.1) zahteva najmanje jednu "
                            "dijagnosticku sifru. Agent 1 je iz nalaza izvukao R10.9 "
                            "(abdominalni bol) - predlazem dodavanje."
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
                        "Pacijent je vec imao MRI mozga (CPT 70551) 2026-03-15 "
                        "(pre 2 meseca). Ugovor ART-4.2.2 ogranicava na 1 MRI u 6 meseci. "
                        "Izuzetak vazi samo uz ICD-10 iz kategorije I60-I69 - sto nije "
                        "slucaj. Potrebna je medicinska dokumentacija ili odobrenje."
                    ),
                    suggested_fix={
                        "action": "request_documentation",
                        "details": (
                            "Trazi se pisano obrazlozenje lekara zasto je MRI "
                            "ponovljen pre isteka 6 meseci."
                        ),
                    },
                )
            ]
        return []

    return []
