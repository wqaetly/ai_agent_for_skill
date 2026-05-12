"""
LangGraph compatibility shims.

After v3.0 the project no longer depends on `langgraph`, but a handful of
node functions in `skill_agent.orchestration.nodes.*` still reference a
small subset of the LangGraph helper API:

  - `add_messages` — list reducer that appends new messages to a state.
  - `StreamWriter` — typing protocol for a "send a streaming event"
                     callable. We model it as a no-op `Callable[[Any], None]`
                     because runner-driven execution doesn't need real-time
                     streaming hooks at the node level (progress is yielded
                     by the runners themselves).
  - `get_stream_writer` — used by the legacy progress streaming helper to
                          obtain a `StreamWriter`. We return a no-op writer
                          so node bodies that try to send events keep
                          working without LangGraph installed.

These shims preserve runtime behaviour without forcing a rewrite of every
node file. Any future deprecation can replace `from .._compat import ...`
with the corresponding direct implementation.
"""

from __future__ import annotations

from typing import Any, Callable, List, Optional


def add_messages(
    existing: Optional[List[Any]], new: Optional[List[Any]]
) -> List[Any]:
    """Tiny replacement for `langgraph.graph.message.add_messages`.

    Concatenates two message lists; either side can be `None` or empty.
    """
    out: List[Any] = list(existing or [])
    if new:
        out.extend(new)
    return out


# `StreamWriter` is just a callable type in LangGraph. We use a plain
# `Callable` alias so type annotations like `writer: StreamWriter` keep
# resolving without LangGraph installed.
StreamWriter = Callable[[Any], None]


def _noop_writer(_event: Any) -> None:
    """Stream writer that drops every event on the floor."""


def get_stream_writer() -> StreamWriter:
    """Replacement for `langgraph.config.get_stream_writer`.

    Returns a no-op writer. Callers always treat a missing writer as a
    silent fallback, so this preserves their intended behaviour when
    invoked outside any LangGraph runtime.
    """
    return _noop_writer
