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


def test_filter_speaks_hindi_money_in_indian_units():
    text_filter = PersonaSpeechFilter(lambda: "arya", "test", lambda: "hi")

    async def run():
        return await text_filter.filter("₹6,000 की मदद और 200000 रुपये की सहायता।")

    assert asyncio.run(run()) == "छह हजार रुपये की मदद और दो लाख रुपये की सहायता।"


def test_filter_speaks_hindi_helplines_digit_by_digit():
    text_filter = PersonaSpeechFilter(lambda: "vidya", "test", lambda: "hi")

    async def run():
        return await text_filter.filter("हेल्पलाइन 14555 और किसान नंबर 1800-180-1551 है।")

    assert asyncio.run(run()) == "हेल्पलाइन एक चार पाँच पाँच पाँच और किसान नंबर एक आठ शून्य शून्य एक आठ शून्य एक पाँच पाँच एक है।"
