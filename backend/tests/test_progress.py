from vaaniseva_rt.bot import TOOL_PROGRESS_SPEECH, should_play_tool_progress


def test_slow_scheme_and_mandi_lookups_have_audible_progress():
    assert "search_government_schemes" in TOOL_PROGRESS_SPEECH
    assert "get_scheme_eligibility" in TOOL_PROGRESS_SPEECH
    assert "get_mandi_price" in TOOL_PROGRESS_SPEECH


def test_health_paths_do_not_add_decorative_progress_speech():
    assert "search_health_information" not in TOOL_PROGRESS_SPEECH
    assert "get_verified_helpline" not in TOOL_PROGRESS_SPEECH


def test_exact_named_schemes_do_not_wait_behind_progress_audio():
    for query in ("PM Kisan Yojana", "पी एम आवास योजना", "योग मुद्रा योजना"):
        assert not should_play_tool_progress("search_government_schemes", {"query": query})


def test_broad_scheme_search_keeps_a_progress_cue():
    assert should_play_tool_progress(
        "search_government_schemes", {"query": "support for a low-income farmer"}
    )
