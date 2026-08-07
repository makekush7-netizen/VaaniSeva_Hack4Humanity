from pipecat.transcriptions.language import Language

from vaaniseva_rt.language_router import language_code


def test_stt_language_is_used_as_authoritative_turn_state():
    assert language_code(Language.MR_IN, "मला माहिती द्या") == "mr"
    assert language_code(Language.TA_IN, "தகவல் சொல்லுங்கள்") == "ta"


def test_explicit_language_request_overrides_stt_guess():
    assert language_code(Language.HI_IN, "पीएम आवास मराठीत सांगा") == "mr"
    assert language_code(Language.HI_IN, "Please answer in English") == "en"
