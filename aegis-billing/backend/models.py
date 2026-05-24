"""
Pydantic models describing the data structures that move through the system.
EDI 837 is an international standard for healthcare claims; here we represent it
as simplified JSON to keep the demo clear.
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------- Clinic -> Clearinghouse ----------

class Patient(BaseModel):
    patient_id: str
    full_name: str
    date_of_birth: str
    insurance_id: str


class BillLineItem(BaseModel):
    """One bill line item entered by front-desk staff."""
    cpt_code: str = Field(..., description="Procedure CPT code, e.g. 76700 (abdominal ultrasound)")
    description: str
    icd10_codes: List[str] = Field(
        default_factory=list,
        description="ICD-10 diagnosis codes that justify this procedure. "
                    "This is the field where 85% of errors happen.",
    )
    unit_price_eur: float
    quantity: int = 1


class EDI837Packet(BaseModel):
    """Standardized digital packet the clinic sends through the clearinghouse."""
    packet_id: str
    clinic_name: str
    clinic_id: str
    patient: Patient
    doctor_note: str = Field(..., description="Free-text note written by the physician")
    bill_items: List[BillLineItem]
    supporting_documents: List[str] = Field(
        default_factory=list,
        description="Documents attached to the claim package before sending to insurance.",
    )
    insurance_company: str
    submitted_at: str  # ISO timestamp


# ---------- Agent output ----------

class ExtractedClinicalFinding(BaseModel):
    """What Agent 1 (Medical Coder) extracted from the physician's note."""
    finding: str
    suggested_icd10: str
    confidence: float
    evidence_quote: str


class ContractRule(BaseModel):
    """Rule Agent 2 (Contract Lawyer) found in the insurance contract."""
    rule_id: str
    procedure_cpt: str
    requires_icd10_categories: List[str]
    additional_constraint: Optional[str] = None
    source_quote: str


class AuditIssue(BaseModel):
    """Concrete error found by Agent 3 (Auditor)."""
    severity: Literal["error", "warning"]
    line_item_cpt: str
    issue_type: Literal[
        "missing_icd10_justification",
        "icd10_procedure_mismatch",
        "contract_limit_violation",
        "duplicate_billing",
        "missing_required_documentation",
    ]
    explanation: str
    suggested_fix: dict  # {"add_icd10": ["R10.9"]} or {"remove_cpt": "..."} etc.


class AegisDecision(BaseModel):
    """Final response the clearinghouse receives from the Aegis filter."""
    packet_id: str
    status: Literal["approved", "rejected"]
    processing_time_ms: int
    agent1_findings: List[ExtractedClinicalFinding]
    agent2_rules: List[ContractRule]
    agent3_issues: List[AuditIssue]
    estimated_saved_eur: float
    narrator_steps: List[str]  # Short step descriptions for the Loom overlay
