# Plan — explorer_2_m5

## Objective
Investigate principle-of-least-privilege capability token permission engine and tool gating for Milestone 5 (R5.2).

## Scope
1. Capability token architecture: `src/security/` (capability token format, intersection rule `child_permission = parent ∩ role ∩ workflow`, revocation, scope hierarchies).
2. Hermes tool gating & permissions: How Hermes and `tools/registry.py` enforce tool invocation permissions, session permissions, and role restrictions.
3. H9 tool permission enforcement: How unauthorized scopes are blocked from calling sensitive H9 tools (e.g. `h9.render`, `h9.publish`, `h9.generate_script`).
4. Permission guard design: Integrating capability token checks into `tools/h9_content_tools.py`, `src/h9_runtime/bridge.py`, and `src/h9_runtime/agent.py`.

## Deliverable
Write findings to `.agents/explorer_2_m5/handoff.md`.
