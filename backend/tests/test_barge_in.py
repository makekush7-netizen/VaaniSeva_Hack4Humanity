import asyncio
import json

from pipecat.frames.frames import InterruptionFrame
from pipecat.serializers.twilio import TwilioFrameSerializer


def test_interruption_serializes_as_twilio_clear():
    serializer = TwilioFrameSerializer(
        stream_sid="MZ_test",
        params=TwilioFrameSerializer.InputParams(auto_hang_up=False),
    )
    wire = asyncio.run(serializer.serialize(InterruptionFrame()))
    assert json.loads(wire) == {"event": "clear", "streamSid": "MZ_test"}
