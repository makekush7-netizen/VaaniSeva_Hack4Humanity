"""Test ElevenLabs API — check subscription, voices, and Hindi TTS latency."""
import os, requests, time, json
from dotenv import load_dotenv
load_dotenv(override=False)

key = os.environ.get("ELEVENLABS_API_KEY", "")
if not key:
    print("ERROR: ELEVENLABS_API_KEY not set in .env")
    exit(1)
h = {"xi-api-key": key}

# Check subscription/credits
r = requests.get("https://api.elevenlabs.io/v1/user/subscription", headers=h, timeout=10)
print("Sub status:", r.status_code)
if r.ok:
    d = r.json()
    print("Tier:", d.get("tier"))
    print("Chars remaining:", d.get("character_count"), "/", d.get("character_limit"))

# Get voice list
r2 = requests.get("https://api.elevenlabs.io/v1/voices", headers=h, timeout=10)
if r2.ok:
    voices = r2.json().get("voices", [])
    print(f"Voices available: {len(voices)}")
    for v in voices[:8]:
        vid = v["voice_id"]
        name = v["name"]
        lang = v.get("labels", {}).get("language", "?")
        print(f"  {vid} - {name} ({lang})")

# Quick latency test — Hindi TTS with turbo model
print("\n--- Hindi TTS Latency Test ---")
t0 = time.time()
r3 = requests.post(
    "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM",
    headers={**h, "Content-Type": "application/json"},
    json={
        "text": "नमस्ते, मैं आपकी मदद कर सकती हूँ।",
        "model_id": "eleven_turbo_v2_5",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    },
    timeout=15
)
t1 = time.time()
print(f"Turbo v2.5: status={r3.status_code}, time={t1-t0:.2f}s, bytes={len(r3.content)}")

# Also test multilingual v2 model
t2 = time.time()
r4 = requests.post(
    "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM",
    headers={**h, "Content-Type": "application/json"},
    json={
        "text": "नमस्ते, मैं आपकी मदद कर सकती हूँ। किसान सम्मान निधि के बारे में बताती हूँ।",
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}
    },
    timeout=15
)
t3 = time.time()
print(f"Multilingual v2: status={r4.status_code}, time={t3-t2:.2f}s, bytes={len(r4.content)}")

# Compare with Sarvam
print("\n--- Sarvam TTS Latency Test ---")
sarvam_key = os.environ.get("SARVAM_API_KEY", "")
if not sarvam_key:
    print("Skipping Sarvam test: SARVAM_API_KEY not set")
else:
t4 = time.time()
r5 = requests.post(
    "https://api.sarvam.ai/text-to-speech",
    json={
        "inputs": ["नमस्ते, मैं आपकी मदद कर सकती हूँ।"],
        "target_language_code": "hi-IN",
        "speaker": "arya",
        "model": "bulbul:v2",
        "pace": 1.25
    },
    headers={"api-subscription-key": sarvam_key},
    timeout=8
)
t5 = time.time()
print(f"Sarvam: status={r5.status_code}, time={t5-t4:.2f}s")
