# VaaniSeva — voice access to essential public information

> **Named beneficiary:** A rural farmer in Madhya Pradesh with a ₹500 keypad phone,
> no smartphone, and no mobile internet — asking "what is today's potato price at Bhind
> mandi?" or "am I eligible for PM-Kisan?" and receiving a verified, grounded answer in
> spoken Hindi, in under two seconds, without touching a screen.

VaaniSeva is a low-latency, multilingual voice agent that works through an ordinary
telephone call or a web browser microphone. It helps callers navigate government
welfare schemes, live crop market prices, and safe health information — entirely by
voice, with no app, no data plan, and no literacy barrier required.

---

## The problem it solves

Over 500 million Indians are effectively excluded from digital services — not because
information does not exist, but because that information lives behind screens, apps,
and data plans they do not have. A farmer eligible for ₹6,000/year under PM-Kisan
may never claim it because the official portal requires a smartphone. A rural patient
needing mental-health support may not know the verified helpline number. A daily-wage
worker may not know their MGNREGA rights.

VaaniSeva's answer: make the country's verified public information reachable from any
phone, in any supported language, right now.

---

## Architecture

```
Caller (any phone or browser mic)
  │
  ├─ Twilio Programmable Voice  ──────►  /twiml  →  <Connect><Stream>  (mu-law 8 kHz)
  └─ Browser raw PCM mic  ─────────────►  /local/ws  (16 kHz PCM)
                                               │
                                    ┌──────────▼──────────────┐
                                    │    Pipecat pipeline      │
                                    │  Silero VAD              │
                                    │  ↓                       │
                                    │  Sarvam Bulbul v2 STT    │
                                    │  (REST, 16 kHz)          │
                                    │  ↓                       │
                                    │  Intent + persona router │
                                    │  (Arya / Hitesh / Vidya) │
                                    │  ↓                       │
                                    │  Amazon Bedrock Nova     │
                                    │  (Converse + streaming)  │
                                    │  ↓                       │
                                    │  In-process MCP server   │──► Grounded data sources
                                    │  ↓                       │
                                    │  Safety / evidence layer │
                                    │  ↓                       │
                                    │  Cartesia Sonic 3 TTS    │
                                    │  (Arya) / Sarvam TTS     │
                                    │  (Hitesh, Vidya)         │
                                    └──────────────────────────┘
                                               │
                                    Barge-in: Twilio `clear` or
                                    browser stop cancels in-flight
                                    TTS and Bedrock generation
```

**End-user → Agent → MCP Server → Grounded Data** — the full agentic pattern:

| Layer | What it does |
|---|---|
| **Caller** | Any phone or browser mic; no app or data required |
| **Transport** | Twilio bidirectional Media Streams (telephone) or raw PCM WebSocket (browser) |
| **Orchestration** | Pipecat streaming pipeline — VAD, STT, LLM, TTS, barge-in as first-class primitives |
| **Agent (LLM)** | Amazon Bedrock Nova — reasoning, persona identity, tool selection |
| **MCP Server** | In-process tool server; exposes only narrow, validated tools; never raw DB access |
| **Grounded data** | DynamoDB RAG corpus (Titan Embeddings v2), data.gov.in mandi API, curated scheme snapshot, verified helplines |
| **Memory** | Salted one-way phone identifier → bounded caller summary (one paragraph max) |

---

## Three specialist personas

Routing is deterministic at the application boundary — topic drives persona, not the caller's phrasing:

| Persona | Voice | Domain |
|---|---|---|
| **Arya** | Cartesia Sonic 3 (Arushi) — warm, feminine | Government schemes, civic navigation, eligibility guidance |
| **Hitesh** | Sarvam Bulbul v2 (Abhilash) — masculine | Agriculture advisory, live mandi price observations |
| **Vidya** | Sarvam Bulbul v2 (Vidya) — feminine | Health navigation, verified helplines, safe escalation |

Persona transfer is atomic: application state, Bedrock system instruction, and TTS voice switch together. The LLM cannot drift identity through conversation history.

---

## Context engineering techniques used

- **Retrieval-Augmented Generation (RAG):** Amazon Titan Text Embeddings v2 generates vectors for scheme documents; cosine search over DynamoDB `vaaniseva-vectors` returns the top relevant chunks. Vectors are cached for 10 minutes to reduce cost and latency. If the AWS read is unavailable, the tool returns the curated official-source snapshot instead — it never silently invents a match.
- **Tool-grounded reasoning:** The LLM may not state a fact for schemes, prices, helplines, or eligibility without a tool result. It is explicitly prohibited from inventing a price or a government benefit figure.
- **Structured memory:** Returning callers with consent receive a one-paragraph continuity summary (preferred name, language, persona, broad help need). The model sees this text; it never touches the database.
- **Localization-aware context:** System instructions are written in the target language; personas use gender-correct Hindi first-person forms; Sarvam STT is tuned for code-switched Indian speech.
- **Guardrails before output:** A safety layer intercepts health output before it reaches TTS — no diagnosis, no dosage, always escalate emergencies to a verified helpline. Scheme results are labelled guidance, never approval decisions.
- **Multi-step agentic planning:** Intent routing → domain tool → evidence validation → safety policy → persona-voiced response. Each stage is logged and traceable.

---

## MCP tools (extensible)

The in-process MCP server is the **only** path to external facts. Adding a new knowledge domain means adding one tool with a source label, a safety scope, and a freshness date — no LLM prompt changes required.

Current tools:

| Tool | Data source | Fail-closed? |
|---|---|---|
| `search_government_schemes` | DynamoDB RAG + curated snapshot | ✅ Falls back, never invents |
| `check_scheme_eligibility` | Same corpus | ✅ Returns "check with official source" |
| `get_mandi_price` | data.gov.in OGD API (live) | ✅ Reports unavailability, no invented price |
| `get_health_helpline` | Curated verified numbers | ✅ Static, deterministic |
| `get_health_guidance` | Curated safe-scope text | ✅ Escalates emergencies |
| `switch_persona` | Internal state | — |
| `end_call` | Twilio API | — |

---

## Datasets cited

| Dataset | Usage |
|---|---|
| **data.gov.in — Agmarknet** | Live mandi price observations for 3,000+ mandis |
| **Amazon Titan Text Embeddings v2** | Scheme document vectors in DynamoDB |
| **Curated central scheme corpus** (8 schemes, built for this project) | PM-Kisan, Ayushman Bharat, MGNREGA, PM Awas, Sukanya Samriddhi, PM Ujjwala, Jan Dhan, Mudra — each with Hindi/English aliases, eligibility rules, official source, verification date |
| **iCall / Vandrevala / NIMHANS helpline registry** | Verified mental-health helplines |
| **Kisan Call Centre (1551)** | Agriculture helpline routing |

No user speech is stored. Memory summaries are bounded, user-deletable on request, and never contain identity documents, precise addresses, or financial credentials.

---

## Latency (measured, not claimed)

| Stage | Observed (local, provider-backed) |
|---|---|
| First greeting audio | 638 – 1,830 ms |
| First masking audio after question | ~2,000 ms |
| First grounded response audio (Twilio) | 568 – 1,322 ms (deployed EC2) |
| Barge-in clear event | ≤ 1 event per interruption |

Target: speech-end to first audible response ≤ 2.5 seconds. Telephone rendering (8 kHz mu-law) adds perceptual overhead not reflected above.

---

## Responsible AI and known limitations

**What VaaniSeva does not do:**
- Does not diagnose, prescribe, or provide dosage — health output is navigation and escalation only.
- Does not guarantee scheme eligibility or approval — all guidance is explicitly labelled.
- Does not claim to work without cellular voice coverage — the caller must have a call connection.
- Does not store sensitive personal data — Aadhaar/PAN/bank numbers are explicitly rejected.
- Does not loop background audio during user speech (damages VAD and caller trust).

**Bias and safety evidence:**
- Scheme data sourced from official government portals only; no inferred eligibility.
- Health scope is restricted to information and navigation; a safety layer blocks diagnosis and dosage at the application layer.
- The LLM is instructed to use feminine self-reference for Arya/Vidya and masculine for Hitesh — deterministic correction guards against gender drift.
- Live price sources are labelled with market name, date, and min/max/modal values; no statewide aggregation is implied.

---

## Scalability and deployment path

- **Current:** Single EC2 instance with Caddy TLS reverse proxy. Docker Compose for repeatable deploys. IAM instance role — no long-lived AWS keys on the server.
- **Cost per call (approximate):** Sarvam STT REST call (~1–2 s audio) + Bedrock Nova token cost + Cartesia/Sarvam TTS. Under ₹2–5 per call at current provider pricing for a 3-minute conversation.
- **Scale path:** Amazon Bedrock AgentCore Runtime (serverless, consumption-based, isolated sessions) — scaffolded but not yet deployed. Eliminates the permanent EC2 allocation.
- **Offline/low-connectivity:** The caller needs only cellular voice (2G voice is sufficient). The cloud backend needs internet; a future edge deployment with a cached scheme corpus and offline TTS model would extend this further.
- **Partner path:** NGO or government body distributes the phone number. No app install, no data plan. The scheme corpus can be updated without redeploying the voice pipeline.

---

## Local development

```bash
cd backend
cp .env.example .env          # fill in provider keys — never commit this file
pip install -r requirements-dev.txt

# Windows (recommended — avoids Python path issues)
.\deployment\run_realtime.ps1 -Port 7860

# Linux/macOS
python -m uvicorn vaaniseva_rt.server:app --host 127.0.0.1 --port 7860
```

Open `http://127.0.0.1:7860/local`, allow the microphone, and connect. `/health` must show all providers green before testing audio — a green health check alone does not prove the voice path works.

```bash
cd backend && pytest -q          # 43 tests, all pass
```

Human listening is the final acceptance gate. Automated tests verify persona state, tool selection, safety boundaries, and event behavior — not accent, pronunciation, or conversational feel.

---

## Website

Import this repository into Vercel with **Root Directory** set to `website`. Add one environment variable:

```env
VITE_VOICE_BASE_URL=https://your-deployed-voice-domain
```

No private key is used by the Vite build. Callback credentials stay in `backend/.env` on the server. The website embeds the same `/local` voice pipeline for browser calls and uses a server-side `/api/calls/callback` endpoint so Twilio credentials never reach the browser.

---

## Repository layout

```
backend/              Pipecat voice runtime (Python, FastAPI)
  vaaniseva_rt/       Core package — pipeline, MCP server, memory, personas, tools
  deployment/         Dockerfile, Docker Compose, IAM policies, Caddy config, run scripts
  tests/              43 automated backend tests
website/              React + Vite frontend (Vercel-ready)
docs/                 Architecture, security, and deployment detail
```

---

## SDG alignment

| SDG | How VaaniSeva addresses it |
|---|---|
| **SDG 1** — No Poverty | PM-Kisan, Jan Dhan, Mudra — verified benefit access for the poorest |
| **SDG 2** — Zero Hunger | Mandi price transparency for farmers; Fasal Bima awareness |
| **SDG 3** — Good Health | Safe health navigation, mental-health helplines, emergency escalation |
| **SDG 4** — Quality Education | Government scheme information as a form of civic knowledge access |
| **SDG 10** — Reduced Inequalities | Voice-only access removes the smartphone/literacy barrier |
| **SDG 16** — Peace, Justice, Strong Institutions | Connecting citizens to verified government services without intermediaries |

---

*Built by Team VaaniSeva. See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md), [docs/SECURITY.md](docs/SECURITY.md), and [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for detail.*
