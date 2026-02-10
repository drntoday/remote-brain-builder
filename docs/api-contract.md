# API Contract (Milestone 0 Draft)

## Contract Principles
- API is intentionally draft-only during milestone 0.
- Message formats will be centrally defined in `shared/protocol/`.
- Versioning must be explicit to support forward migration.
- All operations should be request/response or event-driven with typed payloads.
- Breaking changes require a documented migration note.

## Planned Surfaces
- Session lifecycle operations (connect, authenticate, disconnect).
- Pairing and trust management operations.
- Read-only status/health query operations.
- Controlled remote action operations gated by allowlist.
- Audit event streaming operations for traceability.

## Deferred Until Later Milestones
- Final wire protocol selection and framing.
- Retry semantics and backoff policy.
- Error code catalog and localization strategy.
- Performance SLAs and message size thresholds.
- Backward-compatibility matrix across client versions.
