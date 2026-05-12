"""
Snapshot test for the Unity ⇄ Python RPC protocol.

Goals
-----
1. Lock the **Python-side** built-in RPC method names (`ping`,
   `get_server_info`) so accidental renames break the test loud and early.
2. Lock the **Unity-side** RPC method names (parsed straight from the
   C# `UnityRPCBridge.cs` file) so renaming a Unity handler without
   updating the Python side gets flagged here.
3. Lock the JSON-RPC envelope wire format (length-prefixed JSON, 2.0,
   `id` is `Optional[str]`) so the wire protocol stays stable across
   the migration.

The tests deliberately do not start the actual server; they introspect
the source files. This keeps the suite independent of Unity Editor.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Use the project layout the existing conftest sets up.
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT))


# ---------------------------------------------------------------------------
# Python-side built-in RPC methods
# ---------------------------------------------------------------------------

EXPECTED_PYTHON_BUILTIN_METHODS = {"ping", "get_server_info"}


def test_python_builtin_rpc_methods_are_stable():
    from Python.unity_rpc_server import UnityRPCServer

    server = UnityRPCServer(host="127.0.0.1", port=0)
    actual = set(server.method_handlers.keys())
    assert EXPECTED_PYTHON_BUILTIN_METHODS.issubset(actual), (
        f"Built-in Python RPC methods drifted; expected at least "
        f"{EXPECTED_PYTHON_BUILTIN_METHODS}, got {actual}"
    )


# ---------------------------------------------------------------------------
# Unity-side RPC methods (parsed from C# source)
# ---------------------------------------------------------------------------

EXPECTED_UNITY_METHODS = {
    "CreateSkill",
    "UpdateSkill",
    "DeleteSkill",
    "GetSkillList",
    "ValidateConfig",
    "ApplyParameters",
}

UNITY_BRIDGE_PATH = (
    REPO_ROOT
    / "ai_agent_for_skill"
    / "Packages"
    / "com.rag.skill-agent"
    / "Editor"
    / "SkillSystem"
    / "UnityRPCBridge.cs"
)


def test_unity_rpc_methods_match_snapshot():
    text = UNITY_BRIDGE_PATH.read_text(encoding="utf-8")
    found = set(re.findall(r'RegisterMethod\(\s*"([A-Za-z_][\w]*)"', text))
    assert found == EXPECTED_UNITY_METHODS, (
        f"Unity RPC method snapshot drifted.\n"
        f"  Added:   {found - EXPECTED_UNITY_METHODS}\n"
        f"  Removed: {EXPECTED_UNITY_METHODS - found}\n"
        f"If this is intentional, update EXPECTED_UNITY_METHODS in "
        f"{__file__} together with the matching Python handler in "
        f"`skill_agent/Python/unity_rpc_runtime.py`."
    )


# ---------------------------------------------------------------------------
# JSON-RPC wire envelope
# ---------------------------------------------------------------------------

def test_jsonrpc_envelope_is_v2_with_optional_string_id():
    """
    Both sides must agree on:
      - jsonrpc literal "2.0"
      - `id` is optional (notification when missing) and stringly typed
      - the length-prefixed framing is 4-byte big-endian
    """
    from Python.unity_rpc_server import (
        JSONRPCRequest,
        JSONRPCResponse,
        UnityClient,
    )

    req = JSONRPCRequest(method="ping")
    assert req.jsonrpc == "2.0"
    assert req.id is None  # notifications have no id

    resp = JSONRPCResponse(result={"pong": True}, id="abc")
    assert resp.jsonrpc == "2.0"
    assert resp.id == "abc"

    # Length prefix: implementations on both sides must use 4 bytes big-endian.
    bridge_source = UNITY_BRIDGE_PATH.read_text(encoding="utf-8")
    # The Unity bridge only registers methods; the actual length-prefix lives
    # in UnityRPCClient.cs. Spot-check that the constant 4 is present.
    rpc_client_path = (
        REPO_ROOT
        / "ai_agent_for_skill"
        / "Packages"
        / "com.rag.skill-agent"
        / "Editor"
        / "SkillSystem"
        / "UnityRPCClient.cs"
    )
    assert rpc_client_path.exists(), f"missing {rpc_client_path}"

    client_src = rpc_client_path.read_text(encoding="utf-8")
    # We don't pin a specific style — but 4-byte length framing is the
    # protocol contract; either an explicit `[4]` byte buffer or a
    # `BitConverter` over an int32 must be present.
    assert "BitConverter" in client_src or "byte[4]" in client_src or "byte[] lengthBuffer" in client_src, (
        "UnityRPCClient.cs no longer uses a 4-byte length-prefix; the "
        "Python receive loop in unity_rpc_server.py expects exactly that."
    )


# ---------------------------------------------------------------------------
# Internal Langflow client surface (for parameter-inference RPC path)
# ---------------------------------------------------------------------------

def test_unity_rpc_langflow_client_exposes_parameter_inference_runner():
    from Python.unity_rpc_langflow_client import _FLOW_NAME_BY_RUNNER

    # The Unity "smart suggestion" buttons are documented to call this
    # runner; if the mapping ever drops it, the RPC method behind those
    # buttons starts failing with a confusing ValueError instead of a
    # clear test failure here.
    assert "parameter-inference" in _FLOW_NAME_BY_RUNNER
    assert _FLOW_NAME_BY_RUNNER["parameter-inference"] == "parameter_inference"
