"""
AegisBilling.ai - FastAPI backend
==================================
Pokrece se:  uvicorn main:app --reload --port 8000

Endpointi:
  GET  /api/scenarios                            - lista pripremljenih scenarija
  GET  /api/scenarios/{scenario_id}              - vraca EDI 837 paket za scenario
  POST /api/clearinghouse/intercept              - sinhrono presretanje (sva 3 agenta)
  GET  /api/clearinghouse/intercept-stream/{id}  - SSE stream, salje korak po korak
  POST /api/clinic/apply-fix                     - primenjuje predlozeni fix i re-submituje
  GET  /api/stats                                - dashboard brojaci
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

load_dotenv()

app = FastAPI(
    title="AegisBilling.ai",
    description="AI filter za zdravstvene racune unutar clearinghouse-a (Gemini powered)",
    version="0.1.0",
)

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
# SCENARIJI (mockovani ulazni podaci)
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
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} ne postoji")
    return SCENARIOS[scenario_id]["loader"]()


# ============================================================================
# CORE: presretanje (sinhrono - sva 3 agenta, vrati konacnu odluku)
# ============================================================================

def _run_full_audit(packet: EDI837Packet) -> AegisDecision:
    """Pokrece sva 3 agenta serijski i sklapa konacnu odluku."""
    t0 = time.time()
    narrator_steps: list[str] = []

    narrator_steps.append("Agent 1 (Medical Coder) cita lekarski nalaz...")
    findings = medical_coder.run(packet.doctor_note)
    narrator_steps.append(
        f"Agent 1 nasao {len(findings)} klinickih nalaza iz teksta lekara."
    )

    contract_text = get_contract(packet.insurance_company)
    cpt_codes = [item.cpt_code for item in packet.bill_items]
    narrator_steps.append("Agent 2 (Contract Lawyer) pretrazuje ugovor osiguranja...")
    rules = contract_lawyer.run(contract_text, cpt_codes)
    narrator_steps.append(
        f"Agent 2 izvukao {len(rules)} relevantnih pravila iz ugovora."
    )

    history = get_patient_history(packet.patient.patient_id)
    narrator_steps.append("Agent 3 (Auditor) unakrsno proverava racun...")
    issues = auditor.run(findings, rules, packet.bill_items, history)

    has_errors = any(i.severity == "error" for i in issues)
    status = "rejected" if has_errors else "approved"

    if has_errors:
        narrator_steps.append(
            f"STOP! Aegis je presreo {len(issues)} gresaka pre slanja osiguranju."
        )
    else:
        narrator_steps.append("OK - racun je cist, prosledjen osiguranju.")

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
    """Sinhroni endpoint: vraca konacnu odluku kad svi agenti zavrse."""
    return _run_full_audit(packet)


# ============================================================================
# STREAMING: Server-Sent Events za realtime pipeline animaciju
# ============================================================================

def _sse_pack(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False, default=str)}\n\n"


async def _stream_audit(packet: EDI837Packet) -> AsyncIterator[str]:
    """Salje SSE evente kako se agenti pokrecu."""
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
    rules = await asyncio.to_thread(contract_lawyer.run, contract_text, cpt_codes)
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
        auditor.run, findings, rules, packet.bill_items, history
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
    """SSE endpoint koji frontend pretplati za realtime animaciju pipeline-a."""
    if scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail=f"Scenario {scenario_id} ne postoji")
    packet = SCENARIOS[scenario_id]["loader"]()
    return StreamingResponse(
        _stream_audit(packet),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ============================================================================
# FIX: primena predlozenog auto-fix-a i re-submission
# ============================================================================

class ApplyFixRequest(BaseModel):
    scenario_id: str
    fixes: list[dict]


@app.post("/api/clinic/apply-fix", response_model=AegisDecision)
def apply_fix(req: ApplyFixRequest):
    """Simulira 1-Click Auto-Dopuna sa sestrinog ekrana."""
    if req.scenario_id not in SCENARIOS:
        raise HTTPException(status_code=404, detail="Scenario ne postoji")

    packet = SCENARIOS[req.scenario_id]["loader"]()

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

    return _run_full_audit(packet)


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
