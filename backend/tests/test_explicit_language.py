from vaaniseva_rt.explicit_language import explicit_language_request


def test_explicit_language_requests_are_recognized():
    assert explicit_language_request("अब मुझसे मराठी में बात करो") == "mr"
    assert explicit_language_request("Please answer me in English") == "en"
    assert explicit_language_request("तमिल में बोलो") == "ta"
    assert explicit_language_request("हिंदी में जवाब दो") == "hi"


def test_language_mentions_do_not_automatically_switch_state():
    assert explicit_language_request("मराठी और हिंदी भारत की भाषाएँ हैं") is None
    assert explicit_language_request("My transcript was detected as English") is None
