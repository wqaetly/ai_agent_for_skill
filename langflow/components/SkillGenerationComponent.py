"""
SkillGenerationComponent — coarse-grained wrapper around
`stream_skill_generation`. Used by the `skill_generation` flow.

Strategy
--------
The original LangGraph `skill_generation` topology was a tight
retrieve -> generate -> validate -> fix loop. Per the migration plan,
complex graphs are wrapped as a single Langflow component because
Langflow's DAG model can't faithfully reproduce conditional cycles. We
still preserve per-stage observability by yielding progress through
`self.send_message_text` (so the Playground shows live updates) before
returning the final `Data` object.
"""

from typing import Any, List

from lfx.custom.custom_component.component import Component
from lfx.io import HandleInput, IntInput, Output
from lfx.schema.data import Data

from skill_agent.orchestration.runners import stream_skill_generation


class SkillGenerationComponent(Component):
    display_name: str = "Skill Generation (Standard)"
    description: str = (
        "Run the standard retrieve → generate → validate → fix loop and "
        "stream per-node progress to the Langflow Playground."
    )
    icon = "zap"
    name = "SkillGenerationComponent"

    inputs = [
        HandleInput(
            name="requirement",
            display_name="Requirement",
            input_types=["Message", "str"],
            required=True,
        ),
        IntInput(
            name="max_retries",
            display_name="Max Retries",
            value=3,
            advanced=True,
        ),
    ]

    outputs = [
        Output(display_name="Final Skill", name="result", method="generate"),
    ]

    def _resolve_requirement(self) -> str:
        raw: Any = self.requirement
        return raw.text if hasattr(raw, "text") else str(raw or "")

    def generate(self) -> Data:
        initial_state = {
            "requirement": self._resolve_requirement().strip(),
            "max_retries": int(self.max_retries or 3),
        }

        progress_log: List[str] = []
        final_state: dict = {}
        for event in stream_skill_generation(initial_state):
            if event.get("final"):
                final_state = event["result"]
                continue
            node = event.get("node", "?")
            progress_log.append(f"[{node}] state advanced")
            # `self.status` is what the Playground surfaces in real time.
            self.status = "\n".join(progress_log[-10:])

        self.status = {
            "node": "finalize",
            "is_valid": bool(final_state.get("final_result")),
            "retry_count": final_state.get("retry_count", 0),
        }
        return Data(data=final_state)
