from fastapi.testclient import TestClient

from twilio.request_validator import RequestValidator

from vaaniseva_rt.server import _stream_twiml, _valid_twilio_signature, app


def test_health_reports_only_variable_names():
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "vaaniseva-realtime"
    assert set(body) == {"status", "service", "version", "missing_configuration"}


def test_callback_is_disabled_by_default(monkeypatch):
    monkeypatch.setenv("CALLBACK_ENABLED", "false")
    response = TestClient(app).post("/api/calls/callback", json={"phone_number": "+919876543210"})
    assert response.status_code == 503
    assert response.json()["detail"] == "Callback demo is disabled"


def test_twiml_uses_bidirectional_connect_stream(monkeypatch):
    monkeypatch.delenv("PUBLIC_BASE_URL", raising=False)
    response = TestClient(app).post("/twiml", data={"From": "+919876543210", "To": "+911234567890"})
    assert response.status_code == 200
    xml = response.text
    assert "<Connect>" in xml
    assert "<Stream" in xml
    assert "ws://testserver/ws" in xml
    assert 'name="from_number"' in xml


def test_inline_callback_twiml_points_directly_to_production_stream():
    xml = _stream_twiml(
        "https://voice.example.org",
        "+919876543210",
        "+16293173435",
    )
    assert 'url="wss://voice.example.org/ws"' in xml
    assert 'name="from_number" value="+919876543210"' in xml
    assert 'name="to_number" value="+16293173435"' in xml


def test_twilio_websocket_signature_accepts_documented_trailing_slash_variant():
    token = "test-token"
    url = "wss://voice.example.org/ws"
    signature = RequestValidator(token).compute_signature(f"{url}/", {})

    assert _valid_twilio_signature(url, {}, signature, token)
    assert not _valid_twilio_signature(url, {}, "wrong", token)


def test_twiml_signature_accepts_https_public_url_when_app_sees_http_proxy_url():
    token = "test-token"
    public_url = "https://voice.example.org/twiml"
    proxy_seen_url = "http://voice:7860/twiml"
    params = {"From": "+919876543210", "To": "+911234567890"}
    signature = RequestValidator(token).compute_signature(public_url, params)

    assert _valid_twilio_signature([public_url, proxy_seen_url], params, signature, token)
