"""
SmartRouterComponent — drives the `smart_skill_generation` flow.

Behaviour
---------
1. Classify the user requirement via `route_to_runner_name`.
2. Dispatch to the matching `stream_*` runner from
   `skill_agent.orchestration.runners`.
3. Surface both the routing decision and the runner's progress through
   `self.status`, then return the final state as a `Data` object.

This keeps the routing logic *inside* the flow (per requirement 3.5) so
the OpenAI compat adapter only has to forward `model="smart"` to this
single flow without baking routing rules into the adapter itself.
"""

from typing import Any, Dict, List

from lfx.custom.custom_component.component import Component
from lfx.io import BoolInput, HandleInput, Output
from lfx.schema.data import Data

from skill_agent.orchestration.runners import (
    RUNNER_NAME_TO_STREAM,
    route_to_runner_name,
)
from skill_agent.orchestration.runners.smart_router import (
    RUNNER_PROGRESSIVE,
    RUNNER_SKILL_GENERATION,
    RUNNER_ACTION_BATCH,
    RUNNER_SKILL_SEARCH,
    RUNNER_SKILL_DETAIL,
)


# Default initial-state builder per runner. Each builder receives the raw
# requirement text and returns a kwargs dict for the matching `stream_*`.
def _build_initial_state(runner_name: str, requirement: str) -> Dict[str, Any]:
    if runner_name == RUNNER_SKILL_SEARCH:
        return {"query": requirement, "top_k": 5}
    if runner_name == RUNNER_SKILL_DETAIL:
        return {"skill_id": requirement}
    # All three skill generation runners accept the same canonical key.
    return {"requirement": requirement}


class SmartRouterComponent(Component):
    display_name: str = "Smart Skill Router"
    description: str = (
        "Classify a user requirement and dispatch to the appropriate "
        "Skill Agent runner (search / generation / progressive / "
        "action-batch). Used by the smart_skill_generation flow."
    )
    icon = "sparkles"
    name = "SmartRouterComponent"

    inputs = [
        HandleInput(
            name="requirement",
            display_name="Requirement",
            input_types=["Message", "str"],
            required=True,
        ),
        BoolInput(
            name="prefer_progressive",
            display_name="Prefer Progressive",
            info="Bias the router towards progressive generation for borderline complex requirements.",
            value=True,
            advanced=True,
        ),
    ]

    outputs = [
        Output(display_name="Result", name="result", method="dispatch"),
    ]

    def _resolve_requirement(self) -> str:
        raw: Any = self.requirement
        return raw.text if hasattr(raw, "text") else str(raw or "")

    def dispatch(self) -> Data:
        requirement = self._resolve_requirement().strip()
        runner_name = route_to_runner_name(
            requirement, prefer_progressive=bool(self.prefer_progressive)
        )

        stream_fn = RUNNER_NAME_TO_STREAM.get(runner_name)
        if stream_fn is None:
            # Defensive fallback — should never happen because the router
            # only emits known runner names.
            runner_name = RUNNER_SKILL_GENERATION
            stream_fn = RUNNER_NAME_TO_STREAM[runner_name]

        initial_state = _build_initial_state(runner_name, requirement)

        progress_log: List[str] = [f"[router] -> {runner_name}"]
        self.status = "\n".join(progress_log)

        final_state: dict = {}
        for event in stream_fn(initial_state):
            if event.get("final"):
                final_state = event["result"]
                continue
            node = event.get("node", "?")
            progress_log.append(f"[{runner_name}:{node}]")
            self.status = "\n".join(progress_log[-15:])

        # Decorate the final state with the routing decision so callers
        # can audit which runner handled the request.
        final_state = dict(final_state)
        final_state["_smart_router"] = {
            "runner": runner_name,
            "is_generation": runner_name in {
                RUNNER_SKILL_GENERATION,
                RUNNER_PROGRESSIVE,
                RUNNER_ACTION_BATCH,
            },
        }
        return Data(data=final_state)
