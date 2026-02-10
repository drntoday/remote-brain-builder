# Architecture (Milestone 0)

## Scope
- Establish repository and package structure for cross-platform components.
- Define a standalone `windows-agent` Python package using src layout.
- Keep architecture intentionally minimal until protocol and networking design is approved.
- Prioritize clear boundaries between agent, Android client, and shared protocol artifacts.
- Align implementation order with roadmap milestones.

## Initial Component Map
- `windows-agent/` hosts Python code, tests, and lint configuration.
- `shared/protocol/` will hold message definitions and schema evolution notes.
- `android-client/` remains a separate client implementation track.
- `docs/` contains architecture, API contract, threat model, and roadmap.
- CI validates quality gates for the Python package (lint + tests).

## Non-Goals for This Milestone
- No networking stack implementation.
- No command execution or input control logic.
- No persistence layer beyond placeholder documentation.
- No device pairing workflow implementation yet.
- No transport security implementation yet.
