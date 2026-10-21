#!/usr/bin/env python3
"""Hermes → Claude Code transcript adapter.

Membaca log Hermes secara real-time (tail -f) di VPS, parse setiap baris
menggunakkan parser yang ada di backend/app/hermes_adapter.py, lalu tulis
JSONL records dalam format Claude Code ke ~/.claude/projects/<project>/<sessionId>.jsonl.

Usage:
    python scripts/hermes_to_claude_transcript.py [--log PATH] [--project NAME]

Env:
    HERMES_LOG_PATH   path ke hermes agent.log (default: ~/.hermes/logs/agent.log)
    CLAUDE_PROJECT    project dir name (default: -home-bang-hermes-office)
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Pastikan backend/app dapat diimpor (parser yang sudah ada)
# Coba beberapa lokasi: project dir, VPS path, env var
_SCRIPT_DIR = Path(__file__).resolve().parent
_POSSIBLE_PATHS = [
    _SCRIPT_DIR.parent / "backend" / "app",                           # project/scripts/../backend/app
    Path.home() / "projects" / "bang-heri-pixel-office" / "backend" / "app",  # default project
    Path(os.environ.get("HERMES_ADAPTER_PATH", "")),                 # env override
]
_BACKEND_APP = None
for p in _POSSIBLE_PATHS:
    if p and (p / "hermes_adapter.py").exists():
        _BACKEND_APP = p
        break
if _BACKEND_APP is None:
    print("[ERROR] hermes_adapter.py not found. Set HERMES_ADAPTER_PATH or run from project.", file=sys.stderr)
    sys.exit(1)
if str(_BACKEND_APP) not in sys.path:
    sys.path.insert(0, str(_BACKEND_APP))

from hermes_adapter import parse_log_line  # noqa: E402


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _default_log_path() -> str:
    return os.environ.get("HERMES_LOG_PATH", str(Path.home() / ".hermes" / "logs" / "agent.log"))


def _default_project_dir() -> str:
    return os.environ.get("CLAUDE_PROJECT", "-home-bang-hermes-office")


# ---------------------------------------------------------------------------
# Claude Code record builder
# ---------------------------------------------------------------------------

def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_uuid() -> str:
    return str(uuid.uuid4())


def _usage() -> dict:
    return {
        "input_tokens": 100,
        "cache_creation_input_tokens": 0,
        "cache_read_input_tokens": 0,
        "output_tokens": 50,
    }


def build_assistant_record(
    ev: dict,
    prev_uuid: str | None,
    session_id: str,
) -> dict:
    """Buat assistant record dengan tool_use (action=working) atau text (action=moving)."""
    action = ev.get("action", "idle")
    message = ev.get("message", "")

    if action == "working":
        content = [{
            "type": "tool_use",
            "id": _new_uuid(),
            "name": "bash",
            "input": {"command": message},
        }]
    elif action == "moving":
        content = [{"type": "text", "text": message}]
    else:
        # idle → handled by caller as user record instead
        content = [{"type": "text", "text": message}]

    return {
        "type": "assistant",
        "uuid": _new_uuid(),
        "parentUuid": prev_uuid,
        "timestamp": ev.get("timestamp") or _iso_now(),
        "sessionId": session_id,
        "isSidechain": False,
        "message": {
            "role": "assistant",
            "content": content,
            "usage": _usage(),
            "model": "claude-sonnet-4-6",
        },
    }


def build_user_record(
    ev: dict,
    prev_uuid: str | None,
    session_id: str,
) -> dict:
    """Buat user record dengan tool_result (action=idle)."""
    return {
        "type": "user",
        "uuid": _new_uuid(),
        "parentUuid": prev_uuid,
        "timestamp": ev.get("timestamp") or _iso_now(),
        "sessionId": session_id,
        "isSidechain": False,
        "message": {
            "role": "user",
            "content": [{
                "type": "tool_result",
                "tool_use_id": _new_uuid(),
                "content": "done",
            }],
        },
    }


# ---------------------------------------------------------------------------
# Tail -f via subprocess
# ---------------------------------------------------------------------------

def tail_follow(path: str):
    """Yield baris baru dari file log secara real-time (tail -f)."""
    proc = subprocess.Popen(
        ["tail", "-n", "0", "-f", path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )
    try:
        assert proc.stdout is not None
        for line in proc.stdout:
            yield line.rstrip("\n")
    finally:
        proc.terminate()
        proc.wait()


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Hermes → Claude Code transcript adapter", allow_abbrev=False)
    parser.add_argument("--log", default=_default_log_path(), help="Path ke hermes agent.log")
    parser.add_argument("--project", default=_default_project_dir(), help="Claude Code project dir name")
    parser.add_argument("--once", action="store_true", help="Baca sekali lalu keluar ( untuk testing )")
    args = parser.parse_args()
    if args.project.startswith("-"):
        args.project = args.project[1:]

    log_path = Path(args.log)
    if not log_path.exists():
        print(f"[ERROR] Log file tidak ditemukan: {log_path}", file=sys.stderr)
        sys.exit(1)

    out_dir = Path.home() / ".claude" / "projects" / args.project
    out_dir.mkdir(parents=True, exist_ok=True)

    # Satu file per agentId → filename = <agentId>.jsonl
    file_handles: dict[str, object] = {}
    prev_uuids: dict[str, str | None] = {}

    print(f"[adapter] Watching {log_path}", file=sys.stderr)
    print(f"[adapter] Output dir: {out_dir}", file=sys.stderr)

    def handle_line(raw: str) -> None:
        ev = parse_log_line(raw)
        if ev is None:
            return

        agent_id = ev["agentId"]
        action = ev["action"]
        session_id = agent_id

        if agent_id not in file_handles:
            out_path = out_dir / f"{agent_id}.jsonl"
            file_handles[agent_id] = open(out_path, "a", encoding="utf-8")
            prev_uuids[agent_id] = None
            print(f"[adapter] Opened {out_path}", file=sys.stderr)

        fh = file_handles[agent_id]
        prev = prev_uuids.get(agent_id)

        if action == "idle":
            record = build_user_record(ev, prev, session_id)
        else:
            record = build_assistant_record(ev, prev, session_id)

        prev_uuids[agent_id] = record["uuid"]

        line_json = json.dumps(record, ensure_ascii=False)
        fh.write(line_json + "\n")
        fh.flush()

    if args.once:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            for raw in f:
                handle_line(raw)
    else:
        for raw in tail_follow(str(log_path)):
            handle_line(raw)


if __name__ == "__main__":
    main()