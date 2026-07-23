def test_health_reports_unconfigured_without_a_key(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["vision"] == "unconfigured"
    assert body["analysis_model"] == "stub"


def test_health_reports_configured_with_a_key(client, monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["vision"] == "configured"
    assert body["analysis_model"] != "stub"
