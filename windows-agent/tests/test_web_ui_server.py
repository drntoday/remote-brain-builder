import asyncio
from pathlib import Path

from windows_agent.web_ui_server import StaticUIHTTPServer


async def _http_get(port: int, path: str) -> bytes:
    reader, writer = await asyncio.open_connection("127.0.0.1", port)
    writer.write(f"GET {path} HTTP/1.1\r\nHost: localhost\r\n\r\n".encode())
    await writer.drain()
    data = await reader.read()
    writer.close()
    await writer.wait_closed()
    return data


def test_static_server_serves_index(tmp_path: Path) -> None:
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<h1>ok</h1>", encoding="utf-8")
    (static_dir / "app.js").write_text("console.log('ok')", encoding="utf-8")

    async def run_test() -> None:
        server = StaticUIHTTPServer(host="127.0.0.1", port=9080, static_dir=static_dir)
        task = asyncio.create_task(server.run())
        await asyncio.sleep(0.05)
        try:
            response = await _http_get(9080, "/")
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        assert b"200 OK" in response
        assert b"<h1>ok</h1>" in response

    asyncio.run(run_test())


def test_static_server_404(tmp_path: Path) -> None:
    static_dir = tmp_path / "static"
    static_dir.mkdir()
    (static_dir / "index.html").write_text("<h1>ok</h1>", encoding="utf-8")
    (static_dir / "app.js").write_text("console.log('ok')", encoding="utf-8")

    async def run_test() -> None:
        server = StaticUIHTTPServer(host="127.0.0.1", port=9081, static_dir=static_dir)
        task = asyncio.create_task(server.run())
        await asyncio.sleep(0.05)
        try:
            response = await _http_get(9081, "/missing")
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        assert b"404 Not Found" in response

    asyncio.run(run_test())
