"""
Four prepared scenarios for the demo recording.

Scenario A (hero) - nurse forgot the ICD-10 code for stomach pain.
                    Agent 1 captures context from the doctor's note, Agent 3 offers 1-click fix.
Scenario B (clean) - everything is fine, passes through the pipeline in seconds.
Scenario C (graph rag hero) - brain MRI requested before contract's 6-month limit.
                              Agent 2 catches the rule violation from the contract.
Scenario D (missing documents) - bill has the right CPT and ICD-10, but the claim
                                 package is missing policy-required attachments.
"""
from models import BillLineItem, EDI837Packet, Patient


def scenario_a_missing_icd10() -> EDI837Packet:
    return EDI837Packet(
        packet_id="EDI-2026-05-24-00781",
        clinic_name="St. Sava Medical Center",
        clinic_id="RS-CLI-00214",
        patient=Patient(
            patient_id="PAT-44871",
            full_name="Marko Petrovic",
            date_of_birth="1978-03-12",
            insurance_id="GH-887-441-22",
        ),
        doctor_note=(
            "Patient came in for examination due to sharp stabbing pain "
            "below the left costal arch lasting 3 days. "
            "Pain worsens with deep inhalation and bending. "
            "No fever, no vomiting. Decreased appetite. "
            "Palpation revealed tenderness in the left hypochondrium. "
            "Indicating abdominal ultrasound to rule out spleen and pancreas pathology. "
            "Refer patient for follow-up after results."
        ),
        bill_items=[
            BillLineItem(
                cpt_code="76700",
                description="Abdominal ultrasound, complete",
                icd10_codes=[],  # ERROR: nurse forgot ICD-10!
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
        clinic_name="St. Sava Medical Center",
        clinic_id="RS-CLI-00214",
        patient=Patient(
            patient_id="PAT-39102",
            full_name="Jelena Nikolic",
            date_of_birth="1985-07-22",
            insurance_id="GH-552-118-09",
        ),
        doctor_note=(
            "Routine annual physical examination. "
            "Patient reports no complaints. "
            "Blood pressure 120/80 mmHg. Body temperature 36.6 C. "
            "Auscultation of heart and lungs reveals normal findings. "
            "Recommending complete blood count as part of the physical examination."
        ),
        bill_items=[
            BillLineItem(
                cpt_code="99396",
                description="Periodic physical examination, adults 40-64",
                icd10_codes=["Z00.00"],
                unit_price_eur=120.00,
                quantity=1,
            ),
            BillLineItem(
                cpt_code="85025",
                description="Complete blood count with differential",
                icd10_codes=["Z00.00"],
                unit_price_eur=25.00,
                quantity=1,
            ),
        ],
        insurance_company="Global Health Insurance",
        submitted_at="2026-05-24T09:21:07Z",
    )


def scenario_c_contract_violation() -> EDI837Packet:
    """Pre-authorization (EDI 278) - procedure NOT YET performed, clinic is asking
    insurance for approval BEFORE scheduling. Aegis intercepts and stops it before
    the MRI is performed - 320 EUR really saved."""
    return EDI837Packet(
        packet_id="AUTH-2026-05-24-00783",
        clinic_name="St. Sava Medical Center",
        clinic_id="RS-CLI-00214",
        patient=Patient(
            patient_id="PAT-21055",
            full_name="Stefan Jovanovic",
            date_of_birth="1990-11-04",
            insurance_id="GH-201-993-71",
        ),
        doctor_note=(
            "PRE-AUTHORIZATION REQUEST. "
            "Patient reports frequent headaches over the past month. "
            "Headaches are dull, localized in the frontal region, lasting 2-4 hours. "
            "Neurological examination shows no focal deficits. "
            "Given that the patient had a brain MRI 2 months ago with normal findings, "
            "but due to increased headache intensity, I propose scheduling "
            "a follow-up brain MRI for next week. "
            "Requesting coverage confirmation from insurance before scheduling the appointment."
        ),
        bill_items=[
            BillLineItem(
                cpt_code="70551",
                description="Brain MRI without contrast (PLANNED - not yet performed)",
                icd10_codes=["R51"],
                unit_price_eur=320.00,
                quantity=1,
            ),
        ],
        insurance_company="Global Health Insurance",
        submitted_at="2026-05-24T09:38:51Z",
    )


def scenario_d_missing_documents() -> EDI837Packet:
    return EDI837Packet(
        packet_id="EDI-2026-05-24-00784",
        clinic_name="St. Sava Medical Center",
        clinic_id="RS-CLI-00214",
        patient=Patient(
            patient_id="PAT-77420",
            full_name="Milan Radovanovic",
            date_of_birth="1972-01-18",
            insurance_id="GH-774-220-18",
        ),
        doctor_note=(
            "Patient is 3 weeks after arthroscopic repair of the right knee meniscus. "
            "Reports stiffness, limited flexion to 95 degrees, and pain during stairs. "
            "Orthopedic follow-up recommends supervised therapeutic exercise twice weekly "
            "for 3 weeks to restore range of motion and quadriceps strength. "
            "Billing six sessions of therapeutic exercise after the first completed week."
        ),
        bill_items=[
            BillLineItem(
                cpt_code="97110",
                description="Therapeutic exercises to develop strength and range of motion",
                icd10_codes=["S83.241D", "M25.561"],
                unit_price_eur=45.00,
                quantity=6,
            ),
        ],
        supporting_documents=[
            "orthopedic_followup_note.pdf",
            "invoice_line_items.csv",
        ],
        insurance_company="Global Health Insurance",
        submitted_at="2026-05-24T10:06:12Z",
    )


SCENARIOS = {
    "scenario_a": {
        "name": "Error: missing ICD-10 code",
        "subtitle": "Nurse forgot to link symptoms to the procedure",
        "loader": scenario_a_missing_icd10,
        "expected_outcome": "rejected_with_autofix",
    },
    "scenario_b": {
        "name": "Clean bill",
        "subtitle": "Routine check-up passing through the AI filter",
        "loader": scenario_b_clean_bill,
        "expected_outcome": "approved",
    },
    "scenario_c": {
        "name": "Pre-authorization stopped",
        "subtitle": "MRI scheduled, Aegis stops it BEFORE the procedure (contract violation)",
        "loader": scenario_c_contract_violation,
        "expected_outcome": "rejected_contract",
    },
    "scenario_d": {
        "name": "Missing documents",
        "subtitle": "Aegis predicts which attachments the insurer will require",
        "loader": scenario_d_missing_documents,
        "expected_outcome": "rejected_missing_documents",
    },
}


PATIENT_HISTORY = {
    "PAT-21055": {
        "previous_procedures": [
            {"cpt": "70551", "date": "2026-03-15", "result": "normal findings"}
        ]
    },
}


def get_patient_history(patient_id: str) -> dict:
    return PATIENT_HISTORY.get(patient_id, {"previous_procedures": []})
