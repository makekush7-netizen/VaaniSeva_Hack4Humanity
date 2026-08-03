from __future__ import annotations

from collections.abc import AsyncGenerator

import aiohttp
from loguru import logger
from pipecat.frames.frames import ErrorFrame, Frame, TranscriptionFrame
from pipecat.services.stt_service import SegmentedSTTService
from pipecat.transcriptions.language import Language
from pipecat.utils.time import time_now_iso8601


class SarvamRESTSTTService(SegmentedSTTService):
    """Reliable turn-segment upload path for Sarvam Saaras v3."""

    def __init__(self, api_key: str, *, sample_rate: int = 8000) -> None:
        super().__init__(sample_rate=sample_rate)
        self._api_key = api_key

    async def run_stt(self, audio: bytes) -> AsyncGenerator[Frame | None, None]:
        headers = {"api-subscription-key": self._api_key}
        form = aiohttp.FormData()
        form.add_field("file", audio, filename="turn.wav", content_type="audio/wav")
        form.add_field("model", "saaras:v3")
        form.add_field("language_code", "unknown")
        form.add_field("mode", "codemix")

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=15)) as session:
                async with session.post(
                    "https://api.sarvam.ai/speech-to-text", data=form, headers=headers
                ) as response:
                    if response.status != 200:
                        detail = (await response.text())[:240]
                        logger.error("sarvam_rest_failed status={} detail={}", response.status, detail)
                        yield ErrorFrame(error=f"Sarvam REST STT failed with status {response.status}")
                        return
                    result = await response.json()
        except Exception as exc:
            logger.exception("sarvam_rest_failed")
            yield ErrorFrame(error=f"Sarvam REST STT failed: {type(exc).__name__}")
            return

        transcript = str(result.get("transcript") or "").strip()
        detected = str(result.get("language_code") or "hi-IN")
        logger.info("sarvam_rest_transcript language={} text={}", detected, transcript[:120])
        if transcript:
            try:
                language = Language(detected)
            except ValueError:
                language = Language.HI_IN
            yield TranscriptionFrame(
                transcript,
                self._user_id,
                time_now_iso8601(),
                language,
                result=result,
            )
