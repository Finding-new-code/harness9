# Plan — explorer_1_m5

## Objective
Investigate Hermes sandbox environment infrastructure and H9 subprocess execution, asset downloads, and filesystem writes to design sandbox enforcement for Milestone 5 (R5.1).

## Scope
1. Hermes sandbox infrastructure: `tools/environments/` (`BaseEnvironment`, `LocalEnvironment`, `DockerEnvironment`, `ModalEnvironment`, `DaytonaEnvironment`, `SingularityEnvironment`), command execution, timeout policies, directory isolation.
2. H9 subprocess & I/O operations: HyperFrames rendering (`adapters/hyperframes/`, `src/h9_runtime/execution.py`, `src/models/ir.py` compilation, node/chromium/ffmpeg subprocesses), asset downloading (`src/media/`, `tools/h9_content_tools.py`), and filesystem writes.
3. Runtime boundary interface: `src/h9_runtime/execution.py` (`ExecutionRuntime`), `src/h9_runtime/bridge.py`.
4. Sandbox integration design: How H9 operations route through `BaseEnvironment` / `ExecutionRuntime` to strictly enforce container and filesystem sandbox boundaries.

## Deliverable
Write findings to `.agents/explorer_1_m5/handoff.md`.
