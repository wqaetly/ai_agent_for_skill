"""
Internal thin client: call Langflow flows directly from Python without
going through the OpenAI compat adapter on port 2024.

Why this exists
---------------
The Unity Editor's RPC server (port 8766) needs to invoke skill-generation
or parameter-inference logic for in-editor "smart suggestion" buttons.
Routing those calls through the OpenAI compat adapter would add an extra
HTTP hop *and* force the adapter to translate RPC shapes into chat
messages and back. Instead we keep that path local to Python: the RPC
server uses this helper to talk to Langflow's `POST /api/v1/run/{flow_id}`
directly and returns the raw flow result to Unity.

For features that don't need Langflow (pure RAG search, parameter
suggestions backed by the existing `core.enhanced_rag_engine`), the RPC
server should call the runners in
`skill_agent.orchestration.runners` directly — see `unity_rpc_runtime.py`.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, Optional

from skill_agent.openai_compat.langflow_client import (
    LangflowClient,
    LangflowHTTPError,
)

logger = logging.getLogger(__name__)


_FLOW_NAME_BY_RUNNER = {
    "skill-search": "skill_search",
    "skill-detail": "skill_detail",
    "skill-validation": "skill_validation",
    "parameter-inference": "parameter_inference",
    "skill-generation": "skill_generation",
    "progressive-skill-generation": "progressive_skill_generation",
    "action-batch-skill-generation": "action_batch_skill_generation",
    "smart": "smart_skill_generation",
}


async def call_flow(
    runner_name: str,
    requirement: str,
    session_id: Optional[str] = None,
    extra_tweaks: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Invoke a Langflow flow by its (OpenAI-style) runner name.

    Args:
        runner_name: One of the keys in `_FLOW_NAME_BY_RUNNER`.
        requirement: The natural-language input that the flow's
            `InputComponent` consumes.
        session_id: Optional stable session id (forwarded for log
            correlation).
        extra_tweaks: Optional Langflow `tweaks` dict; see Langflow docs.

    Returns:
        Parsed JSON response from Langflow's run API.

    Raises:
        ValueError: when `runner_name` is unknown.
        LangflowHTTPError: when Langflow returns a non-2xx status.
    """
    flow_name = _FLOW_NAME_BY_RUNNER.get(runner_name)
    if flow_name is None:
        raise ValueError(
            f"Unknown runner name: {runner_name!r}. "
            f"Available: {sorted(_FLOW_NAME_BY_RUNNER)}"
        )

    client = LangflowClient()
    try:
        return await client.run(
            flow_name, requirement, session_id=session_id, extra_tweaks=extra_tweaks
        )
    except LangflowHTTPError:
        # Re-raise so the RPC layer can format an OpenAI-spec-equivalent
        # JSON-RPC error.
        raise


def call_flow_sync(
    runner_name: str,
    requirement: str,
    session_id: Optional[str] = None,
    extra_tweaks: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Synchronous wrapper for callers that don't run an event loop."""
    return asyncio.run(
        call_flow(runner_name, requirement, session_id, extra_tweaks)
    )
