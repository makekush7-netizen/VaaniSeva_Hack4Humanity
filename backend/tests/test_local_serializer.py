import json
import asyncio

from pipecat.frames.frames import InputAudioRawFrame, InterruptionFrame, OutputAudioRawFrame

from vaaniseva_rt.local_serializer import LocalPCMFrameSerializer


def test_local_serializer_maps_binary_pcm_both_directions():
    serializer = LocalPCMFrameSerializer(sample_rate=8000)
    pcm = b"\x00\x00\x10\x00"

    decoded = asyncio.run(serializer.deserialize(pcm))
    assert isinstance(decoded, InputAudioRawFrame)
    assert decoded.audio == pcm
    assert decoded.sample_rate == 8000

    encoded = asyncio.run(serializer.serialize(OutputAudioRawFrame(pcm, 8000, 1)))
    assert encoded == pcm


def test_local_serializer_maps_interruption_to_clear_event():
    serializer = LocalPCMFrameSerializer()
    message = json.loads(asyncio.run(serializer.serialize(InterruptionFrame())))
    assert message == {"type": "clear"}
