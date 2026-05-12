"""
SkillSearchEmbeddingComponent — first half of the細粒度 `skill_search` flow.

In the legacy LangGraph `SkillSearch` was a single node. To meet the
"细粒度可单步调试" goal of the migration, we split it into:

    InputComponent -> SkillSearchEmbeddingComponent -> SkillSearchVectorComponent -> OutputComponent

This component normalises the query and forwards optional retrieval
parameters (top_k, filters) downstream as a `Data` object so the Langflow
playground can inspect the pre-vector-search payload.
"""

from typing import Any

from lfx.custom.custom_component.component import Component
from lfx.io import HandleInput, IntInput, MessageTextInput, Output
from lfx.schema.data import Data


class SkillSearchEmbeddingComponent(Component):
    display_name: str = "Skill Search · Prepare"
    description: str = (
        "Prepare the semantic-search payload (query + top_k + filters) for "
        "the downstream vector search node."
    )
    icon = "wand-2"
    name = "SkillSearchEmbeddingComponent"

    inputs = [
        HandleInput(
            name="query",
            display_name="Query",
            info="Free-form search query (typically wired from InputComponent).",
            input_types=["Message", "str"],
            required=True,
        ),
        IntInput(
            name="top_k",
            display_name="Top K",
            info="Maximum number of results to return.",
            value=5,
        ),
        MessageTextInput(
            name="filters_json",
            display_name="Filters (JSON)",
            info="Optional JSON object of structured filters (e.g. {\"skill_type\": \"AOE\"}).",
            value="",
            advanced=True,
        ),
    ]

    outputs = [
        Output(display_name="Search Payload", name="payload", method="build_payload"),
    ]

    def build_payload(self) -> Data:
        import json as _json

        # Accept Message or raw str transparently.
        raw_query: Any = self.query
        if hasattr(raw_query, "text"):
            query_text = raw_query.text
        else:
            query_text = str(raw_query or "")

        filters = None
        filters_json = (self.filters_json or "").strip()
        if filters_json:
            try:
                filters = _json.loads(filters_json)
            except (ValueError, TypeError):
                filters = None

        payload = {
            "query": query_text.strip(),
            "top_k": int(self.top_k or 5),
            "filters": filters,
        }
        self.status = payload
        return Data(data=payload)
