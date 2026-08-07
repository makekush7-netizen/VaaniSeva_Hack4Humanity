from __future__ import annotations

from collections.abc import Awaitable, Callable

from loguru import logger
from pipecat.frames.frames import Frame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.transcriptions.language import Language


LANGUAGE_ENUMS = {
    "hi": Language.HI,
    "mr": Language.MR,
    "ta": Language.TA,
    "en": Language.EN_IN,
}

_LANGUAGE_CUES = {
    "mr": ("मराठी", "marathi"),
    "ta": ("तमिल", "தமிழ்", "tamil"),
    "en": ("अंग्रेजी", "अंग्रेज़ी", "इंग्लिश", "english"),
    "hi": ("हिंदी", "हिन्दी", "hindi"),
}

_REQUEST_CUES = (
    "बोल", "बात", "जवाब", "उत्तर", "बताओ", "सांगा", "बोला", "करो",
    "speak", "talk", "answer", "reply", "respond", "switch", "continue",
    "பேச", "சொல்ல",
)


def explicit_language_request(transcript: str) -> str | None:
    """Return a language only when the caller explicitly asks to switch."""
    folded = transcript.casefold()
    if not any(cue in folded for cue in _REQUEST_CUES):
        return None
    for code, cues in _LANGUAGE_CUES.items():
        if any(cue in folded for cue in cues):
            return code
    return None


class ExplicitLanguageProcessor(FrameProcessor):
    """Apply caller-requested language state without trusting noisy STT detection."""

    def __init__(
        self,
        state: dict[str, str],
        on_language_changed: Callable[[str], Awaitable[None]],
        session_id: str = "",
    ) -> None:
        super().__init__()
        self._state = state
        self._on_language_changed = on_language_changed
        self._session_id = session_id

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, TranscriptionFrame):
            requested = explicit_language_request(frame.text)
            if requested and requested != self._state.get("active"):
                self._state["active"] = requested
                await self._on_language_changed(requested)
                logger.bind(session=self._session_id, language=requested).info(
                    "explicit_language_applied"
                )
        await self.push_frame(frame, direction)
