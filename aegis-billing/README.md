# AegisBilling.ai - Demo (pitch)

Live demo verzija AegisBilling.ai sistema — **AI filtera unutar klirinške kuće** koji
presreće zdravstvene račune pre nego što stignu osiguravajućoj kući, hvata greške i
sestri na šalteru nudi **"1-Click Auto-Dopunu"**.

Demo prikazuje sva tri stejkholdera **side-by-side**:

```
[Klinika] ──▶ [Clearinghouse + Aegis AI Filter (3 agenta)] ──▶ [Osiguravajuća kuća]
```

- **Backend**: Python 3.10+ / FastAPI / **Google Gemini API** (free tier, gemini-2.0-flash)
- **Frontend**: React 18 + Vite + Tailwind CSS + Framer Motion
- **Ulazni podaci**: mockovani (lekarski nalazi, EDI 837 paketi, ugovori osiguranja).
  AI agenti rade **pravu LLM analizu** preko Gemini API-ja nad tim podacima.

---

## Brzo pokretanje (5 minuta)

### 1. Dobijte besplatan Gemini API ključ

- Otvorite https://aistudio.google.com/apikey
- Kliknite **"Create API key"** → izaberete postojeći GCP projekat ili napravite novi
- Kopirajte ključ (počinje sa `AIza...`)
- **Besplatan tier:** 15 zahteva/min, 1M tokena/dan — više nego dovoljno za demo

### 2. Podesite backend

```bash
cd aegis-billing/backend
cp .env.example .env
```

Otvorite `.env` u editoru i upišite ključ:

```
GEMINI_API_KEY=AIza...vaš ključ ovde
```

Zatim instalirajte i pokrenite:

```bash
python -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Backend je sada na `http://localhost:8000`. Otvorite `http://localhost:8000/docs` da
vidite sve endpointe (Swagger UI). Otvorite `http://localhost:8000/` da proverite
da li je ključ pravilno učitan (`"has_api_key": true`).

### 3. Pokrenite frontend

U drugom terminalu:

```bash
cd aegis-billing/frontend
npm install
npm run dev
```

Otvorite `http://localhost:5173` — to je glavni demo ekran.

---

## Arhitektura

```
aegis-billing/
├── backend/
│   ├── main.py                    # FastAPI: endpointi + SSE streaming
│   ├── models.py                  # Pydantic modeli (EDI 837 paket, Decision...)
│   ├── mock_responses.py          # Fallback ako MOCK_MODE=true
│   ├── agents/
│   │   ├── llm_client.py          # Google Gen AI SDK wrapper (Gemini)
│   │   ├── medical_coder.py       # Agent 1 — čita lekarski nalaz
│   │   ├── contract_lawyer.py     # Agent 2 — Graph RAG nad ugovorom
│   │   └── auditor.py             # Agent 3 — unakrsna provera
│   └── mock_data/
│       ├── scenarios.py           # 3 pripremljena scenarija
│       └── insurance_contracts.py # Mockovani ugovor osiguranja
│
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js             # Proxy na backend (localhost:8000)
    ├── tailwind.config.js
    └── src/
        ├── App.jsx                # Glavni layout + orkestracija
        ├── lib/api.js             # API + SSE klijent
        └── components/
            ├── ClinicPanel.jsx        # Levi panel: nalaz + račun
            ├── ClearinghousePanel.jsx # Sredina: 3 agent kartice
            ├── InsurancePanel.jsx     # Desni: prijem / odbijenica
            ├── AgentCard.jsx          # Pojedinačni agent UI
            ├── PipelineAnimation.jsx  # Tačkica koja putuje
            ├── StatsDashboard.jsx     # 4 brojača na vrhu
            ├── NarratorOverlay.jsx    # Loom-friendly natpisi
            ├── AegisFixModal.jsx      # 1-Click Auto-Dopuna popup
            └── ScenarioSelector.jsx   # Top bar tab-ovi + RUN dugme
```

### Tok jednog scenarija

1. Korisnik bira scenario → frontend zove `GET /api/scenarios/{id}` → klinika panel
   prikazuje lekarski nalaz i račun.
2. Klik **POKRENI DEMO** → otvara se SSE konekcija
   `GET /api/clearinghouse/intercept-stream/{id}`.
3. Backend serijski poziva Agent 1 (Gemini) → emit `agent_result` → frontend prikazuje
   findings; isto za Agent 2 i Agent 3.
4. Backend emit `decision` → frontend prikazuje konačan ishod (approved / rejected) u
   `InsurancePanel`.
5. Ako rejected → otvara se `AegisFixModal` sa **1-Click Auto-Dopunom**.
6. Klik na auto-dopunu → `POST /api/clinic/apply-fix` → primenjuje ICD-10 šifre →
   ponovno pokreće sva 3 agenta → ovaj put approved.

---

## Tri scenarija (za pitch snimak)

### Scenario A: "Greška — nedostaje ICD-10" *(hero scenario)*

- **Pacijent**: Marko Petrović, bol u stomaku.
- **Lekarski nalaz**: opisuje "oštar probadajući bol ispod levog rebranog luka".
- **Račun**: ultrazvuk abdomena (CPT 76700), ali sestra je **zaboravila** da poveže
  ICD-10 šifru za bol.
- **Ishod**: Agent 1 izvuče R10.9 (abdominalni bol) iz teksta, Agent 3 hvata da na
  računu nedostaje ICD-10. Aegis modal nudi 1-click ispravku.

### Scenario B: "Čist račun"

- Rutinski sistematski pregled, sve šifre na mestu.
- **Ishod**: prolazi kroz pipeline za par sekundi — `approved`. Pokazuje da AI ne
  blokira nepotrebno.

### Scenario C: "Kršenje ugovora" *(Graph RAG hero)*

- Pacijent imao MRI mozga pre 2 meseca; ugovor ograničava MRI na 1× / 6 meseci.
- **Ishod**: Agent 2 (Contract Lawyer) hvata kršenje pravila iz ugovora, Agent 3
  blokira račun. Pokazuje moć Graph RAG-a.

---

## Skripta za Loom snimak (preporučeno trajanje: 2-3 minuta)

1. **(0:00)** Otvoriti demo na `localhost:5173`. Reci:
   *"Pred vama je AegisBilling.ai — AI sloj koji sedi unutar klirinške kuće. Levo
   imamo kliniku, u sredini naš filter sa tri agenta, desno osiguranje."*

2. **(0:20)** Klik **"Greška: nedostaje ICD-10 šifra"** → pokaži tekst lekara i
   račun. *"Pacijent ima bol u stomaku — lekar je to napisao. Ali sestra na šalteru
   je zaboravila da prebaci tu dijagnozu u ICD-10 polje na računu."*

3. **(0:40)** Klik **POKRENI DEMO**. Komentariši dok Gemini agenti rade. Loom
   narrator natpisi pri vrhu automatski prate korake.

4. **(1:10)** Kada iskoči crveni Aegis modal, pauziraj. *"Ovo je hero
   funkcionalnost — jedan klik. Sestra ne mora ništa ručno da kuca."*

5. **(1:25)** Klik **1-Click Auto-Dopuna**. Pokaži kako se ICD-10 šifra pojavljuje
   na računu i kako paket sada prolazi do osiguranja.

6. **(1:50)** Pređi na **Scenario B** (čist račun) → pokaži da AI ne blokira sve.

7. **(2:10)** Pređi na **Scenario C** (kršenje ugovora) → pokaži kako Agent 2 hvata
   pravilo iz ugovora koje je nemoguće ručno isprogramirati.

8. **(2:45)** Završi pokazujući stats dashboard. *"Pogledajte: presretnuto X
   računa, sačuvano Y EUR za klinike. Svaki taj račun je 0.05€ direktan prihod u
   našem džepu."*

---

## Šta menjati kad pređete na produkciju

| Komponenta | Sada (demo) | Produkcija |
| --- | --- | --- |
| Ulazni podaci | `mock_data/scenarios.py` | Pravi EDI 837 webhook iz clearinghouse-a |
| Ugovori osiguranja | `insurance_contracts.py` (text) | PDF-ovi u Vertex AI Search graf bazu |
| LLM provider | AI Studio (free tier) | Vertex AI na GCP-u (Gemini Pro/Flash) |
| Agent orchestration | Serijski u FastAPI | Cloud Run + Vertex AI Agents / ADK |
| Stats | In-memory dict | PostgreSQL + Redis |
| Auth | Nema | OAuth2 + IAM između clearinghouse i nas |
| Anonimizacija | Nema | PII redaktor pre slanja u LLM |

---

## API endpointi (za testiranje van UI-ja)

```bash
# Lista scenarija
curl http://localhost:8000/api/scenarios

# Vrati podatke o scenarijju (klinika)
curl http://localhost:8000/api/scenarios/scenario_a

# Sinhrono presretanje (čekaš dok svi agenti završe)
curl -X POST http://localhost:8000/api/clearinghouse/intercept \
  -H "Content-Type: application/json" \
  -d @scenario_a_packet.json

# SSE stream (real-time progress)
curl -N http://localhost:8000/api/clearinghouse/intercept-stream/scenario_a

# Primena fix-a
curl -X POST http://localhost:8000/api/clinic/apply-fix \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"scenario_a","fixes":[{"action":"add_icd10","codes":["R10.9"],"to_cpt":"76700"}]}'

# Stats
curl http://localhost:8000/api/stats
```

---

## Troubleshooting

**"GEMINI_API_KEY nije postavljen"**
Kreirajte `backend/.env` iz `backend/.env.example` i upišite ključ. Ključ dobijate
besplatno na https://aistudio.google.com/apikey

**Frontend ne vidi backend (CORS / Network error)**
Backend mora biti na `http://localhost:8000` i frontend na `http://localhost:5173`.
Vite proxy je već konfigurisan.

**Demo bez interneta / API ključa**
Postavite `MOCK_MODE=true` u `.env` — agenti će koristiti pripremljene odgovore iz
`mock_responses.py`. Vizuelno demo izgleda identično, samo bez LLM poziva.

**Agent vraća čudne / nekompletne odgovore**
Gemini 2.0 Flash je brz ali ponekad varira. Možete probati `gemini-1.5-pro` u
`.env`:
```
AEGIS_MODEL=gemini-1.5-pro
```
za stabilnije odgovore (ali sporije).

**Rate limit error (429)**
Free tier ima 15 zahteva/min. Sačekajte par sekundi i pokušajte ponovo.

---

## License

Demo verzija za pitch potrebe. © 2026 AegisBilling.ai
