from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import pytest

from assigntool.ai_cli import run_ai

_FAKE = Path(__file__).with_name("fake_ai.py")
_COMMAND = (sys.executable, str(_FAKE))


def _run(monkeypatch, *, tool: str = "gemini", mode: str = "gemini_ok", **kwargs):
    monkeypatch.setenv("FAKE_AI_MODE", mode)
    timeout = kwargs.pop("timeout", 2)
    return run_ai(tool, "private prompt", model="test-model", timeout=timeout, command=_COMMAND, **kwargs)


def test_run_ai_reads_gemini_response_and_uses_empty_temp_cwd_and_stdin(monkeypatch, tmp_path) -> None:
    record = tmp_path / "record.json"
    monkeypatch.setenv("FAKE_AI_RECORD", str(record))

    reply = _run(monkeypatch)
    captured = json.loads(record.read_text(encoding="utf-8"))

    assert reply.text == "[]" and reply.failure is None
    assert captured["stdin"] == "private prompt"
    assert captured["argv"] == ["-p", "", "-o", "json", "--approval-mode", "plan", "--skip-trust", "-m", "test-model"]
    assert captured["cwd"] != str(Path.cwd())
    assert captured["cwd_entries"] == []


def test_run_ai_reads_agy_response_and_passes_prompt_as_argument(monkeypatch) -> None:
    reply = _run(monkeypatch, tool="agy", mode="agy_ok")

    assert reply.text == "[]" and reply.failure is None


def test_run_ai_records_agy_prompt_as_argument(monkeypatch, tmp_path) -> None:
    record = tmp_path / "agy.json"
    monkeypatch.setenv("FAKE_AI_RECORD", str(record))

    _run(monkeypatch, tool="agy", mode="agy_ok")

    captured = json.loads(record.read_text(encoding="utf-8"))
    assert captured["stdin"] == ""
    assert captured["argv"][captured["argv"].index("-p") + 1] == "private prompt"
    assert "--model" in captured["argv"]


def test_run_ai_handles_all_child_failures(monkeypatch, tmp_path) -> None:
    assert _run(monkeypatch, mode="exit_error").failure == "mã thoát 41: bad key"
    assert _run(monkeypatch, mode="noisy_error").failure == "mã thoát 41: Please set an Auth method"
    assert _run(monkeypatch, mode="nested_api_error").failure == (
        "mã thoát 144: API key not valid. Please pass a valid API key."
    )
    assert _run(monkeypatch, tool="agy", mode="agy_status_error").failure == "trạng thái ERROR"
    assert _run(monkeypatch, mode="not_json").failure == "kết quả không phải JSON"
    assert _run(monkeypatch, mode="error_object").failure == "lỗi: model issue"
    assert _run(monkeypatch, mode="no_response").failure == "không có trường response"
    assert _run(monkeypatch, mode="sleep", timeout=1).failure == "hết thời gian 1s"
    assert run_ai("gemini", "x", model=None, timeout=1, command=(str(tmp_path / "missing"),)).failure.startswith(
        "không chạy được gemini:"
    )


def test_run_ai_handles_envelope_error_and_fenced_response(monkeypatch) -> None:
    monkeypatch.setenv("FAKE_AI_REPLY", '[{"stt": 1, "size": "M"}]')
    reply = _run(monkeypatch, mode="fenced")

    assert reply.failure is None
    assert reply.text == 'Prose\n```json\n[{"stt": 1, "size": "M"}]\n```\nDone'


def test_run_ai_rejects_missing_tool_and_agy_batch_file() -> None:
    assert run_ai("does-not-exist", "x", model=None, timeout=1).failure == "không tìm thấy does-not-exist"
    assert run_ai("agy", "x", model=None, timeout=1, command=("agy.cmd",)).failure == (
        "agy là file .cmd/.bat; không truyền prompt qua tham số"
    )


@pytest.mark.skipif(os.name == "nt", reason="dùng os.kill(pid, 0) để dò tiến trình; nhánh Windows dùng taskkill /T")
def test_timeout_also_kills_the_childs_own_children(monkeypatch, tmp_path) -> None:
    pid_file = tmp_path / "child.pid"
    monkeypatch.setenv("FAKE_AI_CHILD_PID", str(pid_file))

    assert _run(monkeypatch, mode="sleep_with_child", timeout=1).failure == "hết thời gian 1s"

    grandchild = int(pid_file.read_text(encoding="utf-8"))
    deadline = time.monotonic() + 5
    while _alive(grandchild) and time.monotonic() < deadline:
        time.sleep(0.05)
    assert not _alive(grandchild)


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    return True
