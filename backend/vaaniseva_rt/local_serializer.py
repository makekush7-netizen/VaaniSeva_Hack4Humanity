from __future__ import annotations

import json

from pipecat.frames.frames import (
    AudioRawFrame,
    CancelFrame,
    EndFrame,
    Frame,
    InputAudioRawFrame,
    InterruptionFrame,
    OutputTransportMessageFrame,
    OutputTransportMessageUrgentFrame,
    TranscriptionFrame,
)
from pipecat.serializers.base_serializer import FrameSerializer


class LocalPCMFrameSerializer(FrameSerializer):
    """Tiny browser protocol: binary PCM16 audio plus JSON control events."""

    def __init__(self, sample_rate: int = 8000) -> None:
        super().__init__()
        self._sample_rate = sample_rate

    async def serialize(self, frame: Frame) -> str | bytes | None:
        if isinstance(frame, AudioRawFrame):
            return frame.audio
        if isinstance(frame, InterruptionFrame):
            return json.dumps({"type": "clear"})
        if isinstance(frame, TranscriptionFrame) and frame.text.strip():
            return json.dumps({
                "type": "transcript",
                "text": frame.text.strip(),
                "final": frame.finalized,
            }, ensure_ascii=False)
        if isinstance(frame, (EndFrame, CancelFrame)):
            return json.dumps({"type": "ended"})
        if isinstance(frame, (OutputTransportMessageFrame, OutputTransportMessageUrgentFrame)):
            return json.dumps({"type": "event", "payload": frame.message})
        return None

    async def deserialize(self, data: str | bytes) -> Frame | None:
        if isinstance(data, bytes):
            if not data or len(data) % 2:
                return None
            return InputAudioRawFrame(
                audio=data,
                sample_rate=self._sample_rate,
                num_channels=1,
            )

        try:
            message = json.loads(data)
        except (TypeError, json.JSONDecodeError):
            return None

        if message.get("type") == "stop":
            return EndFrame()
        return None
