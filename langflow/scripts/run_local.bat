@echo off
chcp 65001 >nul
REM ============================================================
REM Skill Agent - local Langflow launcher (no Docker required)
REM
REM Boots Langflow Server @7860 from the wqaetly/langflow @ dev fork
REM checked out as a git submodule under external/langflow.
REM
REM Layout closely mirrors external/langflow/restart_langflow.bat
REM (the fork's own dev launcher) so muscle memory carries over:
REM   [1/7] Stop existing services on 7860 / 3000
REM   [2/7] Build mode selection (LFX_DEV)
REM   [3/7] Rebuild component index (when LFX_DEV=0)
REM   [4/7] Start backend (Langflow @ 7860, --backend-only)
REM   [5/7] Wait for backend /health_check
REM   [6/7] Start frontend (Vite dev server @ 3000) for node-level
REM         debugging in the Playground UI
REM   [7/7] Done
REM
REM Differences vs the fork's restart_langflow.bat (intentional):
REM   - We run from THIS repo, not from the fork directory. The fork
REM     lives under external/langflow/ as a submodule and we pushd into
REM     it for the actual `uv run langflow run` call.
REM   - Backend launch uses `uv run langflow run --backend-only` instead
REM     of the fork's `uvicorn --factory langflow.main:create_app`.
REM     `--backend-only` is mandatory: the fork does NOT ship a built
REM     frontend dist, so without it langflow blows up at "Starting Core
REM     Services" with "Static files directory ... does not exist".
REM     The frontend (port 3000) is started SEPARATELY via vite dev
REM     server in Step 6 so node-level debugging in the Playground UI
REM     stays available - this is the same split as the fork itself.
REM   - We add a pre-flight `uv sync` of the fork's virtualenv, plus
REM     PYTHONPATH / outer-VIRTUAL_ENV hygiene.
REM
REM LFX_DEV behaviour (inherited from fork's restart_langflow.bat):
REM   - "0"          -> index mode (fast startup, requires built index)
REM   - "1"          -> full dynamic load (slow, picks up all changes)
REM   - "<pkg,...>"  -> partial dynamic load (recommended for component
REM                     iteration, e.g. "custom_proxy")
REM ============================================================

setlocal EnableDelayedExpansion

echo ========================================
echo   Skill Agent - LangFlow Restart Script
echo ========================================

REM ----- Outer venv leakage guard ---------------------------------------
REM Some users launch this script from a console where another venv is
REM already active (e.g. the repo-root `.venv`). uv warns about that
REM mismatch and, more importantly, the leaked VIRTUAL_ENV can confuse
REM `uv sync` into resolving paths against the wrong interpreter. We
REM clear the marker for the duration of this script only -- endlocal
REM at the bottom restores the caller's environment.
if defined VIRTUAL_ENV (
    echo [Info] Detected outer VIRTUAL_ENV=!VIRTUAL_ENV! ; clearing for this run.
    set "VIRTUAL_ENV="
)

REM ----- uv link mode -------------------------------------------------
REM We deliberately do NOT force UV_LINK_MODE=copy here:
REM   1. The fork's pyproject.toml already sets cache-dir = '.uv-cache'
REM      under the project, which guarantees the uv cache and the .venv
REM      live on the same drive letter -> hardlink fast-path works.
REM   2. An earlier experiment that pinned link-mode = 'copy' caused
REM      langflow to fail at runtime with "package not found" errors
REM      in some scenarios (recorded in project memory: link-mode=copy
REM      was rolled back). We respect that decision here.
REM   3. The previous attempt to forward UV_LINK_MODE through a child
REM      `cmd /k "... && set UV_LINK_MODE=!UV_LINK_MODE! && ..."`
REM      also ran into cmd's quirk that an unquoted `set VAR=val` swallows
REM      the trailing whitespace before the next `&&`, producing the
REM      literal value 'copy ' (with trailing space) which uv rejects:
REM        error: invalid value 'copy ' for '--link-mode <LINK_MODE>'
REM      Removing the var altogether sidesteps that landmine entirely.

REM ----- Resolve paths --------------------------------------------------
REM SCRIPT_DIR = ...\langflow\scripts\
REM REPO_ROOT  = ...\
REM FORK_DIR   = ...\external\langflow\   (this is the "working dir" for
REM                                        all uv / langflow commands)
set "SCRIPT_DIR=%~dp0"
if "!SCRIPT_DIR:~-1!"=="\" set "SCRIPT_DIR=!SCRIPT_DIR:~0,-1!"
for %%I in ("!SCRIPT_DIR!\..\..") do set "REPO_ROOT=%%~fI"
set "FORK_DIR=!REPO_ROOT!\external\langflow"
set "COMPONENTS_DIR=!REPO_ROOT!\langflow\components"
set "ENV_FILE=!REPO_ROOT!\skill_agent\.env"
set "LANGFLOW_LOG=!SCRIPT_DIR!\last_run.log"

REM ----------------------------------------------------------------------------
REM User config: default LFX_DEV value used when Step 2 prompt is left empty.
REM   Set to a comma-separated package list to enable list mode by default,
REM     e.g.  custom_proxy            (recommended for component iteration)
REM           custom_proxy,openai     (multiple packages)
REM   Set to 1     -> full dynamic load by default (slow)
REM   Set to 0     -> index mode by default (fast, requires rebuilt index)
REM   Leave empty  -> no default; pressing Enter at the prompt falls back to
REM                   index mode (LFX_DEV=0).
REM ----------------------------------------------------------------------------
set "DEFAULT_LFX_DEV=custom_proxy"

echo  Repo root        : !REPO_ROOT!
echo  Fork submodule   : !FORK_DIR!
echo  Components path  : !COMPONENTS_DIR!
echo  Env file         : !ENV_FILE!
echo  Run log          : !LANGFLOW_LOG!
echo ========================================

REM ----- Pre-flight: fork submodule -------------------------------------
if not exist "!FORK_DIR!\pyproject.toml" (
    echo [Error] external\langflow submodule is not initialised.
    echo         Run from the repo root:
    echo             git submodule update --init --recursive
    call :pause_always
    endlocal ^& exit /b 1
)

REM ----- Pre-flight: uv toolchain ---------------------------------------
where uv >nul 2>&1
if errorlevel 1 (
    echo [Error] `uv` is not on PATH.
    echo         Install with one of:
    echo             pip install uv
    echo             winget install astral-sh.uv
    call :pause_always
    endlocal ^& exit /b 1
)

REM ----- Pre-flight: skill_agent .env -----------------------------------
if not exist "!ENV_FILE!" (
    echo [Warn] !ENV_FILE! not found. Custom components that talk to
    echo        DeepSeek Reasoner will fail at runtime. Run launch.bat
    echo        once first to bootstrap DEEPSEEK_API_KEY, or create the
    echo        file manually.
)

REM ----- Pre-flight: paths must not contain spaces ----------------------
REM Step 4 launches the backend via `start "LangFlow-Backend" cmd /k "..."`,
REM which wraps the entire command line in a single pair of double quotes.
REM Internal quotes around path arguments would break that wrapping (cmd's
REM quote pairing is greedy), so we deliberately pass path arguments
REM unquoted - exactly mirroring the fork's restart_langflow.bat. That
REM works only if the paths themselves contain no whitespace. Detect the
REM bad case here and fail loudly instead of producing a confusing silent
REM start failure later.
REM
REM Implementation note: we deliberately AVOID `echo ... | findstr " "`
REM here. The right side of a cmd pipe runs in a fresh subshell that does
REM NOT inherit `setlocal EnableDelayedExpansion`, so `!REPO_ROOT!` may
REM not expand and the check produces false positives / false negatives
REM depending on console host quirks. Instead we use the pure in-process
REM string substitution `!VAR: =!` (strip all spaces) and compare against
REM the original - if they differ, the original contained a space.
set "_repo_no_space=!REPO_ROOT: =!"
if not "!_repo_no_space!"=="!REPO_ROOT!" (
    echo [Error] Repository root contains a space: !REPO_ROOT!
    echo         The Step 4 backend launcher passes path arguments without
    echo         double-quoting them ^(to avoid breaking the start ^/ cmd /k
    echo         quote nesting^), so spaces in the path will silently break
    echo         `langflow run --components-path ... --env-file ...`.
    echo         Move the repo to a space-free path ^(e.g. C:\dev\ai_agent_for_skill^)
    echo         and re-run.
    call :pause_always
    endlocal ^& exit /b 1
)
set "_repo_no_space="

REM ============================================================
REM Step 1: Kill existing processes on ports 7860 and 3000
REM ============================================================
echo.
echo [1/7] Stopping existing services...

REM Kill LISTENING processes on port 7860 (use /T to kill entire process tree)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":7860 " ^| findstr LISTENING 2^>nul') do (
    echo   Killing PID %%a and its child processes ^(port 7860 LISTENING^)
    taskkill /F /T /PID %%a >nul 2>&1
)
REM Kill LISTENING processes on port 3000 (use /T to kill entire process tree)
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000 " ^| findstr LISTENING 2^>nul') do (
    echo   Killing PID %%a and its child processes ^(port 3000 LISTENING^)
    taskkill /F /T /PID %%a >nul 2>&1
)

REM Also kill any lingering LangFlow-Backend/Frontend windows by title
taskkill /F /FI "WINDOWTITLE eq LangFlow-Backend*" >nul 2>&1
taskkill /F /FI "WINDOWTITLE eq LangFlow-Frontend*" >nul 2>&1

REM Fallback: kill any python.exe whose command line contains 'langflow.main:create_app'
REM This catches zombie uvicorn processes that have no LangFlow-Backend window title
REM (e.g. spawned from another terminal session) and would otherwise hold port 7860.
for /f "tokens=2 delims=," %%p in ('wmic process where "name='python.exe' and CommandLine like '%%langflow.main:create_app%%'" get ProcessId /format:csv 2^>nul ^| findstr /r "[0-9]"') do (
    echo   Killing zombie uvicorn python PID %%p ^(by command line match^)
    taskkill /F /T /PID %%p >nul 2>&1
)
REM Also catch `langflow run` style processes started by `uv run langflow run ...`
for /f "tokens=2 delims=," %%p in ('wmic process where "name='python.exe' and CommandLine like '%%langflow run%%'" get ProcessId /format:csv 2^>nul ^| findstr /r "[0-9]"') do (
    echo   Killing zombie langflow-run python PID %%p ^(by command line match^)
    taskkill /F /T /PID %%p >nul 2>&1
)

REM Wait and verify port 7860 is truly free by attempting to bind (with retries)
REM This also catches non-LISTENING usage (e.g. VPN/proxy using 7860 as ephemeral source port)
timeout /t 2 /nobreak >nul
set /a port_retry=0
set /a port_max_retry=5

:port_check_loop
"!FORK_DIR!\.venv\Scripts\python.exe" -c "import socket; s=socket.socket(); s.bind(('0.0.0.0',7860)); s.close()" >nul 2>&1
if not errorlevel 1 goto :port_free

set /a port_retry+=1
if !port_retry! gtr !port_max_retry! goto :port_stuck

echo   Port 7860 occupied ^(attempt !port_retry!/!port_max_retry!^), diagnosing...
REM Show what is using port 7860 (with process name)
for /f "tokens=2,5" %%a in ('netstat -ano ^| findstr ":7860 " 2^>nul') do (
    set "_pname=?"
    for /f "tokens=1 delims=," %%n in ('tasklist /FI "PID eq %%b" /NH /FO CSV 2^>nul') do set "_pname=%%~n"
    echo     Connection: %%a  PID: %%b  Process: !_pname!
)
REM Kill any LISTENING process on 7860
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":7860 " ^| findstr LISTENING 2^>nul') do (
    echo   Force killing LISTENING PID %%a
    taskkill /F /T /PID %%a >nul 2>&1
)
REM Also re-run the command-line based zombie kill (in case a non-LISTENING uvicorn is bound)
for /f "tokens=2 delims=," %%p in ('wmic process where "name='python.exe' and CommandLine like '%%langflow.main:create_app%%'" get ProcessId /format:csv 2^>nul ^| findstr /r "[0-9]"') do (
    echo   Force killing zombie uvicorn python PID %%p
    taskkill /F /T /PID %%p >nul 2>&1
)
for /f "tokens=2 delims=," %%p in ('wmic process where "name='python.exe' and CommandLine like '%%langflow run%%'" get ProcessId /format:csv 2^>nul ^| findstr /r "[0-9]"') do (
    echo   Force killing zombie langflow-run python PID %%p
    taskkill /F /T /PID %%p >nul 2>&1
)
timeout /t 3 /nobreak >nul
goto :port_check_loop

:port_stuck
echo.
echo   ============================================================
echo   ERROR: Port 7860 is still occupied after !port_max_retry! retries.
echo   This is usually caused by VPN/proxy software using 7860 as
echo   an ephemeral source port for outbound connections.
echo.
echo   Current connections on port 7860:
for /f "tokens=*" %%a in ('netstat -ano ^| findstr ":7860 " 2^>nul') do (
    echo     %%a
)
echo.
echo   Options:
echo     1. Re-run this script in an Administrator cmd ^(needed if the
echo        occupying process belongs to a different user/session and
echo        non-admin taskkill is denied^).
echo     2. Disconnect VPN/proxy, then re-run this script.
echo     3. Wait a few minutes for the connection to close, then retry.
echo     4. Run as Administrator: netsh int ipv4 add excludedportrange protocol=tcp startport=7860 numberofports=1
echo        ^(permanently reserves port 7860 from ephemeral allocation^)
echo   ============================================================
echo.
call :pause_always
endlocal ^& exit /b 1

:port_free
echo   Port 7860 is free. Done.

REM ============================================================
REM Pre-step before [2/7]: uv sync the fork virtualenv
REM ------------------------------------------------------------
REM This is OUR addition vs the fork's restart script: the fork
REM assumes .venv already exists, but in a fresh checkout we have
REM to materialise it first. After this step the fork's own
REM .venv\Scripts\python.exe is guaranteed to exist for use in
REM Step 3 (build_component_index.py) and Step 5 (health_check
REM probe).
REM ============================================================
echo.
echo [Pre] Syncing fork virtual environment via `uv sync` ...
echo       (first run: 5-10 min download + build; subsequent runs: ~seconds)
pushd "!FORK_DIR!"
uv sync
set "UV_RC=!ERRORLEVEL!"
popd
if not "!UV_RC!"=="0" (
    echo [Error] `uv sync` failed inside !FORK_DIR! ^(exit code !UV_RC!^).
    echo         Common causes on Windows:
    echo           1. Another langflow / python.exe still holds files in
    echo              !FORK_DIR!\.venv  ^(check Task Manager, kill, retry^).
    echo           2. Windows Defender real-time scan locked a wheel
    echo              mid-install ^(ACCESS_DENIED / os error -2147024891^).
    echo              Run external\langflow\setup_defender_exclusions.ps1
    echo              from an elevated PowerShell, then retry.
    echo           3. The console you launched from already has another
    echo              venv activated; open a fresh cmd and try again.
    call :pause_always
    endlocal ^& exit /b !UV_RC!
)
echo       OK.

REM ============================================================
REM Step 2: Ask whether to do a full build (LFX_DEV)
REM ============================================================
echo.
echo [2/7] Build mode selection:
echo   y                  = Full dynamic load ^(LFX_DEV=1, slow on Windows: minutes^)
echo   n                  = Index mode        ^(LFX_DEV=0, fast: ~10s, requires index rebuild^)
echo   ^<pkg1,pkg2,...^>    = Partial dynamic   ^(LFX_DEV=pkg1,pkg2; only these packages are
echo                                            reflected at startup, the rest read the
echo                                            prebuilt index. Recommended for iterating
echo                                            on a few components, e.g. "custom_proxy"^)
echo   ^<Enter^>            = Use built-in default "!DEFAULT_LFX_DEV!" ^(edit DEFAULT_LFX_DEV at top of this .bat to change^)
echo   -                  = Force index mode this run, ignoring the default
echo.
set /p "full_build=Choose mode (y / n / pkgs / Enter=default / -): "
if /i "!full_build!"=="y" (
    echo   Selected: Full dynamic load, LFX_DEV=1
    set "LFX_DEV=1"
) else if /i "!full_build!"=="n" (
    echo   Selected: Index mode, LFX_DEV=0
    set "LFX_DEV=0"
) else if "!full_build!"=="-" (
    echo   Selected: Index mode this run ^(default ignored^), LFX_DEV=0
    set "LFX_DEV=0"
) else if "!full_build!"=="" (
    if "!DEFAULT_LFX_DEV!"=="" (
        echo   No default configured, falling back to index mode, LFX_DEV=0
        set "LFX_DEV=0"
    ) else (
        echo   Using default from script, LFX_DEV=!DEFAULT_LFX_DEV!
        set "LFX_DEV=!DEFAULT_LFX_DEV!"
    )
) else (
    echo   Selected: Partial dynamic load, LFX_DEV=!full_build!
    set "LFX_DEV=!full_build!"
)

REM ============================================================
REM Step 3: Rebuild component index (skipped whenever LFX_DEV is non-empty and not "0")
REM ============================================================
echo.
if not "!LFX_DEV!"=="0" (
    echo [3/7] Skipping component index rebuild ^(LFX_DEV=!LFX_DEV!, not needed^)...
    goto :step4
)
echo [3/7] Rebuilding component index...
pushd "!FORK_DIR!"
.venv\Scripts\python.exe scripts\build_component_index.py
set "IDX_RC=!ERRORLEVEL!"
popd
if not "!IDX_RC!"=="0" (
    echo   WARNING: Failed to rebuild component index ^(exit code !IDX_RC!^). Continuing anyway...
) else (
    echo   Component index rebuilt successfully.
)

:step4
REM ============================================================
REM Step 4: Start backend (Langflow @ 7860)
REM ------------------------------------------------------------
REM This is where we DIVERGE from the fork's restart_langflow.bat:
REM   - The fork starts uvicorn directly with --factory.
REM   - We use `uv run langflow run --backend-only ...` because:
REM       * The fork has no built frontend dist; --backend-only
REM         prevents the "Static files directory does not exist"
REM         RuntimeError that closes the window instantly.
REM       * --components-path / --env-file are first-class CLI
REM         args of `langflow run`, no need to wire them via env.
REM   - We also configure PYTHONPATH so custom components can do
REM     `from skill_agent.core.* import ...`.
REM   - The child cmd /k window stays open after a crash, so the
REM     traceback is visible directly in that window. last_run.log
REM     keeps a banner only - tee is no longer attempted because
REM     the triple-nested escaping (start / cmd /k / powershell)
REM     is brittle and was the root cause of past silent failures.
REM ============================================================
echo.
if "!LFX_DEV!"=="1" (
    echo [4/7] Starting backend - port 7860, full dynamic load, LFX_DEV=1 ...
) else if "!LFX_DEV!"=="0" (
    echo [4/7] Starting backend - port 7860, index mode, LFX_DEV=0 ...
) else (
    echo [4/7] Starting backend - port 7860, partial dynamic load, LFX_DEV=!LFX_DEV! ...
)

REM ----- configure PYTHONPATH for custom components ---------------------
REM Custom components do `from skill_agent.core...` so the repo root
REM must precede any other PYTHONPATH entry.
if defined PYTHONPATH (
    set "BACKEND_PYTHONPATH=!REPO_ROOT!;!PYTHONPATH!"
) else (
    set "BACKEND_PYTHONPATH=!REPO_ROOT!"
)
echo       PYTHONPATH      : !BACKEND_PYTHONPATH!
echo       Mode            : backend-only ^(no static frontend in fork^)
echo       Components path : !COMPONENTS_DIR!
echo       Env file        : !ENV_FILE!
echo       Run log         : !LANGFLOW_LOG!

REM Build the backend command and launch in a new window.
REM
REM Why `cmd /k` instead of `cmd /c`:
REM   If langflow / uv crashes before reaching the listen state,
REM   `cmd /c` would close the window instantly. `cmd /k` keeps
REM   the window open so the traceback stays visible.
REM
REM Why we DO NOT pipe to PowerShell Tee-Object inside the child
REM window any more (lessons learned from older revisions of this
REM script): nesting `cmd /k "..."` + `\"...\"` + `2^>^&1 ^| powershell
REM ... ^| Tee-Object \"...\"` requires three levels of escaping
REM (outer start, inner cmd /k, inner powershell). Any single
REM mistake makes cmd parse the closing quote in the wrong place
REM and the start command silently fails. We instead let the child
REM window display output live (cmd /k stays open so it cannot be
REM lost), and rely on Langflow's own log file for crash forensics.
REM   The Tee-Object dance was originally added because, when this
REM   script ran in the FOREGROUND of the calling shell, a crash
REM   could close the parent shell before the user could copy the
REM   traceback. Now that we always launch backend via `start ...`
REM   in a separate `cmd /k` window, the window itself is the
REM   forensic record - it just stays open with the traceback
REM   visible until the user closes it.
echo ==== Langflow run @ %DATE% %TIME% ==== > "!LANGFLOW_LOG!"
echo [Note] Realtime stdout is in the LangFlow-Backend child window. >> "!LANGFLOW_LOG!"
echo        This file is only a placeholder; for live output check that window. >> "!LANGFLOW_LOG!"

REM Trick: instead of stuffing `set VAR=val && set VAR=val && ...` into
REM the child cmd /k command line (which a) requires inner quotes that
REM break the outer start "..." wrapping, and b) silently swallows the
REM space before each `&&` into the variable value -> ate us with
REM UV_LINK_MODE='copy '), we set the environment variables HERE in
REM the parent process. `start` propagates the parent environment to
REM the child, so the child cmd /k just needs `cd /d ... && uv run ...`.
REM This keeps the start command line free of any inner quotes AND any
REM unquoted `set` assignments, eliminating both classes of bug.
set "VIRTUAL_ENV=!FORK_DIR!\.venv"
set "PATH=!FORK_DIR!\.venv\Scripts;%PATH%"
set "PYTHONPATH=!BACKEND_PYTHONPATH!"

if exist "!ENV_FILE!" (
    start "LangFlow-Backend" cmd /k "cd /d !FORK_DIR! && uv run langflow run --backend-only --host 127.0.0.1 --port 7860 --components-path !COMPONENTS_DIR! --env-file !ENV_FILE!"
) else (
    start "LangFlow-Backend" cmd /k "cd /d !FORK_DIR! && uv run langflow run --backend-only --host 127.0.0.1 --port 7860 --components-path !COMPONENTS_DIR!"
)

REM ============================================================
REM Step 5: Wait for backend to be ready via /health_check
REM ============================================================
echo.
echo [5/7] Waiting for backend to be ready...
set /a attempts=0
set /a max_attempts=120

:wait_loop
set /a attempts+=1
if !attempts! gtr !max_attempts! (
    echo   WARNING: Backend did not become ready after !max_attempts! attempts.
    echo   See !LANGFLOW_LOG! for the captured traceback.
    goto :start_frontend
)

timeout /t 3 /nobreak >nul
"!FORK_DIR!\.venv\Scripts\python.exe" -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:7860/health_check', timeout=5)" >nul 2>&1
if errorlevel 1 (
    echo   Attempt !attempts!/!max_attempts! - waiting...
    goto :wait_loop
)
echo   Backend is ready!

REM ============================================================
REM Step 6: Start frontend (Vite dev server on port 3000)
REM ------------------------------------------------------------
REM Why we DO start the frontend here (despite Lobe Chat being the
REM end-user UI for normal chat traffic):
REM   - The Langflow Playground UI on :3000 is THE tool for node-level
REM     debugging of custom components (drag-drop edit, run individual
REM     nodes, inspect intermediate IO). Killing it would force every
REM     debug session through raw API calls.
REM   - Backend runs with --backend-only, so the static frontend dist
REM     is NOT served by uvicorn. The Vite dev server on :3000 fills
REM     that gap and proxies /api -> 127.0.0.1:7860 via vite.config.
REM   - This mirrors the fork's restart_langflow.bat Step 6 verbatim,
REM     except that the frontend lives under !FORK_DIR! (submodule),
REM     not !SCRIPT_DIR!.
REM ============================================================
:start_frontend
echo.
echo [6/7] Starting frontend ^(port 3000^)...

REM Pre-flight: ensure frontend dependencies are installed and up-to-date.
REM vite.config.mts hard-imports vite-plugin-istanbul; if it's missing the
REM vite dev server crashes immediately and the cmd /c window closes.
set "FE_DIR=!FORK_DIR!\src\frontend"
set "NEED_NPM_INSTALL=0"
if not exist "!FE_DIR!\node_modules" set "NEED_NPM_INSTALL=1"
if not exist "!FE_DIR!\node_modules\vite\bin\vite.js" set "NEED_NPM_INSTALL=1"
if not exist "!FE_DIR!\node_modules\vite-plugin-istanbul\package.json" set "NEED_NPM_INSTALL=1"
if "!NEED_NPM_INSTALL!"=="1" (
    echo   Frontend dependencies missing or stale, running npm install ^(this may take a minute^)...
    pushd "!FE_DIR!"
    call npm install
    set "NPM_RC=!ERRORLEVEL!"
    popd
    if not "!NPM_RC!"=="0" (
        echo   ERROR: npm install failed ^(exit code !NPM_RC!^). Frontend will not be started.
        echo   Please run 'npm install' manually under !FE_DIR! and re-run this script.
        call :pause_always
        endlocal ^& exit /b 1
    )
    echo   Frontend dependencies installed.
) else (
    echo   Frontend dependencies look OK, skipping npm install.
)

REM Use cmd /k so the window stays open if vite crashes, making errors visible.
start "LangFlow-Frontend" cmd /k "cd /d !FE_DIR! && npm start"

REM ============================================================
REM Step 7: Done
REM ============================================================
echo.
echo [7/7] Services starting:
echo   Backend  ^(Langflow API^)      : http://127.0.0.1:7860
echo   Frontend ^(Langflow Playground^): http://127.0.0.1:3000
echo   Run log                      : !LANGFLOW_LOG!
echo.
echo Press any key to exit this window ^(the LangFlow-Backend / LangFlow-Frontend windows keep running^)...
pause >nul

endlocal ^& exit /b 0

REM ============================================================
REM Helpers
REM ============================================================
REM Always pause on failure, regardless of how we were invoked.
REM Rationale: a window that closes before the user can copy the
REM traceback is the worst-case failure mode. A spurious extra
REM keypress for an automated caller is strictly cheaper than
REM losing diagnostics.
:pause_always
echo.
echo Press any key to close this window...
pause >nul
exit /b 0
