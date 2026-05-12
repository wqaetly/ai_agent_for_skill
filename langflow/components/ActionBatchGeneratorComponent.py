"""
ActionBatchGeneratorComponent — coarse-grained wrapper around
`stream_action_batch_skill_generation`. Used by the
`action_batch_skill_generation` flow.

This is the most token-efficient pipeline (per-batch generation inside
each track) and is selected automatically by the Smart Router when the
requirement complexity score is high.
"""

from typing import Any, List

from lfx.custom.custom_component.component import Component
from lfx.io import HandleInput, IntInput, Output
from lfx.schema.data import Data

from skill_agent.orchestration.runners import stream_action_batch_skill_generation


class ActionBatchGeneratorComponent(Component):
    display_name: str = "Action Batch Generator"
    description: str = (
        "Token-efficient action-batch progressive generation: skeleton → "
        "per-track batches → track assembler → skill assembler. Streams "
        "per-node progress."
    )
    icon = "boxes"
    name = "ActionBatchGeneratorComponent"

    inputs = [
        HandleInput(
            name="requirement",
            display_name="Requirement",
            input_types=["Message", "str"],
            required=True,
        ),
        IntInput(
            name="max_batch_retries",
            display_name="Max Batch Retries",
            value=2,
            advanced=True,
        ),
        IntInput(
            name="token_budget",
            display_name="Token Budget",
            value=100000,
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
            "max_batch_retries": int(self.max_batch_retries or 2),
            "token_budget": int(self.token_budget or 100000),
        }

        progress_log: List[str] = []
        final_state: dict = {}
        for event in stream_action_batch_skill_generation(initial_state):
            if event.get("final"):
                final_state = event["result"]
                continue
            node = event.get("node", "?")
            state = event.get("state", {})
            t_idx = state.get("current_track_index")
            t_total = len(state.get("track_plan") or [])
            b_idx = state.get("current_batch_index")
            b_total = len(state.get("current_track_batch_plan") or [])
            extra = ""
            if t_total:
                extra = f" (track {t_idx}/{t_total}"
                if b_total:
                    extra += f", batch {b_idx}/{b_total}"
                extra += ")"
            progress_log.append(f"[{node}]{extra}")
            self.status = "\n".join(progress_log[-15:])

        self.status = {
            "node": "finalize",
            "is_valid": bool(final_state.get("is_valid")),
            "track_count": len(final_state.get("generated_tracks") or []),
            "tokens_used": final_state.get("total_tokens_used", 0),
        }
        return Data(data=final_state)
