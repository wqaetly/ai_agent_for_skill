"""
Translate Langflow SSE events into OpenAI Chat Completions streaming chunks.

Mapping rules
-------------
- Langflow `token` events with a `chunk` (or `content`) string are
  forwarded as `delta.content` chunks.
- Langflow `add_message` events whose `category == "thinking"` (or
  whose source/component name is one of the *progress-style* runners)
  are forwarded as `delta.reasoning_content` chunks. Lobe Chat's latest
  release renders these inside a collapsible "thoughts" panel.
- Any other `add_message` content is forwarded as `delta.content`.
- The terminal `end` event finishes the stream with `finish_reason="stop"`.

The actual heavy lifting (serialising chunks to `data: ...\\n\\n`) lives
in the FastAPI layer; this module only produces `ChatCompletionChunk`
objects so it stays unit-testable without a network.
"""

from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterable, Optional

from .schemas import (
    ChatChunkChoice,
    ChatChunkDelta,
    ChatCompletionChunk,
)


# Component / source names whose textual events should be surfaced as
# reasoning rather than as the final assistant content.
_REASONING_SOURCES = {
    "ProgressiveGeneratorComponent",
    "ActionBatchGeneratorComponent",
    "SkillGenerationComponent",
    "SmartRouterComponent",
}


def _is_reasoning_message(payload: Dict[str, Any]) -> bool:
    """Decide whether a Langflow message should be wrapped as reasoning."""
    if not isinstance(payload, dict):
        return False
    category = str(payload.get("category", "")).lower()
    if category in {"thinking", "reasoning", "progress"}:
        return True
    sender_name = str(
        payload.get("sender_name") or payload.get("source") or ""
    )
    if sender_name in _REASONING_SOURCES:
        # If the message itself looks like a status update (no `properties.text`
        # the front-end would render as final), keep it as reasoning.
        return True
    properties = payload.get("properties") or {}
    if isinstance(properties, dict) and properties.get("background_color") == "info":
        return True
    return False


def _extract_text(payload: Any) -> str:
    """Pull the textual chunk out of an arbitrary Langflow event payload."""
    if isinstance(payload, str):
        return payload
    if not isinstance(payload, dict):
        return ""
    # Different Langflow versions / fork patches put the text in different
    # keys. We try the most common ones in priority order.
    for key in ("chunk", "content", "text", "message"):
        v = payload.get(key)
        if isinstance(v, str) and v:
            return v
        if isinstance(v, dict):
            inner = v.get("text") or v.get("content")
            if isinstance(inner, str) and inner:
                return inner
    # Final-result envelopes from `end` events:
    result = payload.get("result")
    if isinstance(result, dict):
        return _extract_text(result)
    return ""


def make_chunk(
    chunk_id: str,
    model: str,
    *,
    role: Optional[str] = None,
    content: Optional[str] = None,
    reasoning_content: Optional[str] = None,
    finish_reason: Optional[str] = None,
) -> ChatCompletionChunk:
    delta = ChatChunkDelta(
        role=role if role else None,
        content=content,
        reasoning_content=reasoning_content,
    )
    return ChatCompletionChunk(
        id=chunk_id,
        model=model,
        choices=[ChatChunkChoice(index=0, delta=delta, finish_reason=finish_reason)],
    )


def role_priming_chunk(chunk_id: str, model: str) -> ChatCompletionChunk:
    """The first chunk of every OpenAI stream announces the assistant role."""
    return make_chunk(chunk_id, model, role="assistant")


def stop_chunk(chunk_id: str, model: str) -> ChatCompletionChunk:
    """The terminal chunk every OpenAI stream emits before `[DONE]`."""
    return make_chunk(chunk_id, model, finish_reason="stop")


def langflow_event_to_chunks(
    event: Dict[str, Any], chunk_id: str, model: str
) -> Iterable[ChatCompletionChunk]:
    """
    Convert a single Langflow SSE event into 0..n OpenAI chunks.

    The function is a generator (Iterable) so that one Langflow event can
    expand into both a reasoning chunk and a content chunk if needed.
    """
    name = (event.get("event") or "").lower()
    payload = event.get("data") if isinstance(event, dict) else None

    if name == "token":
        text = _extract_text(payload)
        if text:
            if isinstance(payload, dict) and _is_reasoning_message(payload):
                yield make_chunk(chunk_id, model, reasoning_content=text)
            else:
                yield make_chunk(chunk_id, model, content=text)
        return

    if name == "add_message":
        text = _extract_text(payload)
        if not text:
            return
        if isinstance(payload, dict) and _is_reasoning_message(payload):
            yield make_chunk(chunk_id, model, reasoning_content=text)
        else:
            yield make_chunk(chunk_id, model, content=text)
        return

    if name == "end":
        text = _extract_text(payload)
        if text:
            yield make_chunk(chunk_id, model, content=text)
        return

    # Other events (e.g. `error`) are surfaced as a reasoning footnote so
    # the user sees *something* in the UI but the final assistant content
    # remains clean.
    text = _extract_text(payload)
    if text:
        yield make_chunk(chunk_id, model, reasoning_content=f"[{name}] {text}")


async def stream_langflow_to_openai(
    chunk_id: str,
    model: str,
    langflow_events: AsyncIterator[Dict[str, Any]],
) -> AsyncIterator[ChatCompletionChunk]:
    """
    Convenience helper: walk a Langflow event stream and yield OpenAI chunks
    starting with the role-priming chunk and terminating with the stop chunk.
    """
    yield role_priming_chunk(chunk_id, model)
    async for event in langflow_events:
        for chunk in langflow_event_to_chunks(event, chunk_id, model):
            yield chunk
    yield stop_chunk(chunk_id, model)
