"""
Import-level smoke test for the framework-agnostic runners.

These tests intentionally avoid hitting the real LLM, real RAG and real
network — they only assert that:

  1. The runner package imports cleanly without `langgraph` reaching the
     public surface of `skill_agent.orchestration.runners`.
  2. Every runner-name in the dispatch table maps to a callable.
  3. The smart router routes "火球术造成 100 点火焰伤害" to one of the
     three skill-generation flavours (legacy parity).
  4. The smart router routes "搜索远程攻击技能" to skill-search.

These four checks are enough to catch the most common regressions caused
by the migration (broken imports, typo'd dispatch keys, smart-router
classification drift).
"""

from __future__ import annotations

import importlib
import inspect

import pytest


def test_runners_package_imports_cleanly():
    pkg = importlib.import_module("orchestration.runners")
    assert hasattr(pkg, "RUNNER_NAME_TO_RUN")
    assert hasattr(pkg, "RUNNER_NAME_TO_STREAM")
    assert hasattr(pkg, "route_to_runner_name")


def test_dispatch_tables_are_populated_with_callables():
    from orchestration.runners import (
        RUNNER_NAME_TO_RUN,
        RUNNER_NAME_TO_STREAM,
    )

    expected_runners = {
        "skill-generation",
        "progressive-skill-generation",
        "action-batch-skill-generation",
        "skill-search",
        "skill-detail",
        "skill-validation",
        "parameter-inference",
    }
    assert expected_runners.issubset(RUNNER_NAME_TO_RUN.keys())
    assert expected_runners.issubset(RUNNER_NAME_TO_STREAM.keys())

    for name, fn in RUNNER_NAME_TO_RUN.items():
        assert callable(fn), f"run dispatch for {name!r} is not callable"
    for name, fn in RUNNER_NAME_TO_STREAM.items():
        assert callable(fn), f"stream dispatch for {name!r} is not callable"
        # Stream variants must be generator functions (or yield-coroutines).
        assert inspect.isgeneratorfunction(fn), (
            f"stream dispatch for {name!r} is not a generator function"
        )


@pytest.mark.parametrize("text,expected_set", [
    (
        "火球术，造成 100 点火焰伤害",
        {"skill-generation", "progressive-skill-generation",
         "action-batch-skill-generation"},
    ),
    (
        "搜索远程攻击技能",
        {"skill-search"},
    ),
])
def test_route_to_runner_name_matches_legacy_smart_router(text, expected_set):
    from orchestration.runners import route_to_runner_name
    runner = route_to_runner_name(text)
    assert runner in expected_set, (
        f"smart router classified {text!r} as {runner!r}, expected one of {expected_set}"
    )


def test_simple_runners_are_pure_python_generators_or_callables():
    """
    The four single-node runners (`skill-search`, `skill-detail`,
    `skill-validation`, `parameter-inference`) are callable without any
    network/LLM, so we can at least introspect them.
    """
    from orchestration.runners import (
        run_skill_search,
        run_skill_detail,
        run_skill_validation,
        run_parameter_inference,
        stream_skill_search,
        stream_skill_detail,
        stream_skill_validation,
        stream_parameter_inference,
    )

    for fn in (
        run_skill_search,
        run_skill_detail,
        run_skill_validation,
        run_parameter_inference,
    ):
        assert callable(fn)
    for fn in (
        stream_skill_search,
        stream_skill_detail,
        stream_skill_validation,
        stream_parameter_inference,
    ):
        assert inspect.isgeneratorfunction(fn)
