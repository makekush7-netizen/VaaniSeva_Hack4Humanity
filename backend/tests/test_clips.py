from pathlib import Path
import wave

from vaaniseva_rt.clips import ClipLibrary


def test_unknown_tool_has_no_acknowledgement():
    assert ClipLibrary(Path("missing")).frame_for_tool("switch_persona") is None


def test_hitesh_does_not_use_generated_acknowledgement_fallback():
    frame = ClipLibrary(Path("missing")).frame_for_tool("get_mandi_price", expected_sample_rate=24000, persona="hitesh")

    assert frame is None


def test_missing_or_mismatched_clip_does_not_use_generated_tts_fallback():
    frame = ClipLibrary(Path("missing")).frame_for_tool("get_scheme_eligibility", expected_sample_rate=24000, persona="arya")

    assert frame is None


def test_selected_handoff_and_search_cues_exist_at_browser_and_phone_rates():
    root = Path(__file__).parents[1] / "vaaniseva_rt" / "assets" / "sounds"
    library = ClipLibrary(root)

    for rate in (8000, 24000):
        handoff = library.frame_for_handoff(rate)
        search = library.frame_for_search("get_mandi_price", rate)
        assert handoff is not None and handoff.sample_rate == rate
        assert search is not None and search.sample_rate == rate


def test_search_texture_is_finite_and_excluded_from_sensitive_tools():
    root = Path(__file__).parents[1] / "vaaniseva_rt" / "assets" / "sounds"
    library = ClipLibrary(root)

    assert library.frame_for_search("search_health_information", 24000) is None
    assert library.frame_for_search("get_verified_helpline", 24000) is None
    assert library.frame_for_search("remember_caller_preference", 24000) is None
    with wave.open(str(root / "search_typing_24000.wav"), "rb") as wav:
        assert wav.getnframes() / wav.getframerate() <= 2.5
