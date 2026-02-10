from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class TrustedDevice:
    device_id: str
    device_name: str
    public_key: str


class TrustedRegistry:
    def __init__(self, path: Path) -> None:
        self.path = path
        self._devices: dict[str, TrustedDevice] = {}
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self._devices = {}
            return

        raw = json.loads(self.path.read_text(encoding="utf-8"))
        trusted = raw.get("trusted_devices", [])
        self._devices = {
            item["device_id"]: TrustedDevice(
                device_id=item["device_id"],
                device_name=item.get("device_name", "unknown"),
                public_key=item.get("public_key", ""),
            )
            for item in trusted
            if "device_id" in item
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "trusted_devices": [
                {
                    "device_id": d.device_id,
                    "device_name": d.device_name,
                    "public_key": d.public_key,
                }
                for d in self._devices.values()
            ]
        }
        self.path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def is_trusted(self, device_id: str) -> bool:
        return device_id in self._devices

    def trust_device(self, *, device_id: str, device_name: str, public_key: str) -> None:
        self._devices[device_id] = TrustedDevice(
            device_id=device_id,
            device_name=device_name,
            public_key=public_key,
        )
        self.save()
