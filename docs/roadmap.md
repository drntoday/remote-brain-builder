# Roadmap

## Milestone 0 — Repository Foundations
- Create repository skeleton and baseline documentation.
- Stand up Python package for `windows-agent` with src layout.
- Add CI for lint (`ruff`) and tests (`pytest`).
- Define initial architecture and API contract drafts.
- Record first-pass threat model assumptions.

## Milestone 1 — Pairing and Session Basics
- Implement device pairing workflow and trust establishment.
- Add trusted device registry persistence model.
- Define session lifecycle primitives and state machine.
- Add structured logging and baseline audit events.
- Expand tests for pairing/session edge cases.

## Milestone 2 — Controlled Remote Actions
- Implement allowlist-gated remote command/action handling.
- Add policy enforcement and deny-by-default behavior.
- Expand protocol schemas for action request/response.
- Introduce richer telemetry for observability.
- Run threat-model refresh against implemented flows.
