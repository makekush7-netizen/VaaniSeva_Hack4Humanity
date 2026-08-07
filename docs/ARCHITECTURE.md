# Architecture and design choices

## Pattern: End User → Agent → MCP Server → Grounded Data

VaaniSeva follows the agentic architecture pattern the judges are looking for:

```
Caller → Transport → Pipecat Orchestration → Bedrock Nova (Agent/LLM)
                                                    ↓
                                          In-process MCP Server
                                          (domain logic + guardrails)
                                                    ↓
                          ┌─────────────────────────────────────────┐
                          │           Grounded Data Sources          │
                          │  • DynamoDB RAG (Titan Embeddings v2)   │
                          │  • data.gov.in Agmarknet (live mandi)   │
                          │  • Curated official scheme snapshot      │
                          │  • Verified helpline registry            │
                          └─────────────────────────────────────────┘
```

---

## Real-time voice path

### Telephone (Twilio)
Twilio posts to `/twiml`, receives `<Connect><Stream>`, and opens `/ws`. The server
validates Twilio HMAC-SHA1 signatures at both boundaries, including the
trailing-slash edge case Twilio documents. Audio arrives as mu-law 8 kHz; the
pipeline converts to 16 kHz linear PCM for STT.

### Browser (/local/ws)
Raw 16 kHz PCM from the browser's microphone over WebSocket. Identical agent
pipeline — no Twilio required. The browser demo on the Vercel site uses this path.

---

## Pipecat pipeline stages

1. **Silero VAD** — detects speech / silence boundaries without sending audio to any
   external service. Triggers barge-in cancel when the caller speaks over playback.
2. **Sarvam Saaras v3 STT** — REST call on complete utterance segments (16 kHz).
   Chosen over WebSocket STT after reliability testing showed the REST path is
   significantly more consistent for Indian languages.
3. **Language + persona router** — deterministic at the application layer. Sarvam's
   detected/requested language becomes authoritative state before the turn reaches
   Bedrock and selects the same-language RAG partition and TTS language. Scheme and
   eligibility → Arya; mandi, crop, and pests → Hitesh; health and health numbers → Vidya.
4. **Amazon Bedrock Nova (Converse + streaming)** — reasoning and tool selection. The
   LLM sees only the bounded caller memory summary and the MCP tool definitions; it
   never has direct database access.
5. **In-process MCP server** — the only path to external facts (see below).
6. **Safety / evidence layer** — intercepts health output before TTS; blocks diagnosis,
   dosage, and invented prices; escalates emergencies to verified helplines.
7. **TTS** — Sarvam Bulbul v2 for Arya and Hitesh; Cartesia Sonic 3 for Hindi Vidya.
   Marathi, Tamil, and English force Sarvam's multilingual route. Voice, language, and
   Bedrock system instruction switch atomically.
8. **Barge-in** — Twilio `clear` or browser stop fires immediately when VAD detects
   caller speech during playback, cancelling in-flight TTS and Bedrock generation.

---

## Agent personas — one clear role each

| Persona | Voice | Domain scope |
|---|---|---|
| **Arya** | Sarvam Bulbul v2 (Vidya speaker) | Government schemes, civic navigation, eligibility |
| **Hitesh** | Sarvam Bulbul v2 (Abhilash) | Agriculture advisory, mandi prices |
| **Vidya** | Cartesia Sonic 3 in Hindi; Sarvam in other languages | Health navigation, helplines, safe escalation |

Persona transfer is atomic: application state, Bedrock system instruction (regenerated
from application state, not from conversation history), and TTS provider/voice all
switch together. A deterministic layer also corrects obvious Hindi gender-agreement
drift before text reaches TTS.

---

## MCP Server — domain logic and guardrails

The in-process MCP server enforces:
- **Source labelling** — every tool result includes source name, verification date,
  and geography. The model is instructed to cite these.
- **Fail-closed behaviour** — if a data source is unavailable, the tool returns
  "information not available" rather than allowing the model to fill the gap.
- **Scope boundaries** — scheme tools cannot access health tools and vice versa.
  The `get_health_guidance` tool never returns diagnosis or dosage.
- **Deterministic domain routing** — crop/pest queries invoke Hitesh's agriculture
  tool; health-number queries invoke Vidya; generic health queries never return the
  COVID-specific `1075` as a national-health number.
- **Location-exact mandi behaviour** — district/market filters are passed to the
  official API and an empty exact result asks for the nearest mandi instead of
  substituting records from unrelated cities.
- **Extensibility** — adding a new knowledge domain means adding one MCP tool with
  a source label, safety scope, and freshness date. No LLM prompt restructuring needed.

---

## Context engineering

| Technique | Implementation |
|---|---|
| **RAG** | Titan Text Embeddings v2 → DynamoDB `vaaniseva-vectors`; cosine search; 10-min vector cache |
| **Curated fallback** | Official-source scheme snapshot used if AWS retrieval fails |
| **Structured memory** | One-paragraph continuity summary per consenting caller; model sees text, not DB |
| **Tool-grounded reasoning** | Model may not state factual figures without a tool result |
| **Localization-aware context** | STT language state → same-language RAG → same-language TTS; gender-correct Hindi forms and deterministic spoken-number formatting |
| **Multi-step planning** | Intent router → domain tool → evidence validation → safety policy → persona voice |
| **Guardrails before output** | Safety layer blocks diagnosis, dosage, invented prices before TTS |

---

## Ambience and latency masking

A pre-selected CC0/Mixkit audio palette provides two sounds:
- **Handoff cue** (Kenney `open_001`, 148 ms, −14 dB) — played once on persona transfer.
- **Typing texture** (Mixkit laptop, 1.8 s finite, −24 dB) — played during scheme
  search, eligibility, and mandi tool calls only. Excluded from health, helpline,
  memory, consent, and identity paths.

No audio loops. Pipecat interruption clears queued audio immediately. Ambience does
not play during user speech (would damage VAD and STT). All assets have documented
licences.

---

## Memory and privacy

- Telephone number is salted and hashed to a one-way caller identifier before storage.
- On each call with consent, the model sees a one-paragraph continuity summary
  (preferred name, language, persona, broad help need). It never sees the database.
- The model may propose a constrained memory patch (e.g. "update preferred persona
  to Hitesh"); deterministic application code validates and applies or rejects it.
- Rejected content: Aadhaar/PAN/bank numbers, OTPs, precise address, detailed
  medical/financial/legal records, user-requested deletions.
- Memory is bounded, inspectable, and deletable on caller request.

---

## Latency (measured stage timings)

| Stage | Local (provider-backed) | Deployed EC2 (Twilio) |
|---|---|---|
| First greeting audio | 638 – 1,830 ms | 568 ms |
| First grounded response audio | 1,082 – 3,432 ms | 1,267 ms |
| First masking audio (search cue) | ~2,000 ms | — |
| Barge-in clear event | 1 per interruption | 1 per interruption |

Target: speech-end to first audible response ≤ 2.5 s. Telephone mu-law 8 kHz rendering adds perceptual overhead not reflected above. Record measured timings; do not claim the target until measured.

---

## What this system cannot yet do

- Does not work without cellular voice coverage — the caller must have a call connection.
- Does not operate offline — the cloud backend requires internet.
- Does not diagnose, prescribe, or approve government benefits — all output is guidance.
- Sarvam WebSocket STT was found unreliable; REST STT is used instead.
- AgentCore deployment is scaffolded but not yet live — EC2 is the production host.
- DynamoDB RAG requires the EC2 instance role to have `dynamodb:DescribeTable` + `dynamodb:Scan`; the curated snapshot is the current fallback.
