from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path


class StaticUIHTTPServer:
    def __init__(
        self,
        *,
        host: str,
        port: int,
        static_dir: Path,
    ) -> None:
        self.host = host
        self.port = port
        self.static_dir = static_dir

    async def _send_response(
        self,
        writer: asyncio.StreamWriter,
        *,
        status: str,
        content_type: str,
        body: bytes,
    ) -> None:
        writer.write(
            (
                f"HTTP/1.1 {status}\r\n"
                f"Content-Type: {content_type}\r\n"
                f"Content-Length: {len(body)}\r\n"
                "Cache-Control: no-store\r\n"
                "X-Content-Type-Options: nosniff\r\n"
                "Connection: close\r\n\r\n"
            ).encode()
            + body
        )
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    async def _handle_client(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ) -> None:
        try:
            request_line = await reader.readline()
            if not request_line:
                writer.close()
                await writer.wait_closed()
                return

            try:
                method, target, _ = request_line.decode("utf-8").strip().split(" ", maxsplit=2)
            except ValueError:
                await self._send_response(
                    writer,
                    status="400 Bad Request",
                    content_type="text/plain; charset=utf-8",
                    body=b"bad request",
                )
                return

            # Drain headers without processing; this is a tiny static server.
            while True:
                line = await reader.readline()
                if line in (b"\r\n", b"\n", b""):
                    break

            if method != "GET":
                await self._send_response(
                    writer,
                    status="405 Method Not Allowed",
                    content_type="text/plain; charset=utf-8",
                    body=b"method not allowed",
                )
                return

            if target in ("/", "/index.html"):
                file_path = self.static_dir / "index.html"
                content_type = "text/html; charset=utf-8"
            elif target == "/app.js":
                file_path = self.static_dir / "app.js"
                content_type = "application/javascript; charset=utf-8"
            else:
                await self._send_response(
                    writer,
                    status="404 Not Found",
                    content_type="text/plain; charset=utf-8",
                    body=b"not found",
                )
                return

            body = file_path.read_bytes()
            await self._send_response(
                writer,
                status="200 OK",
                content_type=content_type,
                body=body,
            )
        except Exception:
            writer.close()
            await writer.wait_closed()

    async def run(self) -> None:
        server = await asyncio.start_server(self._handle_client, self.host, self.port)
        async with server:
            await server.serve_forever()


async def run_services(*services: Callable[[], Awaitable[None]]) -> None:
    tasks = [asyncio.create_task(service()) for service in services]
    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    for task in pending:
        task.cancel()
    for task in done:
        task.result()
