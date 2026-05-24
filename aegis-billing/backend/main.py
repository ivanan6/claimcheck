"""
AegisBilling.ai - FastAPI backend
==================================
Run with:  uvicorn main:app --reload --port 8000

Endpoints:
  GET  /api/scenarios                            - list prepared scenarios
  GET  /api/scenarios/{scenario_id}              - return EDI 837 packet for a scenario
  POST /api/clearinghouse/intercept              - synchronous interception (all 3 agents)
  GET  /api/clearinghouse/intercept-stream/{id}  - SSE stream, sends progress step by step
  POST /api/clinic/apply-fix                     - apply suggested fix and resubmit
  GET  /api/stats                                - dashboard counters
"""
import asyncio
import json
import os
import time
from typing import AsyncIterator

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from agents import auditor, contract_lawyer, medical_coder
from agents.llm_client import is_mock_mode
from mock_data.insurance_contracts import get_contract
from mock_data.scenarios import SCENARIOS, get_patient_history
from models import AegisDecision, EDI837Packet
from rag.retriever import build_policy_context, retrieve_policy_chunks
from rag.synthea_loader import sample_patients, synthea_summary

load_dotenv()

app = FastAPI(
    title="AegisBilling.ai",
    description="AI filter for healthcare claims inside a clearinghouse (Gemini powered)",
    version="0.1.0",
)

# In-memory override: when front-desk staff apply a fix in the Clinic panel, the
# corrected packet is stored here so the next Run uses it instead of resetting
# the scenario. It is cleared when the user selects the scenario again.
_FIXED_PACKETS: dict[str, EDI837Packet] = {}

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"),
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH
# ============================================================================

@app.get("/")
def root():
    return {
        "service": "AegisBilling.ai",
        "status": "online",
        "llm_provider": "google-gemini",
        "model": os.getenv("AEGIS_MODEL", "gemini-2.0-flash"),
        "has_api_key": bool(os.getenv("GEMINI_API_KEY")),
        "mock_mode": is_mock_mode(),
    }


# ============================================================================
# SCENARIOS (mock input data)
# ============================================================================

@app.get("/api/scenarios")
def list_scenarios():
    return [
        {
            "id": sid,
            "name": meta["name"],
            "subtitle": meta["subtitle"],
            "expected_outcome": meta["expected_outcome"],
        }
        for sid, meta in SCENARIOS.items()
    ]


@app.get("/api/scenarios/{scenario_id}")
def get_scenario(scenario_id: str) -> EDI837Packet:
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} does not exist")
    if scenario_id in _FIXED_PACKETS:
        return _FIXED_PACKETS[scenario_id]
    return SCENARIOS[scenario_id]["loader"]()


@app.post("/api/scenarios/{scenario_id}/reset")
def reset_scenario(scenario_id: str):
    """Clear the previously applied fix and restore the scenario to its initial state."""
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} does not exist")
    _FIXED_PACKETS.pop(scenario_id, None)
    return {"ok": True, "scenario_id": scenario_id}


# ============================================================================
# CORE: interception (synchronous - all 3 agents, returns final decision)
# ============================================================================

def _run_full_audit(packet: EDI837Packet) -> AegisDecision:
    """Run all 3 agents sequentially and assemble the final decision."""
    t0 = time.time()
    narrator_steps: list[str] = []

    narrator_steps.append("Agent 1 (Medical Coder) reads the physician note...")
    findings = medical_coder.run(packet.doctor_note)
    narrator_steps.append(
        f"Agent 1 found {len(findings)} clinical findings in the physician note."
    )

    contract_text = get_contract(packet.insurance_company)
    cpt_codes = [item.cpt_code for item in packet.bill_items]
    diagnosis_codes = [code for item in packet.bill_items for code in item.icd10_codes]
    narrator_steps.append("Agent 2 (Contract Lawyer) searches the insurance contract...")
    rules = contract_lawyer.run(
        contract_text,
        cpt_codes,
        payer=packet.insurance_company,
        diagnosis_codes=diagnosis_codes,
        supporting_documents=packet.supporting_documents,
        doctor_note=packet.doctor_note,
    )
    narrator_steps.append(
        f"Agent 2 extracted {len(rules)} relevant rules from the contract."
    )

    history = get_patient_history(packet.patient.patient_id)
    narrator_steps.append("Agent 3 (Auditor) cross-checks the bill...")
    issues = auditor.run(
        findings,
        rules,
        packet.bill_items,
        history,
        packet.supporting_documents,
    )

    has_errors = any(i.severity == "error" for i in issues)
    status = "rejected" if has_errors else "approved"

    if has_errors:
        narrator_steps.append(
            f"STOP! Aegis intercepted {len(issues)} errors before sending to insurance."
        )
    else:
        narrator_steps.append("OK - the bill is clean and forwarded to insurance.")

    total_bill = sum(item.unit_price_eur * item.quantity for item in packet.bill_items)
    saved = total_bill if has_errors else 0.0

    elapsed_ms = int((time.time() - t0) * 1000)

    return AegisDecision(
        packet_id=packet.packet_id,
        status=status,
        processing_time_ms=elapsed_ms,
        agent1_findings=findings,
        agent2_rules=rules,
        agent3_issues=issues,
        estimated_saved_eur=round(saved, 2),
        narrator_steps=narrator_steps,
    )


@app.post("/api/clearinghouse/intercept", response_model=AegisDecision)
def intercept(packet: EDI837Packet):
    """Synchronous endpoint: returns the final decision after all agents finish."""
    return _run_full_audit(packet)


# ============================================================================
# STREAMING: Server-Sent Events for the real-time pipeline animation
# ============================================================================

def _sse_pack(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


async def _stream_audit(packet: EDI837Packet) -> AsyncIterator[str]:
    """Send SSE events as agents run."""
    t0 = time.time()

    yield _sse_pack("stage", {"stage": "clearinghouse_received", "packet_id": packet.packet_id})
    await asyncio.sleep(0.4)

    yield _sse_pack("stage", {"stage": "agent1_started", "agent": "medical_coder"})
    findings = await asyncio.to_thread(medical_coder.run, packet.doctor_note)
    yield _sse_pack(
        "agent_result",
        {
            "agent": "medical_coder",
            "agent_number": 1,
            "findings": [f.model_dump() for f in findings],
        },
    )
    yield _sse_pack("stage", {"stage": "agent1_done"})
    await asyncio.sleep(0.3)

    yield _sse_pack("stage", {"stage": "agent2_started", "agent": "contract_lawyer"})
    contract_text = get_contract(packet.insurance_company)
    cpt_codes = [item.cpt_code for item in packet.bill_items]
    diagnosis_codes = [code for item in packet.bill_items for code in item.icd10_codes]
    rules = await asyncio.to_thread(
        contract_lawyer.run,
        contract_text,
        cpt_codes,
        payer=packet.insurance_company,
        diagnosis_codes=diagnosis_codes,
        supporting_documents=packet.supporting_documents,
        doctor_note=packet.doctor_note,
    )
    yield _sse_pack(
        "agent_result",
        {
            "agent": "contract_lawyer",
            "agent_number": 2,
            "rules": [r.model_dump() for r in rules],
        },
    )
    yield _sse_pack("stage", {"stage": "agent2_done"})
    await asyncio.sleep(0.3)

    yield _sse_pack("stage", {"stage": "agent3_started", "agent": "auditor"})
    history = get_patient_history(packet.patient.patient_id)
    issues = await asyncio.to_thread(
        auditor.run,
        findings,
        rules,
        packet.bill_items,
        history,
        packet.supporting_documents,
    )
    yield _sse_pack(
        "agent_result",
        {
            "agent": "auditor",
            "agent_number": 3,
            "issues": [i.model_dump() for i in issues],
        },
    )
    yield _sse_pack("stage", {"stage": "agent3_done"})
    await asyncio.sleep(0.3)

    has_errors = any(i.severity == "error" for i in issues)
    status = "rejected" if has_errors else "approved"
    total_bill = sum(item.unit_price_eur * item.quantity for item in packet.bill_items)
    saved = total_bill if has_errors else 0.0
    elapsed_ms = int((time.time() - t0) * 1000)

    decision = AegisDecision(
        packet_id=packet.packet_id,
        status=status,
        processing_time_ms=elapsed_ms,
        agent1_findings=findings,
        agent2_rules=rules,
        agent3_issues=issues,
        estimated_saved_eur=round(saved, 2),
        narrator_steps=[],
    )

    final_stage = "blocked_by_aegis" if has_errors else "delivered_to_insurance"
    yield _sse_pack("stage", {"stage": final_stage})
    yield _sse_pack("decision", decision.model_dump())
    yield _sse_pack("done", {"elapsed_ms": elapsed_ms})


@app.get("/api/clearinghouse/intercept-stream/{scenario_id}")
async def intercept_stream(scenario_id: str):
    """SSE endpoint the frontend subscribes to for the real-time pipeline animation."""
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} does not exist")
    packet = _FIXED_PACKETS.get(scenario_id) or SCENARIOS[scenario_id]["loader"]()
    return StreamingResponse(
        _stream_audit(packet),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ============================================================================
# FIX: applying the suggested auto-fix and resubmission
# ============================================================================

class ApplyFixRequest(BaseModel):
    scenario_id: str
    fixes: list[dict]


class RagSearchRequest(BaseModel):
    payer: str = "Synthetic Payer Alpha"
    procedure_codes: list[str]
    diagnosis_codes: list[str] = []
    supporting_documents: list[str] = []
    doctor_note: str = ""
    top_k: int = 5


@app.post("/api/clinic/apply-fix", response_model=EDI837Packet)
def apply_fix(req: ApplyFixRequest):
    """
    Apply the fix in the clinic system (add ICD-10, remove line item, etc.) and
    store the corrected packet in _FIXED_PACKETS. Returns the corrected packet
    without rerunning the auditor. The next stream/intercept call will use the
    corrected packet.
    """
    if req.scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario does not exist")

    packet = _FIXED_PACKETS.get(req.scenario_id) or SCENARIOS[req.scenario_id]["loader"]()

    for fix in req.fixes:
        action = fix.get("action")
        if action == "add_icd10":
            target_cpt = fix.get("to_cpt") or fix.get("cpt")
            codes = fix.get("codes", [])
            for item in packet.bill_items:
                if item.cpt_code == target_cpt:
                    for c in codes:
                        if c not in item.icd10_codes:
                            item.icd10_codes.append(c)
        elif action == "remove_line":
            cpt = fix.get("cpt")
            packet.bill_items = [b for b in packet.bill_items if b.cpt_code != cpt]
        elif action == "attach_documents":
            for doc in fix.get("documents", []):
                if doc not in packet.supporting_documents:
                    packet.supporting_documents.append(doc)

    _FIXED_PACKETS[req.scenario_id] = packet
    return packet


@app.post("/api/rag/search")
def rag_search(req: RagSearchRequest):
    """Return the policy chunks the local RAG retriever would send to Agent 2."""
    results = retrieve_policy_chunks(
        payer=req.payer,
        procedure_codes=req.procedure_codes,
        diagnosis_codes=req.diagnosis_codes,
        supporting_documents=req.supporting_documents,
        doctor_note=req.doctor_note,
        top_k=req.top_k,
    )
    return {
        "count": len(results),
        "context": build_policy_context(results),
        "chunks": [
            {
                "chunk_id": result.chunk.chunk_id,
                "source": result.chunk.source,
                "payer": result.chunk.payer,
                "score": round(result.score, 3),
                "matched_terms": list(result.matched_terms),
                "text": result.chunk.text,
            }
            for result in results
        ],
    }


@app.get("/api/synthea/summary")
def get_synthea_summary():
    """Return a small summary proving the local Synthea CSV sample is available."""
    return {
        **synthea_summary(),
        "sample_patients": sample_patients(limit=5),
    }


# ============================================================================
# STATS
# ============================================================================

_stats = {
    "total_intercepted": 0,
    "errors_blocked": 0,
    "saved_eur": 0.0,
    "avg_processing_ms": 0,
    "last_decisions": [],
}


@app.get("/api/stats")
def get_stats():
    return _stats


@app.post("/api/stats/record")
def record_decision(decision: AegisDecision):
    _stats["total_intercepted"] += 1
    if decision.status == "rejected":
        _stats["errors_blocked"] += 1
    _stats["saved_eur"] = round(_stats["saved_eur"] + decision.estimated_saved_eur, 2)

    n = _stats["total_intercepted"]
    prev_avg = _stats["avg_processing_ms"]
    _stats["avg_processing_ms"] = int(
        ((prev_avg * (n - 1)) + decision.processing_time_ms) / n
    )

    _stats["last_decisions"].insert(
        0,
        {
            "packet_id": decision.packet_id,
            "status": decision.status,
            "saved_eur": decision.estimated_saved_eur,
            "processing_ms": decision.processing_time_ms,
        },
    )
    _stats["last_decisions"] = _stats["last_decisions"][:10]
    return _stats
