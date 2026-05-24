"""
Tri pripremljena scenarija za demo snimak.

Scenario A (hero) - sestra je zaboravila ICD-10 sifru za bol u stomaku.
                    Agent 1 hvata kontekst iz teksta lekara, Agent 3 nudi 1-click fix.
Scenario B (clean) - sve je u redu, prolazi kroz pipeline za par sekundi.
Scenario C (graph rag hero) - MRI mozga koji krsi ogranicenje ugovora (6 meseci).
                              Agent 2 hvata krsenje pravila iz ugovora.
"""
from models import BillLineItem, EDI837Packet, Patient


def scenario_a_missing_icd10() -> EDI837Packet:
    return EDI837Packet(
        packet_id="EDI-2026-05-24-00781",
        clinic_name="Poliklinika Sveti Sava",
        clinic_id="RS-CLI-00214",
        patient=Patient(
            patient_id="PAT-44871",
            full_name="Marko Petrovic",
            date_of_birth="1978-03-12",
            insurance_id="GH-887-441-22",
        ),
        doctor_note=(
            "Pacijent dosao na pregled zbog ostrog probadajuceg bola "
            "ispod levog rebranog luka koji traje vec 3 dana. "
            "Bol se pojacava pri dubokom udisaju i savijanju. "
            "Nema groznice, nema povracanja. Apetit smanjen. "
            "Palpacijom uocena osetljivost u levom hipohondrijumu. "
            "Indikujem ultrazvuk abdomena radi iskljucivanja patologije "
            "slezine i pankreasa. Pacijenta uputiti na kontrolu nakon nalaza."
        ),
        bill_items=[
            BillLineItem(
                cpt_code="76700",
                description="Ultrazvuk abdomena, kompletan",
                icd10_codes=[],  # GRESKA: sestra je zaboravila ICD-10!
                unit_price_eur=85.00,
                quantity=1,
            ),
        ],
        insurance_company="Global Health Insurance",
        submitted_at="2026-05-24T09:14:33Z",
    )


def scenario_b_clean_bill() -> EDI837Packet:
    return EDI837Packet(
        packet_id="EDI-2026-05-24-00782",
        clinic_name="Poliklinika Sveti Sava",
        clinic_id="RS-CLI-00214",
        patient=Patient(
            patient_id="PAT-39102",
            full_name="Jelena Nikolic",
            date_of_birth="1985-07-22",
            insurance_id="GH-552-118-09",
        ),
        doctor_note=(
            "Rutinski godisnji sistematski pregled. "
            "Pacijentkinja se ne zali na tegobe. "
            "Krvni pritisak 120/80 mmHg. Telesna temperatura 36.6 C. "
            "Auskultacijom srca i pluca nalaz uredan. "
            "Preporucujem kompletnu krvnu sliku u sklopu sistematskog pregleda."
        ),
        bill_items=[
            BillLineItem(
                cpt_code="99396",
                description="Periodicni sistematski pregled, odrasli 40-64 god",
                icd10_codes=["Z00.00"],
                unit_price_eur=120.00,
                quantity=1,
            ),
            BillLineItem(
                cpt_code="85025",
                description="Kompletna krvna slika sa diferencijalom",
                icd10_codes=["Z00.00"],
                unit_price_eur=25.00,
                quantity=1,
            ),
        ],
        insurance_company="Global Health Insurance",
        submitted_at="2026-05-24T09:21:07Z",
    )


def scenario_c_contract_violation() -> EDI837Packet:
    return EDI837Packet(
        packet_id="EDI-2026-05-24-00783",
        clinic_name="Poliklinika Sveti Sava",
        clinic_id="RS-CLI-00214",
        patient=Patient(
            patient_id="PAT-21055",
            full_name="Stefan Jovanovic",
            date_of_birth="1990-11-04",
            insurance_id="GH-201-993-71",
        ),
        doctor_note=(
            "Pacijent se zali na ucestale glavobolje u poslednjih mesec dana. "
            "Glavobolje su tupe, lokalizovane u frontalnoj regiji, traju 2-4 sata. "
            "Neuroloski pregled bez fokalnih ispada. "
            "S obzirom da je pacijent imao MRI mozga pre 2 meseca sa urednim nalazom, "
            "ali zbog pojacanog intenziteta glavobolja, indikujem kontrolni MRI mozga."
        ),
        bill_items=[
            BillLineItem(
                cpt_code="70551",
                description="MRI mozga bez kontrasta",
                icd10_codes=["R51"],
                unit_price_eur=320.00,
                quantity=1,
            ),
        ],
        insurance_company="Global Health Insurance",
        submitted_at="2026-05-24T09:38:51Z",
    )


SCENARIOS = {
    "scenario_a": {
        "name": "Greska: nedostaje ICD-10 sifra",
        "subtitle": "Sestra je zaboravila da poveze simptome sa procedurom",
        "loader": scenario_a_missing_icd10,
        "expected_outcome": "rejected_with_autofix",
    },
    "scenario_b": {
        "name": "Cist racun",
        "subtitle": "Rutinski pregled koji prolazi kroz AI filter",
        "loader": scenario_b_clean_bill,
        "expected_outcome": "approved",
    },
    "scenario_c": {
        "name": "Krsenje ugovora",
        "subtitle": "MRI mozga koji krsi vremensko ogranicenje od 6 meseci",
        "loader": scenario_c_contract_violation,
        "expected_outcome": "rejected_contract",
    },
}


PATIENT_HISTORY = {
    "PAT-21055": {
        "previous_procedures": [
            {"cpt": "70551", "date": "2026-03-15", "result": "uredan nalaz"}
        ]
    },
}


def get_patient_history(patient_id: str) -> dict:
    return PATIENT_HISTORY.get(patient_id, {"previous_procedures": []})
