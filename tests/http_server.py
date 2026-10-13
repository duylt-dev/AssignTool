"""A real local HTTP server that answers `/api/doc/` from a dict the test can change between runs."""

from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


class FakeDevServer:
    """`data` = {"sprints": reply, "don": {list_id: reply}, "lich-su": reply}; `requests` lists the paths asked."""

    def __init__(self, data: dict[str, object]) -> None:
        self.data = data
        self.requests: list[str] = []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - http.server API
                parsed = urlparse(self.path)
                query = parse_qs(parsed.query)
                server.requests.append(parsed.path)
                name = parsed.path.removeprefix("/api/doc/")
                if self.headers.get("Authorization") != "Bearer test-token":
                    status, body = 401, {"ok": False}
                elif name == "don":
                    reply = server.data["don"].get(query.get("list_id", [""])[0])  # type: ignore[union-attr]
                    status, body = (200, reply) if reply is not None else (404, {"ok": False})
                elif name in ("sprints", "lich-su"):
                    status, body = 200, server.data[name]
                else:
                    status, body = 404, {"detail": "Not Found"}
                payload = json.dumps(body, ensure_ascii=False).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(payload)

            def log_message(self, *_: object) -> None:
                return

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True).start()

    def close(self) -> None:
        self.httpd.shutdown()
