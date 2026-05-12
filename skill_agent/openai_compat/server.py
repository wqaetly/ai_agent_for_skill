"""
FastAPI app exposing OpenAI Chat Completions compatibility on port 2024.

Endpoints
---------
- `GET  /v1/models`            — list every Langflow flow as an OpenAI model.
- `POST /v1/chat/completions`  — forward to a Langflow flow, support
                                 `stream=true`, return errors in OpenAI
                                 envelope shape.
- `GET  /health`               — lightweight liveness probe used by the
                                 launch script.

Run locally:
    python -m skill_agent.openai_compat.server
or:
    uvicorn skill_agent.openai_compat.server:app --host 0.0.0.0 --port 2024
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import uuid
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, StreamingResponse

from .langflow_client import LangflowClient, LangflowHTTPError
from .schemas import (
    APIError,
    APIErrorResponse,
    ChatChoice,
    ChatChoiceMessage,
    ChatCompletionChunk,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ModelInfo,
    ModelsResponse,
    Usage,
)
from .stream_adapter import (
    langflow_event_to_chunks,
    make_chunk,
    role_priming_chunk,
    stop_chunk,
)

logger = logging.getLogger("skill_agent.openai_compat")


# ---------------------------------------------------------------------------
# Flow-id <-> OpenAI model-id table
# ---------------------------------------------------------------------------
# Lobe Chat sends the OpenAI model id we expose here verbatim. Each id maps
# to the Langflow flow name (the same string we Export the JSON file under
# in `langflow/flows/<flow>.flow.json` — Langflow accepts either id *or*
# name on `/api/v1/run/{flow_id_or_name}`).
MODEL_TO_FLOW: Dict[str, str] = {
    "skill-search": "skill_search",
    "skill-detail": "skill_detail",
    "skill-validation": "skill_validation",
    "parameter-inference": "parameter_inference",
    "skill-generation": "skill_generation",
    "progressive-skill-generation": "progressive_skill_generation",
    "action-batch-skill-generation": "action_batch_skill_generation",
    "smart": "smart_skill_generation",
}


# ---------------------------------------------------------------------------
# FastAPI app
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Skill Agent — OpenAI Compat Adapter",
    version="3.0.0",
    description=(
        "Translates OpenAI Chat Completions calls into Langflow Run API "
        "calls. Designed for Lobe Chat as the upstream client."
    ),
)


def _client() -> LangflowClient:
    return LangflowClient()


def _resolve_session_id(req: ChatCompletionRequest) -> Optional[str]:
    """Pull a stable session id from the request, falling back to user."""
    if req.metadata and isinstance(req.metadata, dict):
        sid = req.metadata.get("session_id")
        if isinstance(sid, str) and sid:
            return sid
    return req.user


def _error_json(message: str, status_code: int = 500, code: Optional[str] = None) -> JSONResponse:
    body = APIErrorResponse(error=APIError(message=message, code=code))
    return JSONResponse(status_code=status_code, content=body.model_dump(exclude_none=True))


def _log_request(extra: Dict[str, Any]) -> None:
    """Emit a single JSON log line. Avoids hard dependency on structlog so
    the adapter can boot even on a minimal Python install."""
    payload = {"ts": int(time.time()), **extra}
    try:
        logger.info(json.dumps(payload, ensure_ascii=False))
    except (TypeError, ValueError):
        logger.info(repr(payload))


# ---------------------------------------------------------------------------
# /v1/models
# ---------------------------------------------------------------------------

@app.get("/v1/models", response_model=ModelsResponse)
def list_models() -> ModelsResponse:
    return ModelsResponse(
        data=[ModelInfo(id=model_id) for model_id in MODEL_TO_FLOW.keys()]
    )


# ---------------------------------------------------------------------------
# /v1/chat/completions
# ---------------------------------------------------------------------------

@app.post("/v1/chat/completions")
async def chat_completions(request: Request) -> Any:
    request_id = f"req-{uuid.uuid4().hex[:12]}"
    try:
        raw = await request.json()
    except Exception as exc:  # noqa: BLE001
        return _error_json(f"Invalid JSON body: {exc}", status_code=400, code="invalid_json")

    try:
        req = ChatCompletionRequest.model_validate(raw)
    except Exception as exc:  # noqa: BLE001
        return _error_json(f"Invalid request: {exc}", status_code=400, code="invalid_request")

    flow_id = MODEL_TO_FLOW.get(req.model)
    if flow_id is None:
        return _error_json(
            f"Unknown model: {req.model!r}. Available: {sorted(MODEL_TO_FLOW)}",
            status_code=404,
            code="model_not_found",
        )

    requirement = req.last_user_text().strip()
    if not requirement:
        return _error_json("No user message provided.", status_code=400, code="empty_user_message")

    session_id = _resolve_session_id(req)
    started_at = time.perf_counter()
    _log_request({
        "event": "request_received",
        "request_id": request_id,
        "model": req.model,
        "flow_id": flow_id,
        "session_id": session_id,
        "stream": req.stream,
        "messages_count": len(req.messages),
    })

    if req.stream:
        return await _handle_streaming(
            request, req, flow_id, requirement, session_id, request_id, started_at
        )
    return await _handle_non_streaming(
        req, flow_id, requirement, session_id, request_id, started_at
    )


# ---------------------------------------------------------------------------
# Non-streaming path
# ---------------------------------------------------------------------------

async def _handle_non_streaming(
    req: ChatCompletionRequest,
    flow_id: str,
    requirement: str,
    session_id: Optional[str],
    request_id: str,
    started_at: float,
) -> Any:
    client = _client()
    try:
        raw_result = await client.run(flow_id, requirement, session_id=session_id)
    except LangflowHTTPError as exc:
        _log_request({
            "event": "langflow_http_error",
            "request_id": request_id,
            "status_code": exc.status_code,
            "url": exc.url,
            "body_preview": exc.text[:300],
        })
        return _error_json(
            f"Langflow returned {exc.status_code}.",
            status_code=502,
            code="langflow_upstream_error",
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Unhandled exception calling Langflow")
        return _error_json(
            f"Internal adapter error: {exc.__class__.__name__}",
            status_code=500,
            code="adapter_internal_error",
        )

    text_answer = _extract_text_from_run_result(raw_result)
    response = ChatCompletionResponse(
        model=req.model,
        choices=[
            ChatChoice(
                index=0,
                message=ChatChoiceMessage(role="assistant", content=text_answer),
                finish_reason="stop",
            )
        ],
        usage=Usage(),
    )
    _log_request({
        "event": "request_completed",
        "request_id": request_id,
        "total_latency_ms": int((time.perf_counter() - started_at) * 1000),
        "answer_chars": len(text_answer or ""),
    })
    return JSONResponse(content=response.model_dump(exclude_none=True))


def _extract_text_from_run_result(raw: Dict[str, Any]) -> str:
    """
    Walk the Langflow `/api/v1/run` response and pull out the assistant text.

    Langflow wraps results as `outputs[*].outputs[*].results.message.text`,
    but builds vary; we descend defensively and degrade to JSON dump if the
    expected shape is missing.
    """
    try:
        outputs = raw.get("outputs", []) or []
        for outer in outputs:
            inner_list = (outer or {}).get("outputs", []) or []
            for inner in inner_list:
                results = (inner or {}).get("results") or {}
                msg = results.get("message") or {}
                text = msg.get("text")
                if isinstance(text, str) and text:
                    return text
                if isinstance(msg, dict):
                    inner_text = msg.get("data", {}).get("text") if isinstance(msg.get("data"), dict) else None
                    if isinstance(inner_text, str) and inner_text:
                        return inner_text
    except Exception:  # noqa: BLE001
        pass
    return json.dumps(raw, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Streaming path
# ---------------------------------------------------------------------------

async def _handle_streaming(
    request: Request,
    req: ChatCompletionRequest,
    flow_id: str,
    requirement: str,
    session_id: Optional[str],
    request_id: str,
    started_at: float,
) -> StreamingResponse:
    chunk_id = f"chatcmpl-{uuid.uuid4().hex}"
    model_id = req.model

    async def event_stream() -> AsyncIterator[bytes]:
        client = _client()
        first_byte_sent = False
        first_byte_latency_ms = -1
        disconnected = False

        async def emit(chunk: ChatCompletionChunk) -> bytes:
            nonlocal first_byte_sent, first_byte_latency_ms
            if not first_byte_sent:
                first_byte_sent = True
                first_byte_latency_ms = int((time.perf_counter() - started_at) * 1000)
            return f"data: {chunk.model_dump_json(exclude_none=True)}\n\n".encode("utf-8")

        try:
            yield await emit(role_priming_chunk(chunk_id, model_id))

            async for event in client.stream(flow_id, requirement, session_id=session_id):
                if await request.is_disconnected():
                    disconnected = True
                    break
                for chunk in langflow_event_to_chunks(event, chunk_id, model_id):
                    yield await emit(chunk)

            if not disconnected:
                yield await emit(stop_chunk(chunk_id, model_id))
            yield b"data: [DONE]\n\n"

        except LangflowHTTPError as exc:
            _log_request({
                "event": "stream_langflow_http_error",
                "request_id": request_id,
                "status_code": exc.status_code,
                "body_preview": exc.text[:300],
            })
            yield await emit(make_chunk(
                chunk_id, model_id,
                content=f"\n[error] Langflow returned {exc.status_code}.",
                finish_reason="error",
            ))
            yield b"data: [DONE]\n\n"
            return

        except asyncio.CancelledError:
            disconnected = True
            raise
        except Exception:  # noqa: BLE001
            logger.exception("Streaming pipeline crashed")
            yield await emit(make_chunk(
                chunk_id, model_id,
                content="\n[error] Internal adapter error during streaming.",
                finish_reason="error",
            ))
            yield b"data: [DONE]\n\n"
            return
        finally:
            _log_request({
                "event": "stream_completed",
                "request_id": request_id,
                "first_byte_latency_ms": first_byte_latency_ms,
                "total_latency_ms": int((time.perf_counter() - started_at) * 1000),
                "disconnected": disconnected,
            })

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok", "version": app.version}


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

def _main() -> None:
    import uvicorn
    host = os.environ.get("OPENAI_COMPAT_HOST", "0.0.0.0")
    port = int(os.environ.get("OPENAI_COMPAT_PORT", "2024"))
    uvicorn.run("skill_agent.openai_compat.server:app", host=host, port=port, reload=False)


if __name__ == "__main__":
    _main()
