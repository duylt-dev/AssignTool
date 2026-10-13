#!/usr/bin/env python3
"""Canned child process used to test scrumbot.understanding.ai_cli without a real AI."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path


def main() -> None:
    stdin = sys.stdin.read()
    record = os.environ.get("FAKE_AI_RECORD")
    if record:
        Path(record).write_text(
            json.dumps(
                {"argv": sys.argv[1:], "stdin": stdin, "cwd": str(Path.cwd()), "cwd_entries": sorted(os.listdir())},
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    mode = os.environ.get("FAKE_AI_MODE", "gemini_ok")
    reply = os.environ.get("FAKE_AI_REPLY", "[]")
    if mode == "sleep":
        time.sleep(5)
    if mode == "sleep_with_child":
        # Like gemini 0.57.0, which re-spawns itself: the grandchild must die with the timeout too.
        child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"])
        Path(os.environ["FAKE_AI_CHILD_PID"]).write_text(str(child.pid), encoding="utf-8")
        time.sleep(30)
    if mode == "exit_error":
        print(json.dumps({"error": {"message": "bad key"}}), file=sys.stderr)
        raise SystemExit(41)
    if mode == "noisy_error":
        print("Ripgrep is not available. Falling back to GrepTool.", file=sys.stderr)
        print("[STARTUP] Phase 'cleanup_ops' was started but never ended. Skipping metrics.", file=sys.stderr)
        error = {"type": "Error", "message": "Please set an Auth method", "code": 41}
        print(json.dumps({"session_id": "s", "error": error}, indent=2), file=sys.stderr)
        raise SystemExit(41)
    if mode == "nested_api_error":
        inner = json.dumps({"error": {"code": 400, "message": "API key not valid. Please pass a valid API key."}})
        outer = json.dumps({"error": {"message": inner}})
        print(
            f"Error when talking to Gemini API Full report available at: /tmp/x.json _ApiError: {outer}",
            file=sys.stderr,
        )
        raise SystemExit(144)
    if mode == "agy_status_error":
        print(json.dumps({"status": "ERROR"}))
        return
    if mode == "not_json":
        print("not json")
        return
    if mode == "error_object":
        print(json.dumps({"error": {"message": "model issue"}}))
        return
    if mode == "no_response":
        print(json.dumps({"status": "SUCCESS"}))
        return
    if mode == "fenced":
        reply = f"Prose\n```json\n{reply}\n```\nDone"
    if mode == "agy_ok":
        print(json.dumps({"status": "SUCCESS", "response": reply}))
        return
    print(json.dumps({"response": reply}))


if __name__ == "__main__":
    main()
