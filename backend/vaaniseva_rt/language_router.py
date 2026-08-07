from __future__ import annotations

from collections.abc import Awaitable, Callable

from loguru import logger
from pipecat.frames.frames import Frame, TranscriptionFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.transcriptions.language import Language


SUPPORTED_LANGUAGES = {"hi", "mr", "ta", "en"}
LANGUAGE_ENUMS = {
    "hi": Language.HI,
    "mr": Language.MR,
    "ta": Language.TA,
    "en": Language.EN_IN,
}


def language_code(value: Language | str | None, transcript: str = "") -> str:
    """Resolve a supported language, giving an explicit caller request priority."""
    folded = transcript.casefold()
    explicit = (
        ("mr", ("मराठीत", "मराठी में", "मराठी मे", "in marathi", "marathi language")),
        ("ta", ("தமிழில்", "தமிழ் மொழி", "in tamil", "tamil language")),
        ("en", ("in english", "english language", "अंग्रेजी में", "इंग्लिश में")),
        ("hi", ("हिंदी में", "हिन्दी में", "in hindi", "hindi language")),
    )
    for code, cues in explicit:
        if any(cue in folded for cue in cues):
            return code
    raw = value.value if isinstance(value, Language) else str(value or "")
    code = raw.split("-", 1)[0].lower()
    return code if code in SUPPORTED_LANGUAGES else "hi"


class LanguageStateProcessor(FrameProcessor):
    """Apply STT language state before the transcript reaches the LLM."""

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
            resolved = language_code(frame.language, frame.text)
            if resolved != self._state.get("active"):
                self._state["active"] = resolved
                await self._on_language_changed(resolved)
                logger.bind(session=self._session_id, language=resolved).info("active_language_applied")
        await self.push_frame(frame, direction)
