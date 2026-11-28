from agent import gemini


class FakeResponse:
    def __init__(self, status, payload=None):
        self.status_code = status
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_falls_back_to_next_model_and_sends_key_in_header(monkeypatch):
    calls = []

    def fake_post(url, json, headers, timeout):
        calls.append((url, headers))
        if "model-a" in url:
            return FakeResponse(429)
        return FakeResponse(200, {"candidates": [{"content": {"parts": [{"text": "hello"}]}}]})

    monkeypatch.setattr(gemini.requests, "post", fake_post)
    assert gemini.generate("hi", "SECRET", models=["model-a", "model-b"]) == "hello"
    assert len(calls) == 2
    for url, headers in calls:
        assert "SECRET" not in url
        assert headers["x-goog-api-key"] == "SECRET"


def test_returns_none_when_everything_fails(monkeypatch):
    monkeypatch.setattr(gemini.requests, "post", lambda *a, **k: FakeResponse(503))
    assert gemini.generate("hi", "k", models=["x", "y"]) is None
