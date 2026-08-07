from vaaniseva_rt.bot import TOOL_PROGRESS_SPEECH


def test_slow_scheme_and_mandi_lookups_have_audible_progress():
    assert "search_government_schemes" in TOOL_PROGRESS_SPEECH
    assert "get_scheme_eligibility" in TOOL_PROGRESS_SPEECH
    assert "get_mandi_price" in TOOL_PROGRESS_SPEECH


def test_health_paths_do_not_add_decorative_progress_speech():
    assert "search_health_information" not in TOOL_PROGRESS_SPEECH
    assert "get_verified_helpline" not in TOOL_PROGRESS_SPEECH
