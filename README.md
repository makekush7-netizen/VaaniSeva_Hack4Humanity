# VaaniSeva — voice access to essential public information

VaaniSeva is Team NovaFrost's Hack4Humanity 2026 project: a low-latency,
multilingual voice agent that works through an ordinary telephone call or a web
microphone. It helps callers navigate government schemes, recent mandi observations,
and safe health information without requiring a smartphone or mobile data.

## What judges can verify

- A standalone Pipecat voice runtime (`backend/`) rather than a hosted Vapi dependency.
- Bidirectional Twilio Media Streams with interruption/barge-in support.
- Sarvam STT, Amazon Bedrock Nova reasoning, Cartesia/Sarvam speech, and persona routing.
- An in-process MCP server whose tools enforce source labels and safety boundaries.
- Read-only semantic RAG over DynamoDB vectors generated with Amazon Titan Embeddings v2,
  with a curated official-source fallback when AWS retrieval is unavailable.
- Live data.gov.in mandi observations that fail closed instead of inventing prices.
- Low-volume handoff and search ambience with documented audio licences.
- Privacy-minimised caller memory keyed by a one-way phone identifier.
- A Vercel-ready website (`website/`) for browser voice and server-side callbacks.

## Architecture

```text
Phone caller -> Twilio -> HTTPS/WSS -> Caddy -> FastAPI/Pipecat
Browser mic  -------------------------------> local PCM WebSocket
                                                |
                 Sarvam STT -> Bedrock Nova -> MCP tools -> Cartesia/Sarvam TTS
                                                |            |
                           Titan + DynamoDB RAG / data.gov.in / safe caller memory
```

See [architecture](docs/ARCHITECTURE.md), [security](docs/SECURITY.md), and
[deployment](docs/DEPLOYMENT.md).

## Local voice test

```bash
cd backend
cp .env.example .env
pip install -r requirements-dev.txt
python -m uvicorn vaaniseva_rt.server:app --host 127.0.0.1 --port 7860
```

Open `http://127.0.0.1:7860/local`, allow the microphone, and connect. Provider
and Twilio secrets belong only in `backend/.env`, which Git ignores.

Run automated checks with `pytest -q` from `backend`. Human listening remains the
final acceptance gate for pronunciation, latency, interruptions, persona gender,
and ambience; automated tests cannot certify those.

## Website

Import the repository into Vercel with **Root Directory** set to `website`. Add:

```env
VITE_VOICE_BASE_URL=https://voice.vaanisevaai.me
```

No private key is used by the Vite build. Callback credentials stay in the backend.
