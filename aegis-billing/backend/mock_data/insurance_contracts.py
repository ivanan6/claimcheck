"""
Mock insurance company contracts.
In production, these PDFs are loaded into Graph RAG (Vertex AI Search / Neptune).
For the demo, we represent them as text passed to Agent 2 (Contract Lawyer).
"""

GLOBAL_HEALTH_CONTRACT = """
GLOBAL HEALTH INSURANCE - HEALTH COVERAGE CONTRACT
Version 2026.1 | Effective from: 2026-01-01

ARTICLE 4.2 - DIAGNOSTIC PROCEDURES
4.2.1 Ultrasound procedures (CPT 76700-76770):
  - Covered with a documented clinical indication
  - At least ONE ICD-10 code is required to justify the indication
  - Accepted categories: R10.x (abdominal pain), R19.x (digestive symptoms),
    K00-K93 (digestive system diseases), N00-N99 (genitourinary system diseases)

4.2.2 MRI procedures (CPT 70551-70553 - brain MRI):
  - Limit: maximum ONE brain MRI within 6 months per patient
  - EXCEPTION: does not apply if there is an ICD-10 code from category I60-I69
    (cerebrovascular diseases, including cerebral infarction)
  - A diagnosis from categories G00-G99 (nervous system diseases), R51 (headache),
    or S06.x (intracranial injury) is required

4.2.3 Routine annual physical examination (CPT 99396, 99397):
  - Covered once per year for adult patients
  - Does not require specific ICD-10 diagnosis codes
  - Z00.00 is accepted (general medical examination without complaints)

ARTICLE 5.1 - LABORATORY TESTS
5.1.1 Complete blood count (CPT 85025):
  - Covered with a routine examination or a specific clinical reason
  - If anemia, infection, or malignant processes are suspected, D50-D89 or B95-B97 are required

ARTICLE 6.3 - REHABILITATION AND PHYSICAL THERAPY
6.3.1 Therapeutic exercise (CPT 97110):
  - Covered after orthopedic injury or surgery when ICD-10 diagnosis supports the indication
  - Every claim package must include the physician referral AND the initial physical therapy
    evaluation with treatment plan
  - If billing more than 4 sessions, a progress report must also be attached
  - Claims missing required documentation are denied even when diagnosis and CPT codes match

ARTICLE 7 - GENERIC CONDITIONS
7.1 All diagnostic procedures must be supported by at least one diagnostic ICD-10
    code medically related to the procedure.
7.2 Procedures without a clinical indication are automatically denied.
"""

INSURANCE_CONTRACTS = {
    "Global Health Insurance": GLOBAL_HEALTH_CONTRACT,
}


def get_contract(insurance_company: str) -> str:
    return INSURANCE_CONTRACTS.get(
        insurance_company,
        "Generic contract: all procedures must have ICD-10 justification."
    )
