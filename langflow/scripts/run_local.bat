@echo off
REM ============================================================
REM Skill Agent — local Langflow launcher (no Docker required)
REM
REM Boots Langflow Server @7860 from the wqaetly/langflow @ dev fork
REM checked out as a git submodule under external/langflow.
REM
REM What this script does:
REM   1. Verifies the fork submodule and uv toolchain are present.
REM   2. Runs `uv sync` inside external/langflow to materialise the
REM      project's virtual environment (.venv).
REM   3. Exposes the repository root on PYTHONPATH so that custom
REM      components in langflow/components/ can do
REM      `from skill_agent.core.enhanced_rag_engine import ...`.
REM   4. Forwards skill_agent/.env (DEEPSEEK_API_KEY etc.) to Langflow.
REM   5. Starts Langflow with --components-path pointed at this repo's
REM      langflow/components/ directory.
REM
REM Frontend (:3000) is intentionally NOT started — Lobe Chat is the
REM end-user UI; the Langflow Playground is reachable on :7860 directly.
REM
REM Hand-off contract with launch.bat:
REM   - Called from launch.bat :launch_langflow inside `start ...` so it
REM     keeps running in its own console window.
REM   - Exits non-zero if any pre-flight check fails so the caller can
REM     decide whether to abort the rest of the bring-up.
REM
REM LFX_DEV behaviour (inherited from fork's restart_langflow.bat):
REM   - Unset / "0"  -> index mode (fast startup, requires built index)
REM   - "1"          -> full dynamic load (slow, picks up all changes)
REM   - "<pkg,...>"  -> partial dynamic load (recommended for component
REM                     iteration, e.g. "custom_proxy")
REM   Override by exporting LFX_DEV before invoking this script.
REM ============================================================

setlocal EnableDelayedExpansion

REM ----- Resolve paths --------------------------------------------------
REM SCRIPT_DIR = ...\langflow\scripts\
REM REPO_ROOT  = ...\
REM FORK_DIR   = ...\external\langflow\
set "SCRIPT_DIR=%~dp0"
if "!SCRIPT_DIR:~-1!"=="\" set "SCRIPT_DIR=!SCRIPT_DIR:~0,-1!"
for %%I in ("!SCRIPT_DIR!\..\..") do set "REPO_ROOT=%%~fI"
set "FORK_DIR=!REPO_ROOT!\external\langflow"
set "COMPONENTS_DIR=!REPO_ROOT!\langflow\components"
set "ENV_FILE=!REPO_ROOT!\skill_agent\.env"

echo ============================================================
echo  Skill Agent - Langflow local launcher
echo ============================================================
echo  Repo root        : !REPO_ROOT!
echo  Fork submodule   : !FORK_DIR!
echo  Components path  : !COMPONENTS_DIR!
echo  Env file         : !ENV_FILE!
echo ============================================================
echo.

REM ----- Pre-flight: fork submodule -------------------------------------
if not exist "!FORK_DIR!\pyproject.toml" (
    echo [Error] external\langflow submodule is not initialised.
    echo         Run from the repo root:
    echo             git submodule update --init --recursive
    exit /b 1
)

REM ----- Pre-flight: uv toolchain ---------------------------------------
where uv >nul 2>&1
if errorlevel 1 (
    echo [Error] `uv` is not on PATH.
    echo         Install with one of:
    echo             pip install uv
    echo             winget install astral-sh.uv
    exit /b 1
)

REM ----- Pre-flight: skill_agent .env -----------------------------------
if not exist "!ENV_FILE!" (
    echo [Warn] !ENV_FILE! not found. Custom components that talk to
    echo        DeepSeek Reasoner will fail at runtime. Run launch.bat
    echo        once first to bootstrap DEEPSEEK_API_KEY, or create the
    echo        file manually.
)

REM ----- Step 1: uv sync the fork virtualenv ----------------------------
echo [1/3] Syncing fork virtual environment via `uv sync` ...
echo       (first run: 5-10 min download + build; subsequent runs: ~seconds)
pushd "!FORK_DIR!"
uv sync
set "UV_RC=!ERRORLEVEL!"
popd
if not "!UV_RC!"=="0" (
    echo [Error] `uv sync` failed inside !FORK_DIR! ^(exit code !UV_RC!^).
    echo         Re-run this script in a console with internet access.
    exit /b !UV_RC!
)
echo       OK.
echo.

REM ----- Step 2: configure PYTHONPATH for custom components -------------
REM Custom components do `from skill_agent.core...` so the repo root
REM must precede any other PYTHONPATH entry.
if defined PYTHONPATH (
    set "PYTHONPATH=!REPO_ROOT!;!PYTHONPATH!"
) else (
    set "PYTHONPATH=!REPO_ROOT!"
)
echo [2/3] PYTHONPATH = !PYTHONPATH!
echo.

REM ----- Step 3: launch Langflow Server ---------------------------------
REM We deliberately bind to 127.0.0.1 (not 0.0.0.0) — the OpenAI compat
REM adapter and Lobe Chat both run on the same host, so there is no need
REM to expose Langflow on the LAN.
if not defined LFX_DEV (
    set "LFX_DEV=0"
)

echo [3/3] Starting Langflow @ http://127.0.0.1:7860  ^(LFX_DEV=!LFX_DEV!^)
echo       Components path : !COMPONENTS_DIR!
echo       Env file        : !ENV_FILE!
echo.
echo       Press Ctrl+C in this window to stop the server.
echo ============================================================
echo.

pushd "!FORK_DIR!"

if exist "!ENV_FILE!" (
    uv run langflow run ^
        --host 127.0.0.1 ^
        --port 7860 ^
        --components-path "!COMPONENTS_DIR!" ^
        --env-file "!ENV_FILE!"
) else (
    uv run langflow run ^
        --host 127.0.0.1 ^
        --port 7860 ^
        --components-path "!COMPONENTS_DIR!"
)

set "LF_RC=!ERRORLEVEL!"
popd

endlocal & exit /b %LF_RC%
