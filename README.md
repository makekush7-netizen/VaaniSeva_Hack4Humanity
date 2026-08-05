<div align="center">

<img src="https://img.shields.io/badge/VaaniSeva-Voice%20AI%20for%20India-F0A832?style=for-the-badge&logo=phone&logoColor=white" alt="VaaniSeva" />

<h1>VaaniSeva</h1>
<h3>Voice access to essential public information — from any phone, in any language</h3>

<p>
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Pipecat-Streaming%20Pipeline-6C3BEB?style=flat-square" />
  <img src="https://img.shields.io/badge/Amazon%20Bedrock-Nova%20Lite-FF9900?style=flat-square&logo=amazon-aws&logoColor=white" />
  <img src="https://img.shields.io/badge/Sarvam%20AI-STT%20%2B%20TTS-00B4D8?style=flat-square" />
  <img src="https://img.shields.io/badge/Twilio-Media%20Streams-F22F46?style=flat-square&logo=twilio&logoColor=white" />
  <img src="https://img.shields.io/badge/MCP-In--process%20Tools-10B981?style=flat-square" />
  <img src="https://img.shields.io/badge/Tests-43%20passing-22C55E?style=flat-square&logo=pytest&logoColor=white" />
</p>

<p>
  <a href="https://vaani-seva-hack4-humanity.vercel.app"><strong>🌐 Live Website</strong></a> ·
  <a href="docs/ARCHITECTURE.md"><strong>Architecture</strong></a> ·
  <a href="docs/SECURITY.md"><strong>Security</strong></a> ·
  <a href="docs/DEPLOYMENT.md"><strong>Deployment</strong></a>
</p>

</div>

---

## Who this is for

> A farmer in rural Madhya Pradesh with a ₹500 keypad phone — no smartphone, no mobile data — asking *"what is today's potato price at Bhind mandi?"* or *"am I eligible for PM-Kisan?"* and receiving a **verified, grounded answer in spoken Hindi in under two seconds**, without touching a screen.

Over 500 million Indians are excluded from digital services — not because the information doesn't exist, but because it lives behind screens, apps, and data plans they don't have. VaaniSeva's answer: make India's verified public information reachable from **any phone, in any language, right now**.

---

## Architecture

```mermaid
flowchart TD
    A[📞 Phone Caller\nAny basic phone] -->|Twilio Programmable Voice| B[/twiml\nConnect + Stream]
    C[🌐 Browser Mic\nNo app needed] -->|Raw PCM WebSocket| D[/local/ws]

    B --> E
    D --> E

    subgraph E[" 🔁 Pipecat Streaming Pipeline "]
        direction TB
        E1[Silero VAD\nSpeech detection]
        E2[Sarvam Bulbul v2 STT\nREST · 16 kHz]
        E3[Intent + Persona Router\nDeterministic at app boundary]
        E4[Amazon Bedrock Nova\nReasoning + tool selection]
        E5[Safety / Evidence Layer\nNo invented facts · no diagnosis]
        E6[TTS\nCartesia Sonic 3 · Sarvam Bulbul v2]
        E1 --> E2 --> E3 --> E4 --> E5 --> E6
    end

    E4 -->|Tool calls| F

    subgraph F[" 🔧 In-process MCP Server "]
        direction LR
        F1[search_government_schemes]
        F2[get_mandi_price]
        F3[get_health_helpline]
        F4[check_scheme_eligibility]
        F5[switch_persona]
        F6[end_call]
    end

    F1 & F4 --> G[(DynamoDB RAG\nTitan Embeddings v2\nvaaniseva-vectors)]
    F2 --> H[data.gov.in\nAgmarknet live API]
    F3 --> I[Verified Helpline\nRegistry]

    E6 -->|μ-law 8kHz audio| A
    E6 -->|PCM audio| C

    E1 -.->|Barge-in detected| J[🛑 Cancel in-flight\nTTS + Bedrock generation]
```

**Pattern:** `End User → Agent (Bedrock Nova) → MCP Server → Grounded Data`

Every factual statement — scheme benefits, crop prices, helpline numbers — must originate from a tool result. The LLM is explicitly prohibited from inventing facts.

---

## Three specialist personas

| Persona | Voice | Domain |
|---|---|---|
| **Arya** 👩 | Cartesia Sonic 3 (Arushi) — warm, feminine | Government schemes · civic navigation · eligibility |
| **Hitesh** 👨‍🌾 | Sarvam Bulbul v2 (Abhilash) — masculine | Agriculture advisory · live mandi prices |
| **Vidya** 👩‍⚕️ | Sarvam Bulbul v2 (Vidya) — feminine | Health navigation · helplines · safe escalation |

Persona transfer is **atomic** — application state, Bedrock system instruction, and TTS voice switch together. Gender-correct Hindi first-person forms are enforced deterministically before TTS.

---

## Context engineering

| Technique | How it's implemented |
|---|---|
| **RAG** | Titan Text Embeddings v2 → DynamoDB `vaaniseva-vectors`; cosine search; 10-min vector cache |
| **Curated fallback** | Official-source scheme snapshot used when AWS retrieval is unavailable |
| **Structured memory** | One-paragraph continuity summary per consenting caller; model sees text, never the DB |
| **Tool-grounded reasoning** | Model cannot state a price, benefit, or helpline without a tool result |
| **Localization-aware context** | System prompts in target language; regional Indian speech patterns |
| **Guardrails before output** | Safety layer blocks diagnosis, dosage, and invented prices before TTS |
| **Multi-step planning** | Intent router → domain tool → evidence validation → safety policy → persona voice |

---

## MCP tools

<details>
<summary><strong>View all 6 MCP tools</strong></summary>

| Tool | Data source | Fail behaviour |
|---|---|---|
| `search_government_schemes` | DynamoDB RAG + curated official snapshot | Returns fallback snapshot, never invents |
| `check_scheme_eligibility` | Same corpus | Returns "verify with official source" |
| `get_mandi_price` | data.gov.in Agmarknet (live) | Reports unavailability, no invented price |
| `get_health_helpline` | Curated verified numbers (iCall, Vandrevala, NIMHANS) | Static, deterministic |
| `switch_persona` | Internal application state | Atomic — state + Bedrock + TTS together |
| `end_call` | Twilio REST API | Queues Hindi goodbye then `EndFrame` |

Adding a new knowledge domain = one new MCP tool with a source label, safety scope, and freshness date. No LLM prompt restructuring needed.

</details>

---

## Datasets

| Dataset | Usage |
|---|---|
| **data.gov.in — Agmarknet** | Live mandi observations, 3,000+ mandis across India |
| **Amazon Titan Text Embeddings v2** | Scheme document vectors in DynamoDB |
| **Curated central scheme corpus** *(built for this project)* | PM-Kisan, Ayushman Bharat, MGNREGA, PM Awas, Sukanya Samriddhi, PM Ujjwala, Jan Dhan, Mudra — with Hindi/English aliases, eligibility, official source, verification date |
| **iCall / Vandrevala / NIMHANS registry** | Verified mental-health helplines |
| **Kisan Call Centre 1551** | Agriculture helpline routing |

No user speech is stored. Caller memory is bounded, consent-gated, and deletable on request.

---

## Latency (measured, not claimed)

| Stage | Local — provider-backed | EC2 — real Twilio call |
|---|---|---|
| First greeting audio | 638 – 1,830 ms | **568 ms** |
| First grounded response audio | 1,082 – 3,432 ms | **1,267 ms** |
| First masking audio (search cue) | ~2,000 ms | — |
| Barge-in clear event | 1 per interruption | 1 per interruption |

Target: speech-end → first audible response ≤ 2.5 s. Telephone mu-law 8 kHz rendering adds perceptual overhead not reflected above.

---

## Responsible AI

<details>
<summary><strong>What VaaniSeva does not do</strong></summary>

- Does not diagnose, prescribe, or provide dosage — health output is navigation and escalation only
- Does not guarantee scheme eligibility or approval — all guidance is explicitly labelled as guidance
- Does not claim to work without cellular voice coverage — the caller must have a call connection
- Does not store Aadhaar/PAN/bank numbers, OTPs, or precise addresses — explicitly rejected
- Does not invent prices, benefits, or helpline numbers — the LLM is prohibited from filling data gaps

</details>

<details>
<summary><strong>Bias and safety evidence</strong></summary>

- Scheme data sourced from official government portals only; no inferred eligibility
- Health scope restricted at the application layer — the MCP tool never returns diagnosis or dosage
- Deterministic Hindi gender-agreement correction guards against persona drift
- Live price responses include market name, date, and min/max/modal values — no statewide aggregation implied
- Empty or failed data lookups are described as unavailable, not substituted with model knowledge

</details>

---

## SDG alignment

| SDG | VaaniSeva contribution |
|---|---|
| **SDG 1** — No Poverty | PM-Kisan, Jan Dhan, Mudra — verified benefit access for the poorest |
| **SDG 2** — Zero Hunger | Live mandi price transparency for farmers; Fasal Bima awareness |
| **SDG 3** — Good Health | Safe health navigation, mental-health helplines, emergency escalation |
| **SDG 10** — Reduced Inequalities | Voice-only access removes the smartphone and literacy barrier |
| **SDG 16** — Strong Institutions | Connecting citizens to verified government services without intermediaries |

---

## Scalability and deployment path

| Stage | Status |
|---|---|
| Local browser voice | ✅ Human-accepted |
| EC2 + Caddy TLS deployment | ✅ Live at `voice.vaanisevaai.me` |
| Real Twilio PSTN call (end-to-end) | ✅ Completed — latency rated "exceptionally good" |
| AgentCore serverless deployment | 🔄 Scaffolded, deferred until stable |
| Offline / edge deployment | 🗺️ Roadmap — cached scheme corpus + on-device TTS model |

**Per-call cost (approximate):** ~₹11–14 for a 3-minute conversation at current provider pricing. Drops sharply at volume. No permanent compute cost when calls are not happening (serverless target).

**Partner path:** An NGO or government body distributes the phone number. No app install, no data plan, no literacy requirement. The scheme corpus updates without redeploying the voice pipeline.

---

## Local development

```bash
cd backend
cp .env.example .env          # fill in provider keys — never commit this file
pip install -r requirements-dev.txt
```

```powershell
# Windows (recommended — avoids Python path issues on 3.13)
.\deployment\run_realtime.ps1 -Port 7860
```

Open `http://127.0.0.1:7860/local`, allow the microphone, and connect.

> ⚠️ `/health` green alone does not prove the voice path works. Run a provider-backed smoke test before each human audio session.

```bash
cd backend && pytest -q     # 43 tests, all pass
```

Human listening is the final acceptance gate — automated tests verify persona state, tool selection, and event behaviour, not accent, pronunciation, or conversational feel.

---

## Website (Vercel)

Import this repository into Vercel with **Root Directory** set to `website`. Add:

```env
VITE_VOICE_BASE_URL=https://your-deployed-voice-domain
```

No private key is compiled into the Vite build. Callback credentials stay in `backend/.env` on the server.

---

## Repository layout

```
backend/              Pipecat voice runtime (Python · FastAPI · Uvicorn)
  vaaniseva_rt/       Core package — pipeline, MCP server, memory, personas, tools
  deployment/         Dockerfile · Docker Compose · IAM policies · Caddy config
  tests/              43 automated backend tests
website/              React + Vite frontend (Vercel-ready)
docs/                 Architecture · Security · Deployment detail
```

---

<div align="center">

**Built by Team VaaniSeva** — *access to knowledge is a right, not a privilege of smartphone ownership.*

[Website](https://vaani-seva-hack4-humanity.vercel.app) · [Architecture](docs/ARCHITECTURE.md) · [Security](docs/SECURITY.md) · [Deployment](docs/DEPLOYMENT.md)

</div>
