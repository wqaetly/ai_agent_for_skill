"""
Unit tests for the OpenAI Chat Completions compat adapter.

These tests exercise:
  1. /v1/models returns the expected 8 models.
  2. POST /v1/chat/completions (non-streaming) succeeds when the patched
     LangflowClient returns a known shape.
  3. POST /v1/chat/completions (streaming) emits a role-priming chunk,
     forwards token + add_message events into delta.content /
     delta.reasoning_content, and terminates with `[DONE]`.
  4. When LangflowClient raises `LangflowHTTPError`, the non-streaming
     path returns the OpenAI standard error envelope.

The Langflow upstream is fully patched out — no network calls happen.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Conftest only injects `skill_agent/` onto sys.path; we also need the repo
# root so `from skill_agent.openai_compat...` resolves.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))

from skill_agent.openai_compat import server as server_module  # noqa: E402
from skill_agent.openai_compat.langflow_client import LangflowHTTPError  # noqa: E402


@pytest.fixture
def client():
    return TestClient(server_module.app)


# ---------------------------------------------------------------------------
# /v1/models
# ---------------------------------------------------------------------------

def test_models_endpoint_returns_eight_models(client):
    resp = client.get("/v1/models")
    assert resp.status_code == 200
    body = resp.json()
    assert body["object"] == "list"
    ids = [m["id"] for m in body["data"]]
    assert set(ids) == {
        "skill-search",
        "skill-detail",
        "skill-validation",
        "parameter-inference",
        "skill-generation",
        "progressive-skill-generation",
        "action-batch-skill-generation",
        "smart",
    }


# ---------------------------------------------------------------------------
# Non-streaming
# ---------------------------------------------------------------------------

class _FakeClientOK:
    async def run(self, flow_id, requirement, session_id=None, extra_tweaks=None):
        return {
            "outputs": [
                {
                    "outputs": [
                        {
                            "results": {
                                "message": {"text": f"OK from {flow_id}: {requirement}"}
                            }
                        }
                    ]
                }
            ]
        }


def test_chat_completions_non_streaming(monkeypatch, client):
    monkeypatch.setattr(server_module, "_client", lambda: _FakeClientOK())

    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "skill-search",
            "messages": [{"role": "user", "content": "fireball"}],
            "stream": False,
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["object"] == "chat.completion"
    assert body["model"] == "skill-search"
    assert body["choices"][0]["message"]["content"].startswith("OK from skill_search:")


# ---------------------------------------------------------------------------
# Streaming
# ---------------------------------------------------------------------------

class _FakeClientStreaming:
    async def run(self, *a, **k):
        raise AssertionError("streaming test should not call .run()")

    async def stream(self, flow_id, requirement, session_id=None, extra_tweaks=None):
        yield {"event": "add_message",
               "data": {"category": "thinking", "text": "thinking step 1"}}
        yield {"event": "token", "data": {"chunk": "Hello "}}
        yield {"event": "token", "data": {"chunk": "world."}}
        yield {"event": "end", "data": {"result": ""}}


def test_chat_completions_streaming(monkeypatch, client):
    monkeypatch.setattr(server_module, "_client", lambda: _FakeClientStreaming())

    with client.stream(
        "POST",
        "/v1/chat/completions",
        json={
            "model": "progressive-skill-generation",
            "messages": [{"role": "user", "content": "build a fireball"}],
            "stream": True,
        },
    ) as resp:
        assert resp.status_code == 200
        body = b"".join(resp.iter_bytes()).decode("utf-8")

    assert "data: [DONE]" in body, body

    # Collect every parsed chunk JSON.
    chunks = []
    for raw in body.split("\n\n"):
        raw = raw.strip()
        if not raw or not raw.startswith("data: "):
            continue
        payload = raw[len("data: "):]
        if payload == "[DONE]":
            continue
        chunks.append(json.loads(payload))

    assert chunks, "expected at least one streamed chunk"
    # First chunk must announce the assistant role.
    assert chunks[0]["choices"][0]["delta"].get("role") == "assistant"

    # We expect at least one reasoning_content chunk and at least one content chunk.
    has_reasoning = any(
        c["choices"] and c["choices"][0]["delta"].get("reasoning_content")
        for c in chunks
    )
    has_content = any(
        c["choices"] and c["choices"][0]["delta"].get("content")
        for c in chunks
    )
    assert has_reasoning, "no reasoning_content chunk emitted"
    assert has_content, "no content chunk emitted"


# ---------------------------------------------------------------------------
# Error path
# ---------------------------------------------------------------------------

class _FakeClientBoom:
    async def run(self, *a, **k):
        raise LangflowHTTPError(status_code=503, text="upstream down", url="http://test/api/v1/run/x")

    async def stream(self, *a, **k):  # pragma: no cover — not exercised here
        raise LangflowHTTPError(status_code=503, text="upstream down", url="http://test/api/v1/run/x")


def test_chat_completions_translates_langflow_errors(monkeypatch, client):
    monkeypatch.setattr(server_module, "_client", lambda: _FakeClientBoom())

    resp = client.post(
        "/v1/chat/completions",
        json={
            "model": "skill-search",
            "messages": [{"role": "user", "content": "anything"}],
            "stream": False,
        },
    )
    # Adapter must surface Langflow upstream issues as 502 with OpenAI envelope.
    assert resp.status_code == 502
    body = resp.json()
    assert "error" in body
    assert body["error"]["code"] == "langflow_upstream_error"


def test_unknown_model_returns_404(client):
    resp = client.post(
        "/v1/chat/completions",
        json={"model": "definitely-not-a-flow", "messages": [{"role": "user", "content": "x"}]},
    )
    assert resp.status_code == 404
    body = resp.json()
    assert body["error"]["code"] == "model_not_found"


def test_empty_user_message_returns_400(monkeypatch, client):
    resp = client.post(
        "/v1/chat/completions",
        json={"model": "skill-search", "messages": [{"role": "system", "content": "system only"}]},
    )
    assert resp.status_code == 400
    body = resp.json()
    assert body["error"]["code"] == "empty_user_message"
