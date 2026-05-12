"""
Thin async client over Langflow's `POST /api/v1/run/{flow_id_or_name}`.

Responsibilities
----------------
- Build the `SimplifiedAPIRequest` body expected by Langflow.
- Forward `stream=true` requests as an async generator yielding the raw
  Langflow events (`add_message`, `token`, `end`, ...).
- Surface non-streaming responses as a plain dict.
- Cooperate with caller-provided cancellation: when the caller's task is
  cancelled (or the inbound HTTP request is disconnected) the underlying
  `httpx` connection is closed promptly.

This module **only** speaks to Langflow. OpenAI-shape translation lives in
`stream_adapter.py`.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, AsyncIterator, Dict, Optional

import httpx

logger = logging.getLogger(__name__)


def get_langflow_base_url() -> str:
    """Resolve the Langflow base URL from the environment, with a sane default."""
    return os.environ.get("LANGFLOW_BASE_URL", "http://localhost:7860").rstrip("/")


def _build_payload(
    requirement: str,
    session_id: Optional[str],
    extra_tweaks: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    body: Dict[str, Any] = {
        "input_value": requirement,
        "input_type": "chat",
        "output_type": "chat",
    }
    if session_id:
        body["session_id"] = session_id
    if extra_tweaks:
        body["tweaks"] = extra_tweaks
    return body


def _build_headers() -> Dict[str, str]:
    """Add the Langflow API key header when one is configured."""
    headers: Dict[str, str] = {"Content-Type": "application/json"}
    api_key = os.environ.get("LANGFLOW_API_KEY")
    if api_key:
        # Langflow accepts both header names; sending both is a no-op.
        headers["x-api-key"] = api_key
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


class LangflowClient:
    """Async client for a specific Langflow instance."""

    def __init__(self, base_url: Optional[str] = None, request_timeout: float = 600.0):
        self.base_url = (base_url or get_langflow_base_url()).rstrip("/")
        self.request_timeout = request_timeout

    # ------------------------------------------------------------------
    # Non-streaming
    # ------------------------------------------------------------------

    async def run(
        self,
        flow_id: str,
        requirement: str,
        session_id: Optional[str] = None,
        extra_tweaks: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a flow and return the parsed JSON response."""
        url = f"{self.base_url}/api/v1/run/{flow_id}"
        body = _build_payload(requirement, session_id, extra_tweaks)
        async with httpx.AsyncClient(timeout=self.request_timeout) as client:
            resp = await client.post(url, json=body, headers=_build_headers())
            if resp.status_code >= 400:
                logger.warning(
                    "Langflow non-2xx status=%s url=%s body=%s",
                    resp.status_code, url, resp.text[:500],
                )
                raise LangflowHTTPError(
                    status_code=resp.status_code, text=resp.text, url=url
                )
            return resp.json()

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    async def stream(
        self,
        flow_id: str,
        requirement: str,
        session_id: Optional[str] = None,
        extra_tweaks: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Async-iterate the SSE events produced by Langflow's run endpoint.

        Each yielded value has the shape::

            {"event": "<event_type>", "data": <parsed_json_or_raw_string>}

        The caller is responsible for translating these into OpenAI chunks.
        Fork's `feat：优化flow dump功能` keeps the upstream SSE schema
        intact, so this loop stays compatible with both upstream Langflow
        and the wqaetly fork.
        """
        url = f"{self.base_url}/api/v1/run/{flow_id}?stream=true"
        body = _build_payload(requirement, session_id, extra_tweaks)
        headers = _build_headers()
        # SSE clients should announce they accept event-stream so that the
        # server doesn't fall back to chunked JSON.
        headers["Accept"] = "text/event-stream"

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=body, headers=headers) as resp:
                if resp.status_code >= 400:
                    text = (await resp.aread()).decode("utf-8", errors="replace")
                    logger.warning(
                        "Langflow streaming non-2xx status=%s url=%s body=%s",
                        resp.status_code, url, text[:500],
                    )
                    raise LangflowHTTPError(
                        status_code=resp.status_code, text=text, url=url
                    )

                pending_event: Optional[str] = None
                pending_data_lines: list[str] = []

                async for raw_line in resp.aiter_lines():
                    line = raw_line.rstrip("\r")
                    if line == "":
                        # Blank line — flush the buffered event.
                        if pending_event or pending_data_lines:
                            data_str = "\n".join(pending_data_lines)
                            yield _parse_sse_event(pending_event, data_str)
                        pending_event = None
                        pending_data_lines = []
                        continue
                    if line.startswith(":"):
                        # SSE comment, ignore.
                        continue
                    if line.startswith("event:"):
                        pending_event = line[len("event:"):].strip()
                    elif line.startswith("data:"):
                        pending_data_lines.append(line[len("data:"):].lstrip())
                    elif line.startswith("{") and pending_event is None:
                        # Some Langflow builds ship JSON-lines without the
                        # `data:` prefix; treat them as `data` events.
                        pending_data_lines.append(line)

                # Flush any trailing event without the final blank line.
                if pending_event or pending_data_lines:
                    data_str = "\n".join(pending_data_lines)
                    yield _parse_sse_event(pending_event, data_str)


def _parse_sse_event(event_name: Optional[str], data_str: str) -> Dict[str, Any]:
    """Decode an SSE frame into `{"event": str, "data": Any}`."""
    payload: Any
    if not data_str:
        payload = None
    else:
        try:
            payload = json.loads(data_str)
        except (ValueError, TypeError):
            payload = data_str
    return {"event": event_name or "message", "data": payload}


class LangflowHTTPError(Exception):
    """Raised when Langflow responds with a non-2xx status."""

    def __init__(self, status_code: int, text: str, url: str):
        super().__init__(f"Langflow {status_code} from {url}: {text[:200]}")
        self.status_code = status_code
        self.text = text
        self.url = url
