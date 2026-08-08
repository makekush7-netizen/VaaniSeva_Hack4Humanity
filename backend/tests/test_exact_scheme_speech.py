import asyncio
from types import SimpleNamespace

from vaaniseva_rt.knowledge import KnowledgeService, create_mcp_server
from vaaniseva_rt.memory import SafeMemoryStore
from vaaniseva_rt.tools import build_llm_tools, exact_scheme_spoken_response, mandi_spoken_response


def _payload(name: str) -> dict:
    return {
        "ok": True,
        "retrieval": "exact-curated-scheme",
        "records": [{"name": name}],
    }


def test_pm_kisan_demo_answer_is_complete_and_natural_in_hindi():
    speech = exact_scheme_spoken_response(_payload("PM-KISAN Samman Nidhi"), "hi")

    assert speech is not None
    assert "छह हज़ार रुपये" in speech
    assert "₹" not in speech
    assert "Samman" not in speech
    assert "पात्रता, पंजीकरण या किस्त की स्थिति" in speech


def test_each_demo_scheme_has_application_owned_speech_in_every_supported_language():
    for name in (
        "PM-KISAN Samman Nidhi",
        "Pradhan Mantri Awas Yojana",
        "Pradhan Mantri MUDRA Yojana",
    ):
        for language in ("hi", "mr", "ta", "en"):
            assert exact_scheme_spoken_response(_payload(name), language)


def test_semantic_and_unknown_records_still_use_the_llm_composer():
    assert exact_scheme_spoken_response({"retrieval": "semantic-vector-rag", "records": []}, "hi") is None
    assert exact_scheme_spoken_response(_payload("Unknown scheme"), "hi") is None


def test_exact_scheme_tool_speaks_once_without_a_second_llm_pass(tmp_path):
    callbacks = []
    frames = []

    async def result_callback(payload, properties=None):
        callbacks.append((payload, properties))

    class Worker:
        async def queue_frames(self, queued):
            frames.extend(queued)

    params = SimpleNamespace(result_callback=result_callback, pipeline_worker=Worker())
    tools = build_llm_tools(
        create_mcp_server(KnowledgeService()),
        SafeMemoryStore(tmp_path / "memory.json", "test-salt"),
        "",
    )
    scheme_tool = next(tool for tool in tools if tool.__name__ == "search_government_schemes")

    asyncio.run(scheme_tool(params, "PM किसान योजना"))

    assert len(callbacks) == 1
    assert callbacks[0][0]["spoken_by_application"] is True
    assert callbacks[0][1].run_llm is False
    assert len(frames) == 1
    assert "छह हज़ार रुपये" in frames[0].text


def test_hindi_mandi_answer_is_application_owned_and_has_natural_numbers():
    speech = mandi_spoken_response(
        {"ok": True, "records": [{"district": "Dhar", "modal_price": "2675"}, {"district": "Dewas", "modal_price": "2500"}]},
        "hi", "गेहूँ", "मध्य प्रदेश",
    )

    assert speech is not None
    assert "दो हज़ार छह सौ पचहत्तर" in speech
    assert "**" not in speech
