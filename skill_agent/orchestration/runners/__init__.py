"""
Framework-agnostic runners that replace the LangGraph graphs.

Each runner is a pure-Python function/generator that:
  - Accepts an `initial_state: dict` (same shape as the legacy LangGraph state).
  - Internally calls the existing node functions in
    `skill_agent.orchestration.nodes.*` (which are already framework-neutral
    `(state: dict) -> dict` callables).
  - Replaces LangGraph's `add_conditional_edges` with explicit `while` loops
    and `match` dispatch on the route function return values.
  - Optionally `yield`s `(node_name, state_delta)` tuples through the
    streaming variant so callers (Langflow Custom Components, OpenAI compat
    adapter, Unity RPC) can surface progress without depending on LangGraph.

Why this exists
---------------
LangGraph's `StateGraph.compile()` couples runtime semantics (checkpoint,
recursion limit, conditional edges) with our business logic. Migrating to
Langflow requires a runtime that:

  1. Has zero `import langgraph` at the public API surface.
  2. Can be wrapped in a Langflow Custom Component as a generator.
  3. Can be unit-tested with plain `pytest` (no `compile()` step).

This package provides exactly that.

Transitional dependency
-----------------------
During Task 2 the underlying node modules
(`progressive_skill_nodes`, `action_batch_skill_nodes`, ...) still import a
small subset of LangGraph helpers (`add_messages`, `StreamWriter`,
`get_stream_writer`). Task 7 removes those imports by routing them through
`skill_agent.orchestration._compat` once `langgraph` is dropped from
`requirements.txt`. The runner *callers* (Langflow Components, OpenAI
adapter, Unity RPC) never reach those node-internal imports themselves.

Public exports
--------------
Each `run_*` returns the final state dict. Each `stream_*` is a generator
yielding events of the form::

    {"node": "<node_name>", "state": <full_state_after_node>}

ending with::

    {"final": True, "result": <final_state>}

Smart routing
-------------
`smart_router.route_to_runner_name(text)` returns the canonical OpenAI model
id (e.g. `progressive-skill-generation`) for a given user input.
"""

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
from .parameter_inference import run_parameter_inference, stream_parameter_inference
from .smart_router import route_to_runner_name, RUNNER_NAME_TO_RUN, RUNNER_NAME_TO_STREAM

__all__ = [
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
]
