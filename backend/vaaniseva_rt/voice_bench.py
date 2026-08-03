"""Isolated, zero-LLM voice comparison for human acceptance testing."""

from __future__ import annotations

import base64
from typing import Any

import aiohttp

from .config import Settings

SAMPLES = {
    "greeting": "नमस्ते, मैं आर्या हूँ। बताइए, मैं आपकी कैसे मदद कर सकती हूँ?",
    "scheme": "पी एम किसान योजना की जानकारी मैं इस कॉल पर ही समझा सकती हूँ।",
}

OLD_CARTESIA_MODEL = "sonic-3"
OLD_CARTESIA_ARYA_VOICE = "95d51f79-c397-46f9-b49a-23763d3eaa2d"


def cartesia_request(text: str) -> tuple[dict[str, str], dict[str, Any]]:
    """Reproduce the Round 1 Arya configuration without reading a secret."""
    return (
        {
            "Cartesia-Version": "2025-04-16",
            "Content-Type": "application/json",
        },
        {
            "model_id": OLD_CARTESIA_MODEL,
            "transcript": text,
            "voice": {"mode": "id", "id": OLD_CARTESIA_ARYA_VOICE},
            "output_format": {
                "container": "wav",
                "encoding": "pcm_s16le",
                "sample_rate": 8000,
            },
            "language": "hi",
        },
    )


def sarvam_request(text: str) -> dict[str, Any]:
    """Match the current realtime Arya synthesis settings."""
    return {
        "inputs": [text],
        "target_language_code": "hi-IN",
        "speaker": "arya",
        "model": "bulbul:v2",
        "pace": 1.18,
        "pitch": 0.0,
        "loudness": 1.0,
        "enable_preprocessing": True,
    }


async def synthesize(provider: str, sample: str, settings: Settings) -> bytes:
    if sample not in SAMPLES:
        raise ValueError("Unknown voice sample")
    text = SAMPLES[sample]
    timeout = aiohttp.ClientTimeout(total=20)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        if provider == "cartesia":
            if not settings.cartesia_api_key:
                raise RuntimeError("CARTESIA_API_KEY is not configured")
            headers, payload = cartesia_request(text)
            headers["Authorization"] = f"Bearer {settings.cartesia_api_key}"
            async with session.post(
                "https://api.cartesia.ai/tts/bytes", headers=headers, json=payload
            ) as response:
                if response.status != 200:
                    detail = (await response.text())[:200]
                    raise RuntimeError(f"Cartesia TTS failed ({response.status}): {detail}")
                return await response.read()

        if provider == "sarvam":
            if not settings.sarvam_api_key:
                raise RuntimeError("SARVAM_API_KEY is not configured")
            async with session.post(
                "https://api.sarvam.ai/text-to-speech",
                headers={"api-subscription-key": settings.sarvam_api_key},
                json=sarvam_request(text),
            ) as response:
                if response.status != 200:
                    detail = (await response.text())[:200]
                    raise RuntimeError(f"Sarvam TTS failed ({response.status}): {detail}")
                result = await response.json()
                return base64.b64decode(result["audios"][0])

    raise ValueError("Unknown voice provider")
