import asyncio

from vaaniseva_rt.text_filters import PersonaSpeechFilter, SuppressThinkingFilter


def test_thinking_filter_handles_streamed_tag_fragments():
    text_filter = SuppressThinkingFilter()

    async def run():
        chunks = ["Hello ", "<thi", "nking>private plan", "</think", "ing>नमस्ते"]
        return "".join([await text_filter.filter(chunk) for chunk in chunks])

    assert asyncio.run(run()) == "Hello नमस्ते"


def test_hitesh_filter_repairs_first_person_feminine_forms():
    text_filter = PersonaSpeechFilter(lambda: "hitesh", "test")

    async def run():
        return await text_filter.filter("मैं मदद कर सकती हूँ। मैं जानकारी देख रही हूँ।")

    assert asyncio.run(run()) == "मैं मदद कर सकता हूँ। मैं जानकारी देख रहा हूँ।"


def test_female_filter_repairs_first_person_masculine_forms():
    text_filter = PersonaSpeechFilter(lambda: "arya", "test")

    async def run():
        return await text_filter.filter("मैं मदद कर सकता हूँ। मैं बता रहा हूँ।")

    assert asyncio.run(run()) == "मैं मदद कर सकती हूँ। मैं बता रही हूँ।"


def test_filter_normalizes_pm_kisan_for_tts_pronunciation():
    text_filter = PersonaSpeechFilter(lambda: "hitesh", "test")

    async def run():
        return await text_filter.filter("PM-KISAN योजना में मदद कर सकती हूँ।")

    assert asyncio.run(run()) == "पी एम किसान योजना में मदद कर सकता हूँ।"


def test_filter_makes_pm_kisan_verified_benefit_fully_hindi_for_tts():
    text_filter = PersonaSpeechFilter(lambda: "arya", "test")

    async def run():
        return await text_filter.filter("पी एम किसान Samman Nidhi योजना योग्य परिवारों को ₹6,000 प्रति वर्ष देती है।")

    assert asyncio.run(run()) == "पी एम किसान सम्मान निधि योजना योग्य परिवारों को हर साल छह हज़ार रुपये देती है।"


def test_filter_normalizes_pm_awas_and_mudra_for_tts_pronunciation():
    text_filter = PersonaSpeechFilter(lambda: "arya", "test")

    async def run():
        return await text_filter.filter("PM आवास योजना और PM मुद्रा योजना")

    assert asyncio.run(run()) == "पी एम आवास योजना और पी एम मुद्रा योजना"


def test_filter_uses_the_active_language_for_pm_pronunciation():
    text_filter = PersonaSpeechFilter(lambda: "arya", "test", lambda: "en")

    async def run():
        return await text_filter.filter("PM-KISAN, PM Awas, and PM Mudra")

    assert asyncio.run(run()) == "P M Kisan, P M Awas, and P M Mudra"


def test_filter_normalizes_brand_for_tts_pronunciation():
    text_filter = PersonaSpeechFilter(lambda: "arya", "test")

    async def run():
        return await text_filter.filter("आप VaaniSeva से बात कर रहे हैं।")

    assert asyncio.run(run()) == "आप वाणी सेवा से बात कर रहे हैं।"


def test_filter_does_not_rewrite_natural_hindi():
    text_filter = PersonaSpeechFilter(lambda: "arya", "test")

    async def run():
        return await text_filter.filter("लाइव जानकारी अभी उपलब्ध नहीं है। कृपया पुनः प्रयास करें।")

    assert asyncio.run(run()) == "लाइव जानकारी अभी उपलब्ध नहीं है। कृपया पुनः प्रयास करें।"
