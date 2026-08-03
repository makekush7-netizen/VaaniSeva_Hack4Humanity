from __future__ import annotations

import wave
from pathlib import Path

from pipecat.frames.frames import OutputAudioRawFrame

CLIP_FOR_TOOL = {
    "search_government_schemes": "checking_scheme.wav",
    "get_scheme_eligibility": "checking_scheme.wav",
    "get_verified_helpline": "checking_health.wav",
    "search_health_information": "checking_health.wav",
    "get_mandi_price": "checking_price.wav",
}

SEARCH_CUE_TOOLS = {
    "search_government_schemes",
    "get_scheme_eligibility",
    "get_mandi_price",
}


class ClipLibrary:
    def __init__(self, root: Path):
        self.root = root

    def frame_for_tool(self, tool_name: str, expected_sample_rate: int = 8000, persona: str = "arya"):
        filename = CLIP_FOR_TOOL.get(tool_name)
        if not filename:
            return None
        path = self.root / filename if filename else None
        if persona != "hitesh" and path and path.exists():
            with wave.open(str(path), "rb") as wav:
                if wav.getsampwidth() != 2:
                    raise ValueError(f"Clip must be 16-bit PCM: {path}")
                if wav.getframerate() == expected_sample_rate:
                    return OutputAudioRawFrame(
                        audio=wav.readframes(-1), sample_rate=wav.getframerate(), num_channels=wav.getnchannels()
                    )
        return None

    def _prepared_frame(self, cue_name: str, expected_sample_rate: int):
        path = self.root / f"{cue_name}_{expected_sample_rate}.wav"
        if not path.is_file():
            return None
        with wave.open(str(path), "rb") as wav:
            if (wav.getnchannels(), wav.getsampwidth(), wav.getframerate()) != (
                1,
                2,
                expected_sample_rate,
            ):
                raise ValueError(f"Cue must be mono PCM16 at {expected_sample_rate} Hz: {path}")
            return OutputAudioRawFrame(
                audio=wav.readframes(-1),
                sample_rate=expected_sample_rate,
                num_channels=1,
            )

    def frame_for_handoff(self, expected_sample_rate: int = 8000):
        """Human-approved Open/transfer cue, prepared at -14 dB."""
        return self._prepared_frame("handoff_open", expected_sample_rate)

    def frame_for_search(self, tool_name: str, expected_sample_rate: int = 8000):
        """Finite laptop-typing texture for non-sensitive verified lookups only."""
        if tool_name not in SEARCH_CUE_TOOLS:
            return None
        return self._prepared_frame("search_typing", expected_sample_rate)
