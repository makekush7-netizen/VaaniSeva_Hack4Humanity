import asyncio
from io import BytesIO
from unittest.mock import Mock, patch

from vaaniseva_rt.knowledge import LegacyVectorRAG, KnowledgeService, create_mcp_server, tool_payload


def test_legacy_vector_rag_loads_embeddings_from_dynamodb_projection():
    table = Mock()
    table.scan.return_value = {"Items": [{"embedding_id": "chunk-1", "embedding": [0.1, 0.2]}]}
    resource = Mock()
    resource.Table.return_value = table

    with patch("vaaniseva_rt.knowledge.boto3.resource", return_value=resource):
        records = LegacyVectorRAG("us-east-1", "vaaniseva-vectors", "model")._load_items()

    assert records[0]["embedding"] == [0.1, 0.2]
    projection = table.scan.call_args.kwargs["ProjectionExpression"]
    assert "embedding" in projection.split(", ")


def test_legacy_vector_rag_never_returns_marathi_for_a_hindi_query():
    rag = LegacyVectorRAG("us-east-1", "vaaniseva-vectors", "model")
    rag._items = [
        {"scheme_id": "pmay", "section_id": "mr", "language": "mr", "embedding": [1.0, 0.0], "text": "Marathi guidance"},
        {"scheme_id": "pmay", "section_id": "hi", "language": "hi", "embedding": [0.9, 0.1], "text_hi": "Hindi guidance"},
    ]
    rag._expires_at = float("inf")
    client = Mock()
    client.invoke_model.return_value = {"body": BytesIO(b'{"embedding": [1.0, 0.0]}')}

    with patch("vaaniseva_rt.knowledge.boto3.client", return_value=client):
        records = rag.search("PM Awas", language="hi")

    assert [record["text"] for record in records] == ["Hindi guidance"]


def test_scheme_result_has_source_and_freshness():
    result = asyncio.run(KnowledgeService().search_schemes("farmer crop"))
    assert result["ok"] is True
    assert result["source"]
    assert result["checked_at"]
    assert any("farmer" in item["helps"] for item in result["records"])


def test_broad_scheme_search_prefers_legacy_vector_rag(monkeypatch):
    service = KnowledgeService()
    monkeypatch.setattr(
        service._legacy_rag,
        "search",
        lambda query, language: [{"scheme_id": "pm-kisan", "section_id": "overview", "text": "verified", "similarity": 0.91}],
    )
    result = asyncio.run(service.search_schemes("income support for a landholding farmer"))
    assert result["retrieval"] == "semantic-vector-rag"
    assert "Titan" in result["source"]


def test_explicit_language_selects_the_matching_semantic_partition(monkeypatch):
    service = KnowledgeService()
    seen = {}

    def search(query, language):
        seen["language"] = language
        return [{"scheme_id": "pmay", "section_id": "overview", "text": "मराठी", "similarity": 0.9}]

    monkeypatch.setattr(service._legacy_rag, "search", search)
    result = asyncio.run(service.search_schemes("घरासाठी मदत", language="mr"))

    assert seen["language"] == "mr"
    assert result["retrieval"] == "semantic-vector-rag"


def test_exact_named_scheme_skips_slow_semantic_lookup(monkeypatch):
    service = KnowledgeService()
    semantic = Mock(side_effect=AssertionError("exact scheme should not invoke vector RAG"))
    monkeypatch.setattr(service._legacy_rag, "search", semantic)

    result = asyncio.run(service.search_schemes("मुझे PM Kisan योजना के बारे में बताओ"))

    assert result["retrieval"] == "exact-curated-scheme"
    assert result["records"][0]["name"] == "PM-KISAN Samman Nidhi"
    assert "conversation_guidance" in result["records"][0]
    semantic.assert_not_called()


def test_pm_awas_and_mudra_names_have_exact_curated_answers():
    service = KnowledgeService()
    awas = asyncio.run(service.search_schemes("PM Awas Yojana"))
    mudra = asyncio.run(service.search_schemes("PM Mudra Yojana"))
    misheard_mudra = asyncio.run(service.search_schemes("योग मुद्रा योजना क्या है"))

    assert awas["retrieval"] == "exact-curated-scheme"
    assert "rural or urban" in awas["records"][0]["conversation_guidance"]
    assert mudra["retrieval"] == "exact-curated-scheme"
    assert "credit" in mudra["records"][0]["conversation_guidance"]
    assert misheard_mudra["records"][0]["name"] == "Pradhan Mantri MUDRA Yojana"


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


def test_generic_health_query_never_returns_covid_1075():
    result = asyncio.run(KnowledgeService().helpline("rashtriya swasthya helpline"))
    assert {record["number"] for record in result["records"]} == {"112", "14555"}
    assert all(record["number"] != "1075" for record in result["records"])


def test_pmjay_helpline_is_scoped_to_14555():
    result = asyncio.run(KnowledgeService().helpline("Ayushman Bharat PM-JAY"))
    assert result["records"][0]["number"] == "14555"


def test_mandi_never_invents_without_api_key():
    result = asyncio.run(KnowledgeService("").mandi_price("Wheat", "Maharashtra"))
    assert result["ok"] is False
    assert result["records"] == []
    assert "no price" in result["warning"].lower()


def test_urgent_health_escalates_to_112():
    result = asyncio.run(KnowledgeService().health_information("severe chest pain and cannot breathe"))
    assert result["records"][0]["urgent"] is True
    assert "112" in result["records"][0]["advice"]
