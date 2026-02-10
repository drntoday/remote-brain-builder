# Threat Model (Milestone 0)

## Security Assumptions
- Initial deployment targets **local LAN only** connectivity.
- Any control session requires an explicit **pairing required** flow.
- Access is restricted to entries in a **trusted device registry**.
- Remote actions use an **allowlist-only commands** policy.
- Every security-sensitive action is recorded in an **audit log**.

## Primary Threats
- Unauthorized device attempts to initiate a control session.
- Spoofed messages from unpaired or untrusted devices.
- Privilege escalation through unrestricted command execution.
- Replay attempts against old pairing/session artifacts.
- Local network eavesdropping before full transport hardening is in place.

## Mitigation Direction (Planned)
- Strong pairing handshake with per-device identity material.
- Strict policy checks before any command or action is accepted.
- Command allowlist reviewed and version-controlled.
- Tamper-evident audit log entries with clear actor attribution.
- Security review gate before expanding beyond LAN scope.
