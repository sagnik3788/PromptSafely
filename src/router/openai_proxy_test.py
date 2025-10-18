import pytest
import respx
import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.router.openai_proxy import router, UPSTREAM_URL, ChatRequest


@pytest.fixture
def app():
    app = FastAPI()
    app.include_router(router)
    return app


@pytest.fixture
def client(app):
    return TestClient(app)


def valid_payload():
    return {"model": "gpt", "messages": [{"role": "user", "content": "hello"}]}


@respx.mock
def test_successful_forwarding(client, monkeypatch):

    monkeypatch.setattr(ChatRequest, "model_validate_json", lambda body: None)
    upstream_response = {"id": "resp1", "object": "chat.completion", "choices": []}
    # route call the url
    route = respx.post(UPSTREAM_URL).mock(
        return_value=httpx.Response(200, json=upstream_response)
    )
    # resp proxy via app
    resp = client.post("/chat/completions", json=valid_payload())

    if resp.status_code != 200:
        raise AssertionError(f"expected status 200, got {resp.status_code}")
    if resp.json() != upstream_response:
        raise AssertionError("upstream response did not match")
    if not route.called:
        raise AssertionError("upstream route was not called")
    if route.call_count != 1:
        raise AssertionError(f"expected 1 upstream call, got {route.call_count}")

    sent_headers = route.calls[0].request.headers
    if not any(k.lower() == "x-request-id" for k in sent_headers):
        raise AssertionError("x-request-id header not forwarded to upstream")
