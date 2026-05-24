"""
Pydantic modeli koji opisuju strukture podataka koji teku kroz sistem.
EDI 837 je internacionalni standard za zdravstvene zahteve - mi ga ovde
predstavljamo kao pojednostavljen JSON da bi demo bio jasan.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------- Klinika -> Clearinghouse ----------

class Patient(BaseModel):
    patient_id: str
    full_name: str
    date_of_birth: str
    insurance_id: str


class BillLineItem(BaseModel):
    """Jedna stavka racuna - sto je sestra unela na salteru."""
    cpt_code: str = Field(..., description="CPT kod procedure, npr. 76700 (Ultrazvuk abdomena)")
    description: str
    icd10_codes: List[str] = Field(
        default_factory=list,
        description="ICD-10 dijagnostiocke sifre koje opravdavaju ovu proceduru. "
                    "Ovo je polje gde nastaje 85% gresaka.",
    )
    unit_price_eur: float
    quantity: int = 1


class EDI837Packet(BaseModel):
    """Standardizovani digitalni paket koji klinika salje kroz clearinghouse."""
    packet_id: str
    clinic_name: str
    clinic_id: str
    patient: Patient
    doctor_note: str = Field(..., description="Slobodan tekst koji je lekar napisao u nalazu")
    bill_items: List[BillLineItem]
    insurance_company: str
    submitted_at: str  # ISO timestamp


# ---------- Output agenata ----------

class ExtractedClinicalFinding(BaseModel):
    """Sta je Agent 1 (Medical Coder) izvukao iz teksta lekara."""
    finding: str
    suggested_icd10: str
    confidence: float
    evidence_quote: str


class ContractRule(BaseModel):
    """Pravilo koje je Agent 2 (Contract Lawyer) pronasao u ugovoru osiguranja."""
    rule_id: str
    procedure_cpt: str
    requires_icd10_categories: List[str]
    additional_constraint: Optional[str] = None
    source_quote: str


class AuditIssue(BaseModel):
    """Konkretna greska koju je Agent 3 (Auditor) pronasao."""
    severity: Literal["error", "warning"]
    line_item_cpt: str
    issue_type: Literal[
        "missing_icd10_justification",
        "icd10_procedure_mismatch",
        "contract_limit_violation",
        "duplicate_billing",
    ]
    explanation: str
    suggested_fix: dict  # {"add_icd10": ["R10.9"]} ili {"remove_cpt": "..."} itd.


class AegisDecision(BaseModel):
    """Konacan odgovor koji clearinghouse dobija od Aegis filtera."""
    packet_id: str
    status: Literal["approved", "rejected"]
    processing_time_ms: int
    agent1_findings: List[ExtractedClinicalFinding]
    agent2_rules: List[ContractRule]
    agent3_issues: List[AuditIssue]
    estimated_saved_eur: float
    narrator_steps: List[str]  # Za Loom overlay - kratki opisi koraka
