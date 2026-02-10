from __future__ import annotations

import asyncio
import json
import logging
import secrets
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import AgentConfig
from .input_control import InputController
from .registry import TrustedRegistry
from .security import NonceTracker, RateLimiter

PROTOCOL_VERSION = "1.0"
PAIRING_CODE_TTL_MS = 60_000
INPUT_OR_SYSTEM_TYPES = {
    "input.mouse_move",
    "input.mouse_click",
    "input.mouse_scroll",
    "input.keypress",
    "system.media",
}


class WindowsAgentServer:
    def __init__(self, config: AgentConfig, pairing_code: str) -> None:
        self.config = config
        self.pairing_code = pairing_code
        self.registry = TrustedRegistry(config.trusted_registry_path)
        self.nonce_tracker = NonceTracker()
        self.rate_limiter = RateLimiter(config.rate_limit_per_sec)
        self.input_controller = InputController()
        self.pending_pair_requests: dict[str, dict] = {}
        self.logger = logging.getLogger("windows_agent")
        self._setup_logger(config.audit_log_path)

    def _setup_logger(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler(path, encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def _audit(self, *, device_id: str, action: str) -> None:
        ts = datetime.now(timezone.utc).isoformat()
        self.logger.info("%s device_id=%s action=%s", ts, device_id, action)

    async def _send(self, websocket: Any, *, msg_type: str, device_id: str, payload: dict) -> None:
        body = {
            "protocol_version": PROTOCOL_VERSION,
            "type": msg_type,
            "id": str(uuid.uuid4()),
            "ts": int(datetime.now(timezone.utc).timestamp() * 1000),
            "nonce": secrets.token_hex(10),
            "device_id": device_id,
            "payload": payload,
        }
        await websocket.send(json.dumps(body))

    def _validate_envelope(self, msg: dict) -> str | None:
        required = {"type", "id", "ts", "nonce", "device_id", "payload", "protocol_version"}
        missing = required - set(msg)
        if missing:
            return f"missing_fields:{','.join(sorted(missing))}"
        if msg["protocol_version"] != PROTOCOL_VERSION:
            return "unsupported_protocol_version"
        if not self.nonce_tracker.is_fresh(device_id=msg["device_id"], nonce=msg["nonce"]):
            return "invalid_or_replayed_nonce"
        if not self.rate_limiter.allow(msg["device_id"]):
            return "rate_limit_exceeded"
        return None

    def _is_trusted_for_action(self, msg: dict) -> bool:
        return self.registry.is_trusted(msg["device_id"])

    async def _handle_pair_request(self, websocket: Any, msg: dict) -> None:
        payload = msg.get("payload", {})
        if not payload.get("device_name") or not payload.get("public_key"):
            await self._send(
                websocket,
                msg_type="pair.result",
                device_id="windows-host",
                payload={"success": False, "session_token": None, "reason": "invalid_pair_request"},
            )
            return
        self.pending_pair_requests[msg["device_id"]] = payload
        await self._send(
            websocket,
            msg_type="pair.challenge",
            device_id="windows-host",
            payload={"code": self.pairing_code, "expires_in_ms": PAIRING_CODE_TTL_MS},
        )

    async def _handle_pair_confirm(self, websocket: Any, msg: dict) -> None:
        payload = msg.get("payload", {})
        device_id = msg["device_id"]
        accepted = bool(payload.get("accepted"))
        code = str(payload.get("code", ""))

        if not accepted or code != self.pairing_code:
            self._audit(device_id=device_id, action="pair_failed")
            await self._send(
                websocket,
                msg_type="pair.result",
                device_id="windows-host",
                payload={
                    "success": False,
                    "session_token": None,
                    "reason": "invalid_code_or_rejected",
                },
            )
            return

        request_payload = self.pending_pair_requests.pop(device_id, {})
        self.registry.trust_device(
            device_id=device_id,
            device_name=str(request_payload.get("device_name", "unknown")),
            public_key=str(request_payload.get("public_key", "")),
        )
        self._audit(device_id=device_id, action="pair_success")
        await self._send(
            websocket,
            msg_type="pair.result",
            device_id="windows-host",
            payload={"success": True, "session_token": secrets.token_urlsafe(24), "reason": None},
        )

    async def _handle_action(self, websocket: Any, msg: dict) -> None:
        msg_type = msg["type"]
        device_id = msg["device_id"]
        if not self._is_trusted_for_action(msg):
            await self._send(
                websocket,
                msg_type="pair.result",
                device_id="windows-host",
                payload={"success": False, "session_token": None, "reason": "device_not_trusted"},
            )
            return

        payload = msg["payload"]
        if msg_type == "input.mouse_move":
            self.input_controller.mouse_move(dx=float(payload["dx"]), dy=float(payload["dy"]))
        elif msg_type == "input.mouse_click":
            self.input_controller.mouse_click(
                button=str(payload["button"]),
                action=str(payload["action"]),
            )
        elif msg_type == "input.mouse_scroll":
            self.input_controller.mouse_scroll(
                delta_x=float(payload["delta_x"]),
                delta_y=float(payload["delta_y"]),
            )
        elif msg_type == "input.keypress":
            self.input_controller.keypress(key=str(payload["key"]), action=str(payload["action"]))
        elif msg_type == "system.media":
            self.input_controller.system_media(command=str(payload["command"]))
        else:
            await self._send(
                websocket,
                msg_type="pair.result",
                device_id="windows-host",
                payload={
                    "success": False,
                    "session_token": None,
                    "reason": "message_type_not_allowed",
                },
            )
            return

        self._audit(device_id=device_id, action=msg_type)
        await self._send(
            websocket,
            msg_type="pair.result",
            device_id="windows-host",
            payload={"success": True, "session_token": None, "reason": None},
        )

    async def handle_connection(self, websocket: Any) -> None:
        async for raw in websocket:
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue

            err = self._validate_envelope(msg)
            if err:
                await self._send(
                    websocket,
                    msg_type="pair.result",
                    device_id="windows-host",
                    payload={"success": False, "session_token": None, "reason": err},
                )
                continue

            msg_type = msg["type"]
            if msg_type == "pair.request":
                await self._handle_pair_request(websocket, msg)
            elif msg_type == "pair.confirm":
                await self._handle_pair_confirm(websocket, msg)
            elif msg_type in INPUT_OR_SYSTEM_TYPES:
                await self._handle_action(websocket, msg)
            else:
                await self._send(
                    websocket,
                    msg_type="pair.result",
                    device_id="windows-host",
                    payload={
                        "success": False,
                        "session_token": None,
                        "reason": "message_type_not_allowed",
                    },
                )

    async def run(self) -> None:
        from websockets.asyncio.server import serve

        async with serve(self.handle_connection, self.config.host, self.config.port):
            await asyncio.Future()
