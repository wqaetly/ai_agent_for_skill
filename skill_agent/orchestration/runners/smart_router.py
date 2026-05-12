"""
Framework-agnostic smart router.

Re-exports the classification helpers from
`skill_agent.orchestration.smart_router` (which were already pure Python —
they never touched LangGraph) and adds two helpers that map the legacy
graph ids to the runner names exposed through this package's public API.

Two-layer routing
-----------------
- `smart_route(text)` returns the legacy "graph id" string (e.g.
  `"progressive-skill-generation"`, `"skill-search"`, ...).
- `route_to_runner_name(text)` returns the canonical OpenAI model id used
  by the OpenAI compat adapter and Langflow flow files. The two coincide
  for everything except `skill-detail` (which the legacy router never
  classified directly).

The runner-name aliases double as the OpenAI `model` field in
`/v1/chat/completions` requests.
"""

from typing import Callable, Dict

from ..smart_router import (
    smart_route,
    analyze_complexity,
    route_by_keywords,
    get_available_graphs,
    GRAPH_SKILL_GENERATION,
    GRAPH_PROGRESSIVE,
    GRAPH_ACTION_BATCH,
    GRAPH_SKILL_SEARCH,
    GRAPH_SKILL_DETAIL,
)

# Canonical OpenAI model ids exposed by the compat adapter and Langflow flows.
RUNNER_SKILL_GENERATION = "skill-generation"
RUNNER_PROGRESSIVE = "progressive-skill-generation"
RUNNER_ACTION_BATCH = "action-batch-skill-generation"
RUNNER_SKILL_SEARCH = "skill-search"
RUNNER_SKILL_DETAIL = "skill-detail"
RUNNER_SKILL_VALIDATION = "skill-validation"
RUNNER_PARAMETER_INFERENCE = "parameter-inference"
RUNNER_SMART = "smart"

# Legacy-graph-id -> runner-name. Every legacy id from `smart_router.py`
# already matches its target runner name 1:1, but we keep the indirection
# explicit so future renames are obvious.
_LEGACY_TO_RUNNER = {
    GRAPH_SKILL_GENERATION: RUNNER_SKILL_GENERATION,
    GRAPH_PROGRESSIVE: RUNNER_PROGRESSIVE,
    GRAPH_ACTION_BATCH: RUNNER_ACTION_BATCH,
    GRAPH_SKILL_SEARCH: RUNNER_SKILL_SEARCH,
    GRAPH_SKILL_DETAIL: RUNNER_SKILL_DETAIL,
}


def route_to_runner_name(user_input: str, prefer_progressive: bool = True) -> str:
    """
    Decide which runner should handle `user_input`.

    Args:
        user_input: Raw user requirement text.
        prefer_progressive: Forwarded to `smart_route` — see its docstring.

    Returns:
        One of the `RUNNER_*` constants (always a valid runner name).
    """
    decision = smart_route(user_input, prefer_progressive=prefer_progressive)
    legacy_id = decision["graph_id"]
    return _LEGACY_TO_RUNNER.get(legacy_id, RUNNER_SKILL_GENERATION)


# Late-bound name -> runner mapping. Filled in lazily by `_register` to
# avoid circular imports (each runner module imports from this one only via
# `runners/__init__.py`).
RUNNER_NAME_TO_RUN: Dict[str, Callable] = {}
RUNNER_NAME_TO_STREAM: Dict[str, Callable] = {}


def _register() -> None:
    """Populate the runner-name dispatch tables; called once on package import."""
    from .skill_generation import run_skill_generation, stream_skill_generation
    from .progressive_skill_generation import (
        run_progressive_skill_generation,
        stream_progressive_skill_generation,
    )
    from .action_batch_skill_generation import (
        run_action_batch_skill_generation,
        stream_action_batch_skill_generation,
    )
    from .skill_search import run_skill_search, stream_skill_search
    from .skill_detail import run_skill_detail, stream_skill_detail
    from .skill_validation import run_skill_validation, stream_skill_validation
    from .parameter_inference import (
        run_parameter_inference,
        stream_parameter_inference,
    )

    RUNNER_NAME_TO_RUN.update({
        RUNNER_SKILL_GENERATION: run_skill_generation,
        RUNNER_PROGRESSIVE: run_progressive_skill_generation,
        RUNNER_ACTION_BATCH: run_action_batch_skill_generation,
        RUNNER_SKILL_SEARCH: run_skill_search,
        RUNNER_SKILL_DETAIL: run_skill_detail,
        RUNNER_SKILL_VALIDATION: run_skill_validation,
        RUNNER_PARAMETER_INFERENCE: run_parameter_inference,
    })
    RUNNER_NAME_TO_STREAM.update({
        RUNNER_SKILL_GENERATION: stream_skill_generation,
        RUNNER_PROGRESSIVE: stream_progressive_skill_generation,
        RUNNER_ACTION_BATCH: stream_action_batch_skill_generation,
        RUNNER_SKILL_SEARCH: stream_skill_search,
        RUNNER_SKILL_DETAIL: stream_skill_detail,
        RUNNER_SKILL_VALIDATION: stream_skill_validation,
        RUNNER_PARAMETER_INFERENCE: stream_parameter_inference,
    })


_register()


__all__ = [
    "smart_route",
    "analyze_complexity",
    "route_by_keywords",
    "get_available_graphs",
    "route_to_runner_name",
    "RUNNER_NAME_TO_RUN",
    "RUNNER_NAME_TO_STREAM",
    "RUNNER_SKILL_GENERATION",
    "RUNNER_PROGRESSIVE",
    "RUNNER_ACTION_BATCH",
    "RUNNER_SKILL_SEARCH",
    "RUNNER_SKILL_DETAIL",
    "RUNNER_SKILL_VALIDATION",
    "RUNNER_PARAMETER_INFERENCE",
    "RUNNER_SMART",
]
