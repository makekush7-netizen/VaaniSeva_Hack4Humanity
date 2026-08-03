from vaaniseva_rt.voice_bench import (
    OLD_CARTESIA_ARYA_VOICE,
    OLD_CARTESIA_MODEL,
    SAMPLES,
    cartesia_request,
    sarvam_request,
)


def test_cartesia_bench_reproduces_round_one_arya_configuration():
    headers, payload = cartesia_request(SAMPLES["greeting"])

    assert "Authorization" not in headers
    assert payload["model_id"] == OLD_CARTESIA_MODEL == "sonic-3"
    assert payload["voice"]["id"] == OLD_CARTESIA_ARYA_VOICE
    assert payload["language"] == "hi"
    assert payload["output_format"]["sample_rate"] == 8000


def test_sarvam_bench_matches_current_realtime_arya_settings():
    payload = sarvam_request(SAMPLES["scheme"])

    assert payload["model"] == "bulbul:v2"
    assert payload["speaker"] == "arya"
    assert payload["pace"] == 1.18
    assert payload["target_language_code"] == "hi-IN"


def test_bench_samples_cover_greeting_and_pm_kisan_pronunciation():
    assert "कर सकती हूँ" in SAMPLES["greeting"]
    assert "पी एम किसान" in SAMPLES["scheme"]
