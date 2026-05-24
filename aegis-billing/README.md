# RedShield

Live demo version of the AegisBilling.ai system: an **AI filter inside a
clearinghouse** that intercepts healthcare claims before they reach the insurer,
catches errors, and offers front-desk staff a **"1-Click Auto-Fill"** fix.

The demo shows all three stakeholders **side by side**:

```text
[Clinic] --> [Clearinghouse + Aegis AI Filter (3 agents)] --> [Insurance Company]
```

- **Backend**: Python 3.10+ / FastAPI / **Google Gemini API** (free tier, gemini-2.0-flash)
- **Frontend**: React 18 + Vite + Tailwind CSS + Framer Motion
- **Input data**: mocked physician notes, EDI 837 packets, and insurance contracts.
  AI agents perform **real LLM analysis** through the Gemini API over that data.

---

## Quick Start (5 minutes)

### 1. Get a free Gemini API key

- Open https://aistudio.google.com/apikey
- Click **"Create API key"** and choose an existing GCP project or create a new one
- Copy the key (it starts with `AIza...`)
- **Free tier:** 15 requests/min, 1M tokens/day, more than enough for the demo

### 2. Configure the backend

```bash
cd aegis-billing/backend
cp .env.example .env
```

Open `.env` in your editor and add the key:

```env
GEMINI_API_KEY=AIza...your_key_here
```

Then install and run:

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The backend is now at `http://localhost:8000`. Open `http://localhost:8000/docs`
to see all endpoints (Swagger UI). Open `http://localhost:8000/` to verify that
the key is loaded correctly (`"has_api_key": true`).

### 3. Run the frontend

In another terminal:

```bash
cd aegis-billing/frontend
npm install
npm run dev
```

Open `http://localhost:5173`; this is the main demo screen.

---

## Architecture

```text
aegis-billing/
├── backend/
│   ├── main.py                    # FastAPI: endpoints + SSE streaming
│   ├── models.py                  # Pydantic models (EDI 837 packet, Decision...)
│   ├── mock_responses.py          # Fallback when MOCK_MODE=true
│   ├── agents/
│   │   ├── llm_client.py          # Google Gen AI SDK wrapper (Gemini)
│   │   ├── medical_coder.py       # Agent 1 - reads physician notes
│   │   ├── contract_lawyer.py     # Agent 2 - RAG over payer policies
│   │   └── auditor.py             # Agent 3 - cross-checking
│   ├── rag/
│   │   ├── retriever.py           # Local policy chunk retrieval
│   │   ├── inspect.py             # CLI retrieval debugger
│   │   └── synthea_loader.py      # Lightweight Synthea CSV reader
│   └── mock_data/
│       ├── scenarios.py           # 4 prepared scenarios
│       └── insurance_contracts.py # Mock insurance contract
│
├── data/
│   ├── policies/                  # Synthetic payer policy docs for RAG
│   ├── claims/                    # Synthetic claim packages
│   ├── clinical_notes/            # Synthetic physician notes
│   ├── supporting_docs/           # Synthetic attachments
│   └── synthea_csv/               # Local Synthea CSV sample (ignored by git)
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js             # Proxy to backend (localhost:8000)
    ├── tailwind.config.js
    └── src/
        ├── App.jsx                # Main layout + orchestration
        ├── lib/api.js             # API + SSE client
        └── components/
            ├── ClinicPanel.jsx        # Left panel: note + bill
            ├── ClearinghousePanel.jsx # Middle: 3 agent cards
            ├── InsurancePanel.jsx     # Right: receipt / denial
            ├── AgentCard.jsx          # Individual agent UI
            ├── PipelineAnimation.jsx  # Traveling packet dot
            ├── StatsDashboard.jsx     # 4 counters at the top
            ├── NarratorOverlay.jsx    # Loom-friendly captions
            ├── AegisFixModal.jsx      # 1-Click Auto-Fill popup
            └── ScenarioSelector.jsx   # Top bar tabs + Run button
```

### Scenario Flow

1. User selects a scenario -> frontend calls `GET /api/scenarios/{id}` -> the
   clinic panel displays the physician note and bill.
2. Click **Run demo** -> an SSE connection opens:
   `GET /api/clearinghouse/intercept-stream/{id}`.
3. Backend calls Agent 1 (Gemini) -> emits `agent_result` -> frontend displays
   findings; the same happens for Agent 2 and Agent 3.
4. Agent 2 retrieves relevant chunks from `data/policies/*.txt`, sends only
   those excerpts to the LLM, and extracts payer rules.
5. Backend emits `decision` -> frontend displays the final outcome
   (`approved` / `rejected`) in `InsurancePanel`.
6. If rejected -> `AegisFixModal` opens with **1-Click Auto-Fill**.
7. Click auto-fill -> `POST /api/clinic/apply-fix` -> applies ICD-10 codes ->
   reruns all 3 agents -> this time the claim is approved.

### Local RAG

The demo now has a local file-based RAG layer:

- `data/policies/*.txt` are treated as the payer knowledge base.
- `backend/rag/retriever.py` chunks those policies by section.
- The retriever scores chunks using payer, procedure codes, diagnosis codes,
  attached documents, and physician note text.
- `contract_lawyer.py` sends only the top retrieved chunks to the LLM.

Inspect retrieval manually:

```bash
cd aegis-billing
PYTHONPATH=backend backend/.venv/bin/python -m rag.inspect \
  --payer "Synthetic Payer Alpha" \
  --procedure PROC-PT-THEREX \
  --top-k 3
```

Check that the Synthea CSV sample is visible:

```bash
curl http://localhost:8000/api/synthea/summary
```

Search retrieved policy chunks through the API:

```bash
curl -X POST http://localhost:8000/api/rag/search \
  -H "Content-Type: application/json" \
  -d '{"payer":"Synthetic Payer Alpha","procedure_codes":["PROC-PT-THEREX"],"top_k":3}'
```

---

## Four Scenarios (for pitch recording)

### Scenario A: "Error: missing ICD-10 code" *(hero scenario)*

- **Patient**: Marko Petrovic, abdominal pain.
- **Physician note**: describes "sharp stabbing pain below the left costal arch".
- **Bill**: abdominal ultrasound (CPT 76700), but the nurse **forgot** to link
  the ICD-10 code for pain.
- **Outcome**: Agent 1 extracts R10.9 (abdominal pain) from the text, Agent 3
  catches that the bill is missing ICD-10. The Aegis modal offers a 1-click fix.

### Scenario B: "Clean bill"

- Routine annual physical examination, all codes in place.
- **Outcome**: passes through the pipeline in a few seconds as `approved`.
  Shows that the AI does not block unnecessarily.

### Scenario C: "Contract violation" *(Graph RAG hero)*

- Patient had a brain MRI 2 months ago; the contract limits MRI to 1x / 6 months.
- **Outcome**: Agent 2 (Contract Lawyer) catches the contract rule violation,
  Agent 3 blocks the request. Demonstrates the power of Graph RAG.

### Scenario D: "Missing documents"

- Physical therapy bill has matching CPT and ICD-10 codes.
- The policy requires a physician referral, initial PT evaluation with treatment
  plan, and a progress report when billing more than 4 sessions.
- The clinic attached only a follow-up note and invoice lines.
- **Outcome**: Aegis predicts the insurer would deny the package as incomplete
  and tells the clinic exactly which documents to attach before submission.

---

## Loom Recording Script (recommended length: 2-3 minutes)

1. **(0:00)** Open the demo at `localhost:5173`. Say:
   *"This is AegisBilling.ai, an AI layer sitting inside the clearinghouse. On
   the left we have the clinic, in the middle our three-agent filter, and on the
   right the insurer."*

2. **(0:20)** Click **"Error: missing ICD-10 code"** -> show the physician text
   and bill. *"The patient has abdominal pain; the doctor wrote that down. But
   the front desk forgot to copy that diagnosis into the ICD-10 field on the bill."*

3. **(0:40)** Click **Run demo**. Comment while the Gemini agents work. Loom
   narrator captions at the top automatically follow the steps.

4. **(1:10)** When the red Aegis modal appears, pause. *"This is the hero
   functionality: one click. Front-desk staff do not have to type anything manually."*

5. **(1:25)** Click **1-Click Auto-Fill**. Show how the ICD-10 code appears on
   the bill and how the packet now passes to insurance.

6. **(1:50)** Switch to **Scenario B** (clean bill) -> show that AI does not
   block everything.

7. **(2:10)** Switch to **Scenario C** (contract violation) -> show how Agent 2
   catches a contract rule that would be impossible to hard-code manually.

8. **(2:35)** Switch to **Scenario D** (missing documents) -> show that the bill
   is medically valid, but the policy requires extra attachments before it can
   pass insurance.

9. **(2:55)** Finish by showing the stats dashboard. *"Look: X bills intercepted,
   Y EUR saved for clinics. Every bill is 0.05 EUR of direct revenue for us."*

---

## What To Change For Production

| Component | Now (demo) | Production |
| --- | --- | --- |
| Input data | `mock_data/scenarios.py` | Real EDI 837 webhook from the clearinghouse |
| Insurance contracts | `insurance_contracts.py` (text) | PDFs in Vertex AI Search graph database |
| LLM provider | AI Studio (free tier) | Vertex AI on GCP (Gemini Pro/Flash) |
| Agent orchestration | Sequential in FastAPI | Cloud Run + Vertex AI Agents / ADK |
| Stats | In-memory dict | PostgreSQL + Redis |
| Auth | None | OAuth2 + IAM between the clearinghouse and us |
| Anonymization | None | PII redactor before sending to LLM |

---

## API Endpoints (for testing outside the UI)

```bash
# Scenario list
curl http://localhost:8000/api/scenarios

# Return scenario data (clinic)
curl http://localhost:8000/api/scenarios/scenario_a

# Synchronous interception (waits until all agents finish)
curl -X POST http://localhost:8000/api/clearinghouse/intercept \
  -H "Content-Type: application/json" \
  -d @scenario_a_packet.json

# SSE stream (real-time progress)
curl -N http://localhost:8000/api/clearinghouse/intercept-stream/scenario_a

# Apply fix
curl -X POST http://localhost:8000/api/clinic/apply-fix \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"scenario_a","fixes":[{"action":"add_icd10","codes":["R10.9"],"to_cpt":"76700"}]}'

# Stats
curl http://localhost:8000/api/stats
```

---

## Troubleshooting

**"GEMINI_API_KEY is not set"**
Create `backend/.env` from `backend/.env.example` and add the key. You can get
the key for free at https://aistudio.google.com/apikey

**Frontend cannot see backend (CORS / Network error)**
Backend must run at `http://localhost:8000` and frontend at
`http://localhost:5173`. The Vite proxy is already configured.

**Demo without internet / API key**
Set `MOCK_MODE=true` in `.env`; agents will use prepared responses from
`mock_responses.py`. Visually, the demo looks identical, just without LLM calls.

**Agent returns odd / incomplete responses**
Gemini 2.0 Flash is fast but can vary. You can try `gemini-1.5-pro` in `.env`:

```env
AEGIS_MODEL=gemini-1.5-pro
```

for more stable responses (but slower).

**Rate limit error (429)**
The free tier has 15 requests/min. Wait a few seconds and try again.

---

## License

Demo version for pitch purposes. (c) 2026 AegisBilling.ai
