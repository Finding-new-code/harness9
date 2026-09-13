# Technical Handoff Report: Sandbox Execution Enforcement (Milestone 5 - Part 1: R5.1)

**Author:** explorer_1_m5 (Read-only Technical Explorer)  
**Date:** 2026-09-05  
**Target Delivery:** `.agents/explorer_1_m5/handoff.md`  
**Recipient:** Orchestrator (`9473b3cb-ee83-4756-bdcf-820eaf3c56fb`)  
**Scope:** Investigation of Hermes sandbox environment infrastructure (`tools/environments/`), H9 execution paths (HyperFrames rendering, asset downloading, filesystem operations), runtime boundary interfaces (`src/h9_runtime/execution.py`, `src/h9_runtime/bridge.py`), and architecture design for sandbox boundary enforcement across Docker, Modal, and Local environments.

---

## 1. Observation

### 1.1 Hermes Sandbox Environment Infrastructure (`tools/environments/`)

#### A. Unified Base Environment (`tools/environments/base.py`)
- **Core Abstraction (`BaseEnvironment`, line 650)**:
  `BaseEnvironment(ABC)` defines the execution lifecycle across all backends. Subclasses implement `_run_bash(cmd_string, login=..., timeout=..., stdin_data=...)` and `cleanup()`. The base class provides `execute()` with session snapshot sourcing, CWD tracking, interrupt handling, and timeout enforcement.
- **Session Snapshot Capture (`init_session()`, lines 764–853)**:
  Runs once on backend startup with `login=True`. Captures exported environment variables, function definitions (filtering out private functions via `awk`), aliases (`alias -p`), and shell options (`shopt -s expand_aliases`, `set +e`, `set +u`). Assembled in a unique temporary file (`mktemp $snapshot_path.tmp.XXXXXXXXXX`) and atomically replaced (`mv -f`) to prevent concurrent race conditions (issue #38249).
- **Command Wrapping (`_wrap_command()`, lines 911–1032)**:
  Before executing `command`, wraps it into a self-contained bash script:
  1. Sources the session snapshot (`source <snapshot_path> >/dev/null 2>&1 || true`).
  2. Exports Hermes agent harness attribution markers (`export AI_AGENT="${AI_AGENT:-hermes-agent}" HERMES_AGENT="${HERMES_AGENT:-true}"`, lines 978–980).
  3. Sets non-interactive pagers (`export GIT_PAGER="${GIT_PAGER:-cat}" PAGER="${PAGER:-cat}"`, line 989).
  4. Changes directory (`builtin cd -- <quoted_cwd> || exit 126`, line 996).
  5. Executes command (`eval '<escaped_command>'`, line 999), saving exit code `__hermes_ec=$?`.
  6. Re-exports updated environment state atomically to the snapshot file (lines 1013–1019).
  7. Emits in-band stdout CWD marker: `printf '\n__HERMES_CWD_{session_id}__%s__HERMES_CWD_{session_id}__\n' "$(pwd -P)"` (lines 1028–1029).
  8. Exits with original code: `exit $__hermes_ec`.
- **Bounded Output Collection (`_BoundedOutputCollector`, lines 82–100, 1074–1105)**:
  For foreground terminal commands, retains at most `tool_output.max_bytes` (typically 50,000 to 100,000 bytes) in a 40% head / 60% tail split. When output overflows, it tees to a disk spill file under `~/.hermes/cache/terminal-output/` capped at 5,000,000 characters (`_SPILL_CAP_CHARS`). Internal consumers leave `bounded_capture=False` for unbounded capture.
- **Process Polling & Timeout Enforcement (`_wait_for_process()`, lines 1048–1383)**:
  Non-blocking wait using `select()` polling with exponential backoff starting at 5ms up to 200ms (lines 1323–1325). Monitors `is_interrupted()` (cancels with exit code 130) and `deadline` (kills process group and returns exit code 124, lines 1286–1292). Fires gateway activity touch every 10s (`touch_activity_if_due()`, line 1295). Wraps wait in `try/finally` to guarantee process group termination on `KeyboardInterrupt` or `SystemExit` (lines 1326–1346).

#### B. Local Environment (`tools/environments/local.py`)
- **Implementation (`LocalEnvironment`, lines 1839–2050)**:
  Spawns host bash processes using `subprocess.Popen([bash, "-c", cmd_string], start_new_session=True, ...)` (lines 1994–2006).
- **Process Group Killing (`_kill_process()`, lines 2018–2050)**:
  On POSIX, stores `proc._hermes_pgid = os.getpgid(proc.pid)` and invokes `os.killpg(pgid, signal.SIGKILL)` to terminate all detached descendant processes.
- **Temp Storage (`get_temp_dir()`, lines 1858–1938)**:
  Defaults to `HERMES_HOME/cache/terminal` (real disk) rather than RAM-backed `/tmp` tmpfs. Automated hourly cache cleanup via `cleanup_terminal_temp_cache()` (lines 57–111) with 72-hour max age.
- **Windows Path Translation (`_quote_shell_path`, `_quote_cwd_for_cd`, lines 1940–1947)**:
  Translates Windows drive paths (`C:\Users\...`) to MSYS/Git-Bash paths (`/c/Users/...`) for shell execution.

#### C. Docker Environment (`tools/environments/docker.py`)
- **Security Hardening (`_BASE_SECURITY_ARGS`, lines 374–382)**:
  ```python
  _BASE_SECURITY_ARGS = [
      "--cap-drop", "ALL",
      "--cap-add", "DAC_OVERRIDE",
      "--cap-add", "CHOWN",
      "--cap-add", "FOWNER",
      "--security-opt", "no-new-privileges",
      "--tmpfs", "/tmp:rw,nosuid,size=512m",
      "--tmpfs", "/var/tmp:rw,noexec,nosuid,size=256m",
  ]
  ```
- **Shared Memory Limit for Renderers (`_DEFAULT_SHM_SIZE = "1g"`, lines 388–397)**:
  Explicitly addresses Chromium, Playwright, and media renderers crashing under Docker's default 64MB `/dev/shm`. Configurable via `terminal.docker_shm_size`.
- **PID Limit**: `--pids-limit 256` (line 386) to prevent fork bombs.
- **Filesystem Isolation & Mounts (lines 979–1121)**:
  - Persistent Mode: Mounts `<sandbox_dir>/docker/<task_id>/home` to `/root` and `<sandbox_dir>/docker/<task_id>/workspace` to `/workspace`.
  - Non-Persistent Mode: `--tmpfs /workspace:rw,exec,size=10g`, `--tmpfs /home:rw,exec,size=1g`, `--tmpfs /root:rw,exec,size=1g`.
  - Host CWD Binding: If `docker_mount_cwd_to_workspace=True`, mounts host cwd to `/workspace` (line 1041).
  - Read-Only Mounts: Credentials (`get_credential_file_mounts()`, line 1073), skills (`get_skills_directory_mount()`, line 1093), and caches (`get_cache_directory_mounts()`, line 1114) mounted `:ro`.
- **Network & Egress Proxy Isolation (lines 1125–1200)**:
  - Network disabling: `--network=none` when `docker_network=False` (line 977).
  - Egress Proxy (`iron-proxy`): Sandboxes receive PROXY tokens instead of real API keys; CA cert is mounted and `HTTPS_PROXY` / `SSL_CERT_FILE` / `NODE_OPTIONS=--use-openssl-ca` are injected.
- **Command Execution (`_run_bash()`, lines 1634–1666)**:
  Executes commands inside the container via `docker exec -i <container_id> bash -c <cmd_string>`.

#### D. Cloud Environments: Modal, Daytona, Singularity
- **Modal (`tools/environments/modal.py`, lines 164–479)**:
  Executes in native cloud sandboxes (`modal.Sandbox.create.aio("sleep", "infinity", ...)`). Commands execute via `sandbox.exec.aio("bash", "-c", cmd)`. Filesystem synchronization handled by `FileSyncManager` (lines 285–292) using tarball streaming over stdin/stdout.
- **Daytona (`tools/environments/daytona.py`, lines 30–120)**:
  Executes in cloud sandboxes via Daytona SDK (`Daytona.create(...)` or `daytona.get(...)`). Writable disk and memory resource limits enforced.
- **Singularity (`tools/environments/singularity.py`, lines 30–150)**:
  HPC container isolation with `singularity exec --containall --no-home` and writable overlay directories.

#### E. Active Environment Registry in `tools/terminal_tool.py`
- `_active_environments: Dict[str, BaseEnvironment]` (line 1145) maintains active sandbox environment instances indexed by `task_id` / `session_id`.
- `get_active_env(task_id: str) -> Optional[BaseEnvironment]` (line 2262) returns the active environment.
- `ensure_task_env(task_id: Optional[str] = None)` (line 2269) lazily instantiates and caches the container sandbox if not already active.

#### F. Sandbox File Operations (`tools/file_operations.py`)
- `ShellFileOperations(FileOperations)` (lines 926–975) routes all filesystem reads, writes, patches, and directory manipulations through `terminal_env.execute(command, cwd=...)`.
- In a containerized environment (Docker, Modal), file operations run inside the sandbox container filesystem, rather than touching the host filesystem.

---

### 1.2 Harness 9 Operations Execution Paths & Current Gaps

#### A. HyperFrames Rendering Subprocesses
- **`adapters/hyperframes/adapter.py`**:
  - `HyperFramesAdapter.compile_composition()` (lines 78–249): Assembles HTML, CSS, and GSAP timeline code and writes `index.html`, `styles.css`, and `main.js` via `atomic_write()` (lines 232–234) on the **local host filesystem**.
  - `HyperFramesAdapter.render_project()` (lines 250–280): Calls `self.renderer.render(project_dir=proj_dir, output_mp4=output_path, ...)`.
- **`src/hyperframes/renderer.py`**:
  - `HyperFramesRenderer.render()` (lines 85–181):
    - Creates local temporary directory: `with tempfile.TemporaryDirectory() as temp_frames_dir:` (line 139).
    - Writes deterministic PNG frames to local disk: `frame_file.write_bytes(frame_bytes)` (line 223).
    - Calls `render_video_with_ffmpeg(...)` (line 152).
    - If target MP4 missing or empty, generates fallback via `create_fallback_mp4()` (line 164).
    - Calls `probe_media_file(target_mp4)` (line 166) to verify stream presence and duration.
- **`src/utils/ffmpeg.py`**:
  - `is_ffmpeg_available()` (lines 23–38): Invokes host `subprocess.run([ffmpeg_path, "-version"])`.
  - `is_ffprobe_available()` (lines 41–56): Invokes host `subprocess.run([ffprobe_path, "-version"])`.
  - `probe_media_file()` (lines 80–141): Invokes host `subprocess.run(["ffprobe", ...])`.
  - `render_video_with_ffmpeg()` (lines 157–233): Executes host `subprocess.run(["ffmpeg", "-y", ...], timeout=120)` (lines 216–222).
- **Vulnerability / Boundary Violation**:
  All video encoding and media inspection execute directly as subprocesses on the host machine using Python's standard `subprocess` module. When running in a sandboxed deployment (e.g. Hermes Docker container with security drop-caps or Modal cloud sandbox), host-direct subprocess invocation violates container isolation, risks security escape, and fails if FFmpeg/Node/Chromium is installed only inside the container and not on the host.

#### B. Asset Discovery and Downloading
- **`src/assets/freezer.py`**:
  - `download_stream(url, ...)` (lines 120–167):
    Uses `urllib.request.urlopen(req, timeout=timeout_sec)` (line 136) running in the host Python process.
- **`tools/h9_content_tools.py:handle_h9_discover_assets`**:
  - Calls `bridge.discover_assets(...)` (line 237).
  - In `src/h9_runtime/bridge.py` (`discover_assets`, lines 721–780): Generates procedural SVGs using `ProceduralSVGGenerator` and writes directly to `images_dir / filename` using `file_path.write_text()` on the host disk (line 770).
- **Vulnerability / Boundary Violation**:
  Host-side `urllib.request.urlopen()` completely bypasses Docker `--network=none` isolation and bypasses the Hermes `iron-proxy` credential-scrubbing egress proxy. Furthermore, external downloaded media lands on the host filesystem rather than inside the sandbox's `/workspace` volume.

#### C. Runtime Boundary Interface (`src/h9_runtime/execution.py` & `bridge.py`)
- **`src/h9_runtime/execution.py`**:
  - `ExecutionRuntime` protocol (lines 26–56) defines `execute_command()`, `validate_path()`, `read_file()`, and `write_file()`.
  - `DefaultExecutionRuntime` (lines 59–199):
    - `validate_path()` (lines 72–88): Enforces that relative paths resolve inside `base_dir / session_id`.
    - `execute_command()` (lines 90–161): Uses `subprocess.Popen(command, cwd=effective_cwd, shell=is_shell, ...)` directly on the host machine.
    - `read_file()` and `write_file()` (lines 163–198): Use host `open()` and `tempfile.NamedTemporaryFile` with `os.replace`.
- **`src/h9_runtime/bridge.py`**:
  - `HermesCapabilityBridge` initializes `self._execution = execution_runtime or DefaultExecutionRuntime(base_dir=self.workspace_root / "sandbox")` (lines 139–141).
  - High-level methods (`render_video`, `discover_assets`, `compile_production_ir`) write files directly to `self.workspace_root` rather than delegating filesystem writes through `ExecutionRuntime` or `BaseEnvironment`.

---

## 2. Logic Chain

1. **Premise 1**: Hermes Agent's security architecture mandates that all untrusted terminal commands, untrusted script evaluations, headless browser rendering, and network communications run within sandboxed environments (`BaseEnvironment` subclasses: `DockerEnvironment`, `ModalEnvironment`, `LocalEnvironment`).
2. **Premise 2**: In `DockerEnvironment`, the container is hardened with `--cap-drop ALL`, `--security-opt no-new-privileges`, `--pids-limit 256`, `--tmpfs /tmp`, and `--shm-size 1g`. Network isolation is enforced with `--network=none` or routed through `iron-proxy`. Host paths are mounted read-only (`:ro`) except for designated `/workspace` and `/root` volumes.
3. **Premise 3**: In H9 content production, HyperFrames rendering involves:
   - Compiling HTML5 / CSS / JavaScript GSAP timeline code.
   - Headless browser rendering (Node.js / Chromium / Puppeteer / Remotion) and frame sequencing.
   - FFmpeg encoding and ffprobe stream verification.
4. **Premise 4**: Currently, H9's `DefaultExecutionRuntime.execute_command()`, `src/utils/ffmpeg.py` (`render_video_with_ffmpeg`, `probe_media_file`), and `src/assets/freezer.py` (`download_stream`) execute directly in the host OS process using Python `subprocess.Popen` and `urllib.request`.
5. **Deduction 1**: This direct host execution creates a critical sandbox boundary violation. An untrusted prompt, script, or component code could execute arbitrary shell code on the host, escape process limits, bypass network egress proxy controls, and access unauthorized host directories.
6. **Deduction 2**: To enforce strict sandbox boundaries, `src/h9_runtime/execution.py` must provide a concrete `HermesExecutionRuntime` that routes `execute_command()` through the active Hermes `BaseEnvironment` (via `get_active_env(session_id)` or `ensure_task_env(session_id)`).
7. **Deduction 3**: All H9 subprocess operations (FFmpeg video encoding, ffprobe inspection, Node/Chromium headless rendering) must be refactored to execute via `ExecutionRuntime.execute_command()`, ensuring they run inside the container (e.g. `docker exec <container_id> ffmpeg ...` or Modal `sandbox.exec.aio("ffmpeg ...")`).
8. **Deduction 4**: Filesystem paths must map consistently between host and container:
   - For Docker: The session directory `output/sessions/{session_id}` maps to `/workspace` inside the container via Docker bind mount (`-v <session_dir>:/workspace`).
   - For Modal: Assets and project directories synchronize via `FileSyncManager`.
   - For Local: Path confinement strictly prevents path traversal (`..` escaping session root) and commands execute via `LocalEnvironment.execute()` with process-group kill guarantees.
9. **Deduction 5**: Asset downloads in container mode must route through the container network stack (e.g. executing `curl` inside the container or via egress proxy) so that `--network=none` and proxy tokens are strictly respected.

---

## 3. Architecture Design: Sandbox Execution Enforcement

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                         H9 Content Production Pipeline                           │
│  h9.research │ h9.discover_assets │ h9.generate_script │ h9.render (ProductionIR)│
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                    Runtime Boundary (src/h9_runtime/bridge.py)                   │
│                               CapabilityBridge                                   │
│    _execution: ExecutionRuntime ────────► HermesExecutionRuntime (NEW)          │
└────────────────────────────────────────┬─────────────────────────────────────────┘
                                         │
                   ┌─────────────────────┴──────────────────────┐
                   │                                            │
                   ▼                                            ▼
      Path Confinement & I/O                       Command & Subprocess Execution
     validate_path(target, sid)                     execute_command(cmd, cwd, ...)
  (rejects traversal / absolute escapes)                        │
                   │                                            │
                   ▼                                            ▼
┌──────────────────────────────────────┐     ┌─────────────────────────────────────┐
│       Filesystem Sandboxing          │     │    Hermes BaseEnvironment Binding   │
│  Docker: /workspace (bind-mounted)   │◄────┤    tools/terminal_tool.py           │
│  Modal:  /root/workspace (synced)    │     │    get_active_env(session_id) /     │
│  Local:  output/sessions/{sid}       │     │    ensure_task_env(session_id)      │
└──────────────────────────────────────┘     └──────────────────┬──────────────────┘
                                                                │
                 ┌──────────────────────────────────────────────┼──────────────────────────────┐
                 │                                              │                              │
                 ▼                                              ▼                              ▼
  ┌─────────────────────────────┐                ┌─────────────────────────────┐  ┌───────────────────────────┐
  │      DockerEnvironment      │                │       ModalEnvironment      │  │     LocalEnvironment      │
  │ --cap-drop ALL              │                │ Native cloud sandbox        │  │ Host bash with            │
  │ --security-opt no-new-privs │                │ sandbox.exec.aio()          │  │ session snapshot &        │
  │ --shm-size 1g (Chromium)    │                │ FileSyncManager tarball     │  │ process-group kill (pgid) │
  │ --network=none / iron-proxy │                │ Isolated cloud container    │  │ Temp storage under        │
  │ -v <session_dir>:/workspace │                │ No host filesystem access   │  │ HERMES_HOME/cache/terminal│
  └──────────────┬──────────────┘                └──────────────┬──────────────┘  └─────────────┬─────────────┘
                 │                                              │                               │
                 └──────────────────────────────┬───────────────┴───────────────────────────────┘
                                                │
                                                ▼
                             ┌─────────────────────────────────────┐
                             │    Isolated Subprocess Execution    │
                             │  - ffmpeg -y -framerate ...         │
                             │  - ffprobe -v quiet -print_format ..│
                             │  - node / chromium (HyperFrames)    │
                             │  - curl -sSL (Asset Downloads)      │
                             └─────────────────────────────────────┘
```

### 3.1 `HermesExecutionRuntime` Implementation Design

Located in `src/h9_runtime/execution.py`:

```python
class HermesExecutionRuntime:
    """ExecutionRuntime implementation delegating to active Hermes BaseEnvironment."""

    def __init__(
        self,
        session_id: str,
        base_dir: Optional[Path] = None,
        env_type_override: Optional[str] = None,
    ) -> None:
        self.session_id = session_id
        self.base_dir = (base_dir or Path("output/sessions")).resolve()
        self.session_root = (self.base_dir / session_id).resolve()
        self.session_root.mkdir(parents=True, exist_ok=True)
        self.env_type_override = env_type_override

    def _resolve_environment(self) -> BaseEnvironment:
        """Resolve active BaseEnvironment from Hermes terminal tool registry."""
        from tools.terminal_tool import get_active_env, ensure_task_env
        env = get_active_env(self.session_id)
        if env is None:
            env = ensure_task_env(self.session_id)
        if env is None:
            # Fall back to LocalEnvironment if no container env is active
            from tools.environments.local import LocalEnvironment
            env = LocalEnvironment(cwd=str(self.session_root))
        return env

    def execute_command(
        self,
        command: Union[str, List[str]],
        cwd: Optional[Path] = None,
        timeout_seconds: float = 300.0,
        env_vars: Optional[Dict[str, str]] = None,
        session_id: Optional[str] = None,
    ) -> ExecutionResult:
        """Execute command within active BaseEnvironment (Docker, Modal, Local)."""
        env = self._resolve_environment()
        effective_cwd = str(cwd.resolve()) if cwd else str(self.session_root)
        
        # Translate command to shell string if passed as list
        if isinstance(command, list):
            import shlex
            cmd_str = " ".join(shlex.quote(str(arg)) for arg in command)
        else:
            cmd_str = command

        # If environment is containerized (Docker), translate host path to container path
        if not getattr(env, "is_local", False):
            # In Docker, host session directory is mounted at /workspace
            cmd_str = self._translate_paths_for_container(cmd_str, env)
            container_cwd = "/workspace"
        else:
            container_cwd = effective_cwd

        start_time = time.time()
        result = env.execute(
            cmd_str,
            cwd=container_cwd,
            timeout=int(timeout_seconds),
            bounded_capture=False,  # Unbounded capture for data integrity
        )
        elapsed = time.time() - start_time

        timed_out = result.get("returncode") == 124 or "[Command timed out" in result.get("output", "")
        return ExecutionResult(
            exit_code=int(result.get("returncode") or 0),
            stdout=result.get("output", ""),
            stderr=result.get("stderr", ""),
            duration_seconds=round(elapsed, 3),
            timed_out=timed_out,
        )

    def validate_path(self, target_path: Union[str, Path], session_id: Optional[str] = None) -> Path:
        """Enforce strict path confinement inside session root."""
        sid = session_id or self.session_id
        root = (self.base_dir / sid).resolve()
        candidate = Path(target_path)
        resolved = (root / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()

        try:
            resolved.relative_to(root)
        except ValueError:
            raise ValueError(f"Path traversal violation: '{target_path}' escapes session root '{root}'")
        return resolved

    def read_file(self, path: Union[str, Path], session_id: Optional[str] = None) -> str:
        env = self._resolve_environment()
        target = self.validate_path(path, session_id)
        if getattr(env, "is_local", False):
            return target.read_text(encoding="utf-8")
        # In container backend, read via BaseEnvironment / ShellFileOperations
        from tools.file_operations import ShellFileOperations
        sfo = ShellFileOperations(env, cwd="/workspace")
        rel_path = target.relative_to(self.session_root).as_posix()
        res = sfo.read_file_raw(f"/workspace/{rel_path}")
        if res.error:
            raise FileNotFoundError(f"Failed to read file from sandbox: {res.error}")
        return res.content

    def write_file(
        self,
        path: Union[str, Path],
        content: Union[str, bytes],
        session_id: Optional[str] = None,
        atomic: bool = True,
    ) -> Path:
        env = self._resolve_environment()
        target = self.validate_path(path, session_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        if getattr(env, "is_local", False):
            # Local write
            if isinstance(content, bytes):
                target.write_bytes(content)
            else:
                target.write_text(content, encoding="utf-8")
            return target
        
        # Container write via ShellFileOperations
        from tools.file_operations import ShellFileOperations
        sfo = ShellFileOperations(env, cwd="/workspace")
        rel_path = target.relative_to(self.session_root).as_posix()
        text_content = content.decode("utf-8", errors="replace") if isinstance(content, bytes) else content
        res = sfo.write_file(f"/workspace/{rel_path}", text_content)
        if res.error:
            raise IOError(f"Failed to write file into sandbox: {res.error}")
        return target
```

### 3.2 Refactoring Subprocess Execution in Rendering & FFmpeg

1. **`src/utils/ffmpeg.py`**:
   - Update `render_video_with_ffmpeg(...)` and `probe_media_file(...)` to accept an optional `execution_runtime: Optional[ExecutionRuntime] = None`.
   - When `execution_runtime` is provided:
     ```python
     # Instead of subprocess.run(cmd, ...)
     result = execution_runtime.execute_command(cmd, cwd=out_path.parent)
     if result.exit_code != 0:
         logger.warning("FFmpeg render returned error: %s", result.stderr)
     ```
   - When running in Docker, `render_video_with_ffmpeg` passes the paths relative to `/workspace` (e.g. `-i /workspace/assets/images/frame_%04d.png /workspace/renders/final.mp4`).
2. **`src/hyperframes/renderer.py`**:
   - `HyperFramesRenderer.__init__(..., execution_runtime: Optional[ExecutionRuntime] = None)`
   - When generating frames, instead of requiring host Node/Chromium, frame generation or Remotion compilation invokes `execution_runtime.execute_command(["node", "render.js", ...])`.
   - The `--shm-size 1g` in `DockerEnvironment` guarantees headless Chromium will not crash with "bus error" or "insufficient shared memory".

### 3.3 Sandboxed Asset Downloading

1. **`src/assets/freezer.py`**:
   - Update `AssetFreezer` to support sandboxed downloads via `execution_runtime`:
     ```python
     def download_stream_sandboxed(
         url: str,
         target_path: Path,
         execution_runtime: ExecutionRuntime,
         max_size_bytes: int = MAX_ASSET_SIZE_BYTES,
         timeout_sec: int = DEFAULT_DOWNLOAD_TIMEOUT,
     ) -> Tuple[Path, str, int, str]:
         # Executes curl inside the sandbox
         cmd = [
             "curl", "-sSL",
             "--max-filesize", str(max_size_bytes),
             "--max-time", str(timeout_sec),
             "-o", str(target_path),
             url,
         ]
         res = execution_runtime.execute_command(cmd)
         if res.exit_code != 0:
             raise AssetDownloadError(f"Sandboxed curl download failed: {res.stderr}")
         ...
     ```
   - In Docker with egress proxy (`iron-proxy`), `curl` inside the container automatically uses `HTTPS_PROXY` and proxy tokens, preventing credential leakage and adhering to `--network=none` or host egress policies.

---

## 4. Caveats

1. **Host-Side Mock / Offline Fallbacks**: In unit tests where Docker or Modal daemons are not running, `HermesExecutionRuntime` must cleanly degrade to `LocalEnvironment` with path confinement enabled, avoiding blocking on missing Docker engines.
2. **Path Mapping Complexity**: In Docker environments without `docker_mount_cwd_to_workspace`, paths must be translated between the host path (`output/sessions/{session_id}/...`) and the container workspace path (`/workspace/...`). Bind mounting `<session_dir>:/workspace` eliminates path copying overhead.
3. **Binary Performance**: Executing FFmpeg inside Docker incurs a minor startup overhead for `docker exec` (~50ms), but provides 100% container isolation and prevents corrupted host codecs from altering render output.
4. **Modal Tarball Synchronization**: In Modal, streaming large video files back and forth over stdin/stdout tarball sync could be bandwidth-intensive. For high-volume production, a Modal volume mount is recommended over pure stdin synchronization.

---

## 5. Conclusion

1. **Current Vulnerability**: H9 currently executes subprocesses (FFmpeg, ffprobe, node) and network asset downloads directly on the host operating system via Python `subprocess.run` and `urllib.request`. This violates Hermes sandbox architecture when running in containerized or cloud environments.
2. **Unified Abstraction Available**: Hermes provides a mature, hardened sandbox framework in `tools/environments/` (`BaseEnvironment`, `DockerEnvironment`, `ModalEnvironment`, `LocalEnvironment`) with session snapshots, output bounding, cwd tracking, process group killing, and iron-proxy egress filtering.
3. **Integration Plan**:
   - Implement `HermesExecutionRuntime` in `src/h9_runtime/execution.py` conforming to `ExecutionRuntime` protocol and delegating to `BaseEnvironment`.
   - Wire `CapabilityBridge` to instantiate and provide `HermesExecutionRuntime`.
   - Refactor `src/utils/ffmpeg.py`, `src/hyperframes/renderer.py`, and `src/assets/freezer.py` to route all subprocess and download commands through `ExecutionRuntime.execute_command()`.
   - Enforce path confinement and `/workspace` bind mounts to isolate all pipeline writes.

---

## 6. Verification Method

### 6.1 Independent Code Inspection
- Inspect `tools/environments/base.py` (lines 650–1551) to confirm `execute()`, `_wait_for_process()`, and output bounding contracts.
- Inspect `tools/environments/docker.py` (lines 374–397, 883–1050) to confirm `--cap-drop ALL`, `--shm-size 1g`, and bind-mount specifications.
- Inspect `src/h9_runtime/execution.py` (lines 59–199) and `src/utils/ffmpeg.py` (lines 157–233) to verify current direct-host subprocess invocations.

### 6.2 Unit and Conformance Tests
1. **Runtime Boundary Tests**:
   ```bash
   pytest tests/test_h9_runtime.py -v
   ```
2. **BaseEnvironment Conformance Tests**:
   ```bash
   pytest tests/tools/test_base_environment.py -v
   ```
3. **Docker Environment Security Tests**:
   ```bash
   pytest tests/tools/test_docker_environment.py -k "test_security_args or test_shm_size" -v
   ```
4. **M5 Sandbox Enforcement Tests (to be implemented)**:
   Verify `HermesExecutionRuntime` executes FFmpeg and commands inside `MockBaseEnvironment` or `DockerEnvironment`, verifying that `subprocess.Popen` is never called on the host.

### 6.3 Invalidation Conditions
- Any proposed design that introduces mid-conversation cache mutations or breaks prompt caching.
- Any implementation that attempts to run root or privileged Docker containers without `--cap-drop ALL`.
- Any design requiring new `HERMES_*` env vars for non-secret configuration (violating contribution guidelines).
