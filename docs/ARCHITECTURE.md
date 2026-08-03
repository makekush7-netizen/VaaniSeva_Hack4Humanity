# Architecture and design choices

## Real-time path

Twilio posts to `/twiml`, receives `<Connect><Stream>`, and opens `/ws`. The server
validates Twilio signatures at both boundaries. Pipecat streams audio through Silero
VAD, Sarvam speech recognition, Amazon Bedrock Nova, MCP tools, and streaming TTS.
The transport supports barge-in so a caller can interrupt naturally.

The browser demo uses `/local/ws` with raw PCM and the identical agent pipeline. It
does not create a Twilio call and is embedded by the Vercel site with microphone
permission.

## Agent and ambience

Arya handles general navigation, Hitesh agriculture and mandi questions, and Vidya
health navigation. Intent routing can transfer to the right specialist even when the
caller asks the current persona. Handoff and search cues are quiet, short, and never
mask generated speech. The agent can end a call after a clear user request.

## MCP and knowledge

The in-process MCP server exposes narrow tools for schemes, eligibility guidance,
mandi observations, verified helplines, and safe health navigation. Scheme retrieval
first uses Amazon Titan embeddings against the read-only `vaaniseva-vectors`
DynamoDB corpus. Vectors are cached for ten minutes to reduce cost and latency. If
AWS retrieval is denied or unavailable, the tool returns the curated official-source
snapshot; it never silently fabricates a match.

Mandi data comes from the Government of India data.gov.in resource. Every response
contains its source and check time. Empty or failed results are described as
unavailable rather than turned into a price.

## Memory

The telephone number is transformed with an application salt into a one-way caller
identifier. The model sees a short, bounded continuity summary, not database access.
The system is designed to avoid identity documents, medical records, financial
credentials, and other high-risk personal data.
