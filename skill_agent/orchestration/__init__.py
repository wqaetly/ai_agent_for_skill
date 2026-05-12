"""
SkillRAG Orchestration Layer (v3.0 — Langflow + framework-agnostic runners)

This module used to wire LangGraph `StateGraph` instances; from v3.0 onward
the public surface is the `runners` package (pure Python while-loops that
internally reuse the existing `nodes/` functions) plus the legacy
`smart_router` helpers and `tools.rag_tools`.

Sub-packages
------------
- ``runners/``  — Framework-agnostic execution entry points used by Langflow
                  Custom Components, the OpenAI compat adapter and the
                  Unity RPC server.
- ``nodes/``    — Stateful node functions reused by every runner.
- ``prompts/``  — Prompt manager.
- ``tools/``    — RAG core helpers.
- ``smart_router`` — Requirement-text → graph_id classifier.
"""

__version__ = "3.0.0"

# Public runners (preferred entry point)
from .runners import (
    run_skill_generation,
    stream_skill_generation,
    run_progressive_skill_generation,
    stream_progressive_skill_generation,
    run_action_batch_skill_generation,
    stream_action_batch_skill_generation,
    run_skill_search,
    stream_skill_search,
    run_skill_detail,
    stream_skill_detail,
    run_skill_validation,
    stream_skill_validation,
    run_parameter_inference,
    stream_parameter_inference,
    route_to_runner_name,
    RUNNER_NAME_TO_RUN,
    RUNNER_NAME_TO_STREAM,
)

# Legacy smart-router helpers (still used by callers that want the raw
# graph_id, e.g. observability layers).
from .smart_router import (
    smart_route,
    analyze_complexity,
    get_available_graphs,
)

# Tool surface (RAG)
from .tools.rag_tools import RAG_TOOLS

# Prompt manager
from .prompts.prompt_manager import get_prompt_manager


__all__ = [
    # Runners (framework-agnostic, recommended)
    "run_skill_generation",
    "stream_skill_generation",
    "run_progressive_skill_generation",
    "stream_progressive_skill_generation",
    "run_action_batch_skill_generation",
    "stream_action_batch_skill_generation",
    "run_skill_search",
    "stream_skill_search",
    "run_skill_detail",
    "stream_skill_detail",
    "run_skill_validation",
    "stream_skill_validation",
    "run_parameter_inference",
    "stream_parameter_inference",
    "route_to_runner_name",
    "RUNNER_NAME_TO_RUN",
    "RUNNER_NAME_TO_STREAM",
    # Smart router
    "smart_route",
    "analyze_complexity",
    "get_available_graphs",
    # Tools / managers
    "RAG_TOOLS",
    "get_prompt_manager",
]
