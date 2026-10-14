"""The HTTP client against a real local HTTP server (bot spec §2.2, A55): headers, pages, batches, retries and every
error message. No mock of urllib: the bytes cross a real socket, as they do with the dev server."""

from __future__ import annotations

import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import pytest

from scrumbot import __version__
from scrumbot.input.dev_api.client import ApiClient, ApiError
from scrumbot.input.dev_api.config import ApiConfig

TOKEN = "secret-token-123"


class Server:
    """Serves queued (status, body) replies per path and records every request."""

    def __init__(self) -> None:
        self.replies: dict[str, list[tuple[int, bytes]]] = {}
        self.requests: list[tuple[str, dict[str, list[str]], dict[str, str]]] = []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self) -> None:  # noqa: N802 - http.server API
                parsed = urlparse(self.path)
                server.requests.append((parsed.path, parse_qs(parsed.query), dict(self.headers)))
                queue = server.replies.get(parsed.path, [])
                status, body = queue.pop(0) if len(queue) > 1 else (queue[0] if queue else (404, b"{}"))
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, *_: object) -> None:
                return

        self.httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"
        self.thread = threading.Thread(target=self.httpd.serve_forever, kwargs={"poll_interval": 0.05}, daemon=True)
        self.thread.start()

    def reply(self, path: str, *replies: tuple[int, object]) -> None:
        self.replies[f"/api/doc/{path}"] = [
            (status, body if isinstance(body, bytes) else json.dumps(body).encode()) for status, body in replies
        ]


@pytest.fixture
def server() -> Iterator[Server]:
    running = Server()
    yield running
    running.httpd.shutdown()


def _client(server: Server, sleeps: list[float] | None = None) -> ApiClient:
    return ApiClient(ApiConfig(server.base, TOKEN), sleep=(sleeps if sleeps is not None else []).append)


def test_every_call_sends_the_token_and_a_user_agent(server: Server) -> None:
    server.reply("sprints", (200, {"ok": True, "sprints": []}))

    assert _client(server).sprints("90169740714") == {"ok": True, "sprints": []}

    path, query, headers = server.requests[0]
    assert (path, query) == ("/api/doc/sprints", {"folder_id": ["90169740714"]})
    assert headers["Authorization"] == f"Bearer {TOKEN}"
    assert headers["User-Agent"] == f"scrumbot/{__version__}"


def test_orders_reads_every_page_and_merges_the_lookup_tables(server: Server) -> None:
    page = {"ok": True, "goc_moi_trang": 1, "tong_goc": 2}
    server.reply(
        "don",
        (200, {**page, "trang": 1, "don": [{"id": "a"}], "trang_thai": [{"id": 1}], "nguoi": [{"id": 7}]}),
        (200, {**page, "trang": 2, "don": [{"id": "b"}], "trang_thai": [{"id": 1}, {"id": 2}], "nguoi": []}),
    )

    merged = _client(server).orders("L1")

    assert [item["id"] for item in merged["don"]] == ["a", "b"]
    assert [item["id"] for item in merged["trang_thai"]] == [1, 2]
    assert [request[1]["trang"] for request in server.requests] == [["1"], ["2"]]


def test_history_is_read_in_batches_of_fifty(server: Server) -> None:
    server.reply("lich-su", (200, {"ok": True, "doi_trang_thai": [{"task_id": "x"}], "comment": [], "nguoi": []}))
    ids = [f"t{index}" for index in range(120)]

    merged = _client(server).history(ids)

    assert [len(request[1]["task_id"][0].split(",")) for request in server.requests] == [50, 50, 20]
    assert merged == {"doi_trang_thai": [{"task_id": "x"}] * 3}


def test_429_waits_and_retries_then_succeeds(server: Server) -> None:
    sleeps: list[float] = []
    server.reply("sprints", (429, {"ok": False}), (429, {"ok": False}), (200, {"ok": True, "sprints": []}))

    assert _client(server, sleeps).sprints("f") == {"ok": True, "sprints": []}
    assert sleeps == [30, 30]


@pytest.mark.parametrize(
    ("status", "message"),
    [
        (401, "API từ chối token (401). Kiểm tra SCRUMBOT_API_TOKEN, hoặc xin TM token mới."),
        (404, "API trả 404 cho sprints: API đang tắt trên server hoặc id không còn trong phạm vi."),
        (429, "API vẫn giới hạn tải (429) sau 3 lần thử; chạy lại sau ít phút."),
        (500, "API lỗi phía server (500) ở sprints; thử lại sau."),
        (418, "API trả mã 418 ở sprints."),
    ],
)
def test_http_errors_stop_with_a_vietnamese_message_and_never_the_token(
    server: Server, status: int, message: str
) -> None:
    server.reply("sprints", (status, {"ok": False}))
    sleeps: list[float] = []

    with pytest.raises(ApiError) as caught:
        _client(server, sleeps).sprints("f")

    assert str(caught.value) == message and TOKEN not in str(caught.value)
    assert sleeps == ([30, 30, 30] if status == 429 else [])


def test_a_reply_that_is_not_json_or_says_ok_false_is_unreadable(server: Server) -> None:
    server.reply("sprints", (200, b"<html>"))
    with pytest.raises(ApiError, match="API trả dữ liệu không đọc được ở sprints."):
        _client(server).sprints("f")
    server.reply("don", (200, {"ok": False}))
    with pytest.raises(ApiError, match="API trả dữ liệu không đọc được ở don."):
        _client(server).orders("L")


def test_a_closed_port_is_a_network_error_naming_the_host() -> None:
    client = ApiClient(ApiConfig("http://127.0.0.1:9", TOKEN))

    with pytest.raises(ApiError, match=r"^Không gọi được API 127\.0\.0\.1: "):
        client.sprints("f")
