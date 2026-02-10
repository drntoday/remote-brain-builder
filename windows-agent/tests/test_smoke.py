from windows_agent import __version__


def test_smoke() -> None:
    assert __version__ == "0.1.0"
