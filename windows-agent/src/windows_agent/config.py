from __future__ import annotations

import argparse
import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_PORT = 8765
DEFAULT_RATE_LIMIT_PER_SEC = 30


@dataclass(slots=True)
class AgentConfig:
    host: str = "0.0.0.0"
    port: int = DEFAULT_PORT
    trusted_registry_path: Path = Path("trusted_devices.json")
    audit_log_path: Path = Path("audit.log")
    rate_limit_per_sec: int = DEFAULT_RATE_LIMIT_PER_SEC
    show_pairing_window: bool = True


def parse_args() -> AgentConfig:
    parser = argparse.ArgumentParser(description="Remote Brain Builder Windows agent")
    parser.add_argument("--host", default=os.getenv("WINDOWS_AGENT_HOST", "0.0.0.0"))
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("WINDOWS_AGENT_PORT", str(DEFAULT_PORT))),
    )
    parser.add_argument(
        "--trusted-registry",
        type=Path,
        default=Path(os.getenv("WINDOWS_AGENT_TRUSTED_REGISTRY", "trusted_devices.json")),
    )
    parser.add_argument(
        "--audit-log",
        type=Path,
        default=Path(os.getenv("WINDOWS_AGENT_AUDIT_LOG", "audit.log")),
    )
    parser.add_argument(
        "--rate-limit-per-sec",
        type=int,
        default=int(os.getenv("WINDOWS_AGENT_RATE_LIMIT", str(DEFAULT_RATE_LIMIT_PER_SEC))),
    )
    parser.add_argument(
        "--no-pairing-window",
        action="store_true",
        help="Disable tkinter pairing window (useful for headless testing).",
    )

    args = parser.parse_args()
    return AgentConfig(
        host=args.host,
        port=args.port,
        trusted_registry_path=args.trusted_registry,
        audit_log_path=args.audit_log,
        rate_limit_per_sec=max(1, args.rate_limit_per_sec),
        show_pairing_window=not args.no_pairing_window,
    )
