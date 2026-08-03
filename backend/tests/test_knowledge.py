import asyncio

from vaaniseva_rt.knowledge import KnowledgeService, create_mcp_server, tool_payload


def test_scheme_result_has_source_and_freshness():
    result = asyncio.run(KnowledgeService().search_schemes("farmer crop"))
    assert result["ok"] is True
    assert result["source"]
    assert result["checked_at"]
    assert any("farmer" in item["helps"] for item in result["records"])


def test_scheme_search_prefers_legacy_vector_rag(monkeypatch):
    service = KnowledgeService()
    monkeypatch.setattr(
        service._legacy_rag,
        "search",
        lambda query, language: [{"scheme_id": "pm-kisan", "section_id": "overview", "text": "verified", "similarity": 0.91}],
    )
    result = asyncio.run(service.search_schemes("PM Kisan"))
    assert result["retrieval"] == "semantic-vector-rag"
    assert "Titan" in result["source"]


def test_mcp_server_calls_real_registered_tool():
    server = create_mcp_server(KnowledgeService())
    result = asyncio.run(server.call_tool("get_verified_helpline", {"topic": "farmer"}))
    payload = tool_payload(result)
    assert payload["ok"] is True
    assert payload["records"][0]["number"] == "1800-180-1551"
    assert payload["source"].startswith("https://")


def test_agriculture_helpline_never_falls_back_to_health():
    for topic in ("agriculture", "farming support", "kisan", "खेती"):
        result = asyncio.run(KnowledgeService().helpline(topic))
        assert result["records"][0]["number"] == "1800-180-1551"


def test_mandi_never_invents_without_api_key():
    result = asyncio.run(KnowledgeService("").mandi_price("Wheat", "Maharashtra"))
    assert result["ok"] is False
    assert result["records"] == []
    assert "no price" in result["warning"].lower()


def test_urgent_health_escalates_to_112():
    result = asyncio.run(KnowledgeService().health_information("severe chest pain and cannot breathe"))
    assert result["records"][0]["urgent"] is True
    assert "112" in result["records"][0]["advice"]
