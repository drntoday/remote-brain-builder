from pathlib import Path

from windows_agent.registry import TrustedRegistry


def test_registry_read_write(tmp_path: Path) -> None:
    registry_path = tmp_path / "trusted_devices.json"
    registry = TrustedRegistry(registry_path)

    registry.trust_device(device_id="dev-1", device_name="Pixel", public_key="pk")

    reloaded = TrustedRegistry(registry_path)
    assert reloaded.is_trusted("dev-1")
