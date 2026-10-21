#!/usr/bin/env python3
"""Hermes → Claude Code transcript adapter.

Membaca log Hermes secara real-time (tail -f) di VPS, parse setiap baris
lalu tulis JSONL records dalam format Claude Code ke
~/.claude/projects/<project>/<agentId>.jsonl.

Parser (v1.2) menangani format log Hermes yang nyata:

    INFO [cron_72d65950ce86_20261021_060045] agent.conversation_loop: ...
    INFO [cron_72d65950ce86_20261021_060045] agent.tool_executor: tool web_search completed
    INFO __main__: Job 'Riset Konten' completed successfully
    INFO cron.scheduler: Job '72d65950ce86': delivered to telegram: ...

Usage:
    python scripts/hermes_to_claude_transcript.py [--log PATH] [--project NAME]
    python scripts/hermes_to_claude_transcript.py --self-test

Env:
    HERMES_LOG_PATH   path ke hermes agent.log (default: ~/.hermes/logs/agent.log)
    CLAUDE_PROJECT    project dir name (default: -home-bang-hermes-office)
    HERMES_ADAPTER_PATH  path folder berisi hermes_adapter.py (opsional)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Import parser lama (opsional)
# ---------------------------------------------------------------------------
# Parser format-real (lihat PARSER HERMES AKTUAL di bawah) bersifat mandiri,
# jadi script tetap jalan di VPS Even tanpa backend/app/hermes_adapter.py.
# Import hanya dipakai sebagai fallback untuk pola log lama.
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
if _BACKEND_APP is not None and str(_BACKEND_APP) not in sys.path:
    sys.path.insert(0, str(_BACKEND_APP))

try:
    from hermes_adapter import parse_log_line as _legacy_parse_log_line  # noqa: E402
except Exception:  # pragma: no cover - adapter lama tidak wajib ada
    _legacy_parse_log_line = None
    if _BACKEND_APP is None:
        print(
            "[WARN] hermes_adapter.py tidak ditemukan — memakai parser log-real saja. "
            "Set HERMES_ADAPTER_PATH untuk mengaktifkan fallback pola lama.",
            file=sys.stderr,
        )


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

def _default_log_path() -> str:
    return os.environ.get("HERMES_LOG_PATH", str(Path.home() / ".hermes" / "logs" / "agent.log"))


def _default_project_dir() -> str:
    return os.environ.get("CLAUDE_PROJECT", "-home-bang-hermes-office")


# ---------------------------------------------------------------------------
# PARSER HERMES AKTUAL (format log VPS terbaru)
# ---------------------------------------------------------------------------

# 1. Tag cron: [cron_<job_id>_<YYYYMMDD>_<HHMMSS>]  →  job_id = 72d65950ce86
CRON_TAG_RE = re.compile(r"\[cron_(?P<job_id>[0-9a-z]{6,})(?:_[0-9]+)*\]", re.IGNORECASE)

# 2. Nama job: Job 'Riset Konten'  /  Job '72d65950ce86'
JOB_NAME_RE = re.compile(r"Job\s+['\"](?P<name>[^'\"]+)['\"]", re.IGNORECASE)

# 3. Job selesai: Job 'Riset Konten' completed successfully
JOB_COMPLETED_RE = re.compile(r"Job\s+['\"]?(?P<name>[^'\"\n]+?)['\"]?\s+completed", re.IGNORECASE)

# 4. Tool selesai: agent.tool_executor: tool web_search completed
TOOL_COMPLETED_RE = re.compile(r"\btool\s+(?P<tool>[a-zA-Z][\w.\-]*)\s+completed", re.IGNORECASE)

# 5. Panggilan API: "API call #3"
API_CALL_RE = re.compile(r"API\s*call\s*#(?P<n>\d+)", re.IGNORECASE)

# 6. Pengiriman laporan: Job '72d65950ce86': delivered to telegram: <teks>
DELIVERED_RE = re.compile(r"delivered\s+to\s+telegram", re.IGNORECASE)

# 6b. Tag agen eksplisit di dalam log (mis. msg='... invoked the "agen-content" skill')
AGENT_TAG_RE = re.compile(
    r"(agen-bangheri|agen-inbox|agen-content|agen-pm|agen-admin)", re.IGNORECASE
)

# 6c. Selesai satu turn agent: "Turn ended: reason=text_response(...)"
TURN_ENDED_RE = re.compile(r"Turn\s+ended", re.IGNORECASE)

# 6d. Baris log yang menandai aktivitas agen (dipakai untuk konteks job)
TASK_LINE_RE = re.compile(r"\bagent\.[a-z_]+|\btool\s+[a-z_]+", re.IGNORECASE)

# 7. Pengambilan query pencarian dari baris tool
QUERY_PATTERNS = (
    re.compile(r"['\"]?query['\"]?\s*[=:]\s*['\"](?P<q>[^'\"]+)['\"]", re.IGNORECASE),
    re.compile(r"search(?:ing)?\s+(?:for\s+)?['\"](?P<q>[^'\"]+)['\"]", re.IGNORECASE),
    re.compile(r"['\"](?P<q>[^'\"]{3,})['\"]\s*$", re.IGNORECASE),
)

# Registry id cron → nama job. Diisi ulang dari log saat ditemukan,
# dan bisa di-seed manual di sini (contoh: cron 'Riset Konten' di VPS).
KNOWN_CRON_JOBS: dict[str, str] = {
    "72d65950ce86": "Riset Konten",
}
_CRON_JOB_NAMES: dict[str, str] = dict(KNOWN_CRON_JOBS)

# Konteks job terakhir (id cron) untuk baris log tanpa tag cron,
# mis. "INFO agent.tool_executor: tool web_search completed (1.28s, 6724 chars)".
CRON_CONTEXT_TTL = 300  # detik
_LAST_CRON_ID: str | None = None
_LAST_CRON_TS: float = 0.0

# Pemetaan nama job → agentId (urutan = prioritas).
JOB_AGENT_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("agen-inbox", ("inbox", "lead", "email", "imap", "klasifikasi")),
    ("agen-content", ("konten", "content", "riset", "tren", "artikel", "caption", "sosmed", "instagram", "tiktok")),
    ("agen-pm", ("project", "proyek", "wo-", "deadline", "kanban", "timeline", "sprint", "task")),
    ("agen-admin", ("monitor", "gateway", "laporan", "keuangan", "invoice", "budget", "arsip", "housekeeping", "memory")),
)

# Nama agen default bila job tidak cocok dengan keyword mana pun.
DEFAULT_AGENT_ID = "agen-bangheri"

# Pesan per tool.
TOOL_MESSAGES = {
    "send_telegram": "📤 Mengirim pesan ke Telegram",
    "save_memory": "💾 Menyimpan catatan ke memory",
    "write_memory": "💾 Memperbarui memory",
    "read_memory": "📖 Membaca memory",
    "file_io": "📁 Membaca/menulis file",
}

# Sanitasi privasi: ID numerik Telegram (>= 6 digit) disensor.
NUMERIC_ID_RE = re.compile(r"\b\d{6,}\b")

# Modul Hermes pada baris log → narasi.
MODULE_MESSAGES = {
    "agent.turn_context": "🗣️ Menerima perintah tugas",
    "agent.conversation_loop": "💭 Berpikir dan memproses tugas",
    "agent.tool_executor": "⚙️ Menjalankan tool",
    "agent.message_sanitization": "🛡️ Membersihkan pesan masuk",
    "agent.auxiliary_client": "🤖 Memeriksa model auxiliary",
    "agent.background_review": "🔍 Meninjau hasil di latar belakang",
    "agent.conversation_compression": "🗜️ Memadatkan riwayat chat",
    "agent.chat_completion_helpers": "💬 Menyusun permintaan ke model",
    "tools.tool_result_storage": "💾 Menyimpan hasil tool",
    "hermes_cli.tools_config": "🔧 Mengonfigurasi toolset platform",
    "hermes_cli.mem_trim": "🧹 Membersihkan memori gateway",
    "hermes_cli.auth": "🔑 Autentikasi ke provider",
    "run_agent": "⚙️ Menyiapkan eksekusi model",
    "cron.scheduler": "⏰ Menjadwalkan job cron",
    "__main__": "🔧 Menjalankan job",
}


def _sanitize(text: str) -> str:
    """Sensor ID numerik Telegram agar tidak bocor ke balon chat."""
    return NUMERIC_ID_RE.sub("<ID>", text)


def _truncate(text: str, max_len: int = 60) -> str:
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def map_job_to_agent(job_name: str) -> str:
    """Map nama job ke agentId berdasarkan keyword (default agen-bangheri)."""
    lowered = job_name.lower()
    for agent_id, keywords in JOB_AGENT_KEYWORDS:
        for keyword in keywords:
            if keyword in lowered:
                return agent_id
    return DEFAULT_AGENT_ID


def _is_cron_id(text: str) -> bool:
    return bool(re.fullmatch(r"[0-9a-f]{6,}", text.strip(), re.IGNORECASE))


def _resolve_job_name(cron_id: str | None, job_name: str | None) -> str:
    """Tentukan nama job efektif dari tag cron dan/atau nama job."""
    if job_name:
        candidate = job_name.strip()
        if _is_cron_id(candidate):
            return _CRON_JOB_NAMES.get(candidate.lower(), candidate)
        return candidate
    if cron_id:
        return _CRON_JOB_NAMES.get(cron_id, cron_id)
    return ""


def _extract_query(line: str) -> str | None:
    """Ambil query pencarian dari baris log tool (jika ada)."""
    for pattern in QUERY_PATTERNS:
        m = pattern.search(line)
        if m:
            query = _sanitize(m.group("q").strip())
            if query:
                return _truncate(query, 40)
    return None


def _describe_line(line: str) -> str:
    """Narasi umum untuk baris log cron."""
    lowered = line.lower()
    for module, message in MODULE_MESSAGES.items():
        if module in lowered:
            return message
    return "⚙️ Proses berjalan"


def _event(agent_id: str, action: str, message: str, **extra) -> dict:
    event = {
        "agentId": agent_id,
        "action": action,
        "message": _truncate(_sanitize(message), 60),
        "timestamp": _now_iso(),
    }
    event.update(extra)
    return event


def _current_cron_id() -> str | None:
    """Id cron terakhir yang terlihat (konteks baris log tanpa tag cron)."""
    if _LAST_CRON_ID is None:
        return None
    if time.monotonic() - _LAST_CRON_TS > CRON_CONTEXT_TTL:
        return None
    return _LAST_CRON_ID


def _detect_agent(line: str, cron_id: str | None, job_name: str | None) -> tuple[str, str]:
    """Tentukan (agentId, nama job efektif) untuk satu baris log."""
    # 1. Tag agen eksplisit di baris → menang
    m = AGENT_TAG_RE.search(line)
    if m:
        return m.group(1).lower(), _resolve_job_name(cron_id, job_name)

    # 2. Nama job (mapping keyword)
    resolved = _resolve_job_name(cron_id, job_name)
    if resolved:
        return map_job_to_agent(resolved), resolved

    # 3. Konteks: id cron terakhir (± Cron_CONTEXT_TTL detik)
    context_id = _current_cron_id()
    if context_id:
        context_name = _CRON_JOB_NAMES.get(context_id, context_id)
        return map_job_to_agent(context_name), context_name

    # 4. Default
    return DEFAULT_AGENT_ID, ""


def parse_hermes_log_line(line: str) -> dict | None:
    """Parse satu baris log Hermes ke AgentEvent (format log aktual VPS).

    Fallback ke hermes_adapter.parse_log_line untuk pola lama.
    """
    global _LAST_CRON_ID, _LAST_CRON_TS

    if not line or not line.strip():
        return None

    cron_id: str | None = None
    m = CRON_TAG_RE.search(line)
    if m:
        cron_id = m.group("job_id").lower()
        _LAST_CRON_ID = cron_id
        _LAST_CRON_TS = time.monotonic()

    job_name: str | None = None
    m = JOB_NAME_RE.search(line)
    if m:
        job_name = m.group("name").strip()

    # Belajar pemetaan id cron → nama job dari baris yang memuat keduanya.
    if cron_id and job_name and not _is_cron_id(job_name):
        _CRON_JOB_NAMES.setdefault(cron_id, job_name)

    agent_id, _resolved = _detect_agent(line, cron_id, job_name)

    # 1. "API call #3" → sedang berpikir
    m = API_CALL_RE.search(line)
    if m:
        return _event(agent_id, "working", f"🤖 Berpikir... (call #{m.group('n')})")

    # 2. "tool web_search completed" → memakai tool
    m = TOOL_COMPLETED_RE.search(line)
    if m:
        tool = m.group("tool").lower()
        if tool == "web_search":
            query = _extract_query(line)
            message = f"🔍 Mencari: {query}" if query else "🔍 Mencari: web_search"
        else:
            message = TOOL_MESSAGES.get(tool, f"⚙️ {tool} selesai")
        return _event(agent_id, "working", message, toolUsed=tool)

    # 3. "Job 'Riset Konten' completed successfully" → job selesai
    m = JOB_COMPLETED_RE.search(line)
    if m:
        name = m.group("name").strip()
        return _event(map_job_to_agent(name), "idle", f"✅ {name} selesai")

    # 4. "Job '<id>': delivered to telegram: ..." → laporan terkirim
    if DELIVERED_RE.search(line) and job_name:
        marker = "delivered to telegram:"
        idx = line.lower().find(marker)
        tail = line[idx + len(marker):].strip() if idx >= 0 else ""
        message = f"📤 {tail}" if tail else "📤 Laporan dikirim ke Telegram"
        return _event(agent_id, "working", message)

    # 5. "Turn ended: ..." → turn agen selesai
    if TURN_ENDED_RE.search(line):
        return _event(agent_id, "idle", "✅ Selesai mengerjakan tugas")

    # 6. Baris bertag cron → working (narasi per modul Hermes)
    if cron_id:
        return _event(agent_id, "working", _describe_line(line))

    # 6b. Baris tanpa tag cron tapi masih dalam konteks job (mis. "agent.tool_executor")
    if _current_cron_id() and TASK_LINE_RE.search(line):
        return _event(agent_id, "working", _describe_line(line))

    # 7. Fallback ke parser pola lama
    if _legacy_parse_log_line is not None:
        return _legacy_parse_log_line(line)
    return None


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
# Self-test
# ---------------------------------------------------------------------------

SAMPLE_LINES = [
    "INFO [cron_72d65950ce86_20261021_060045] agent.conversation_loop: Menganalisis tren AI untuk UMKM",
    "INFO [cron_72d65950ce86_20261021_060045] agent.tool_executor: tool web_search completed",
    "INFO [cron_72d65950ce86_20261021_060045] agent.tool_executor: tool web_search completed query='tren AI UMKM 2026'",
    "INFO __main__: Job 'Riset Konten' completed successfully",
    "INFO cron.scheduler: Job '72d65950ce86': delivered to telegram: Laporan tren AI siap",
    "INFO [cron_aabbcc11ee22_20261021_070000] agent.tool_executor: tool web_search completed",
    "INFO __main__: Job 'Monitoring' completed successfully",
    "INFO __main__: Job 'Inbox' completed successfully",
    "INFO __main__: Job 'Lead Harian' completed successfully",
    "INFO __main__: Job 'Project WO-014' completed successfully",
    "INFO __main__: Job 'Latihan Kaggle' completed successfully",
    "INFO [cron_72d65950ce86_20261021_060100] agent.tool_executor: API call #3",
]


def self_test() -> int:
    failures = 0
    for line in SAMPLE_LINES:
        event = parse_hermes_log_line(line)
        if event is None:
            print(f"[FAIL] tidak ter-parse: {line}")
            failures += 1
            continue
        print(
            f"[OK] {event['agentId']:<15} {event['action']:<8} {event['message']}"
        )
    print(f"\n{len(SAMPLE_LINES) - failures}/{len(SAMPLE_LINES)} baris ter-parse.")
    return 1 if failures else 0


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Hermes → Claude Code transcript adapter", allow_abbrev=False)
    parser.add_argument("--log", default=_default_log_path(), help="Path ke hermes agent.log")
    parser.add_argument("--project", default=_default_project_dir(), help="Claude Code project dir name")
    parser.add_argument("--once", action="store_true", help="Baca sekali lalu keluar ( untuk testing )")
    parser.add_argument("--self-test", action="store_true", help="Uji parser dengan contoh log")
    args = parser.parse_args()

    if args.self_test:
        raise SystemExit(self_test())

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
    print(
        f"[adapter] Parser: log-real + fallback={'hermes_adapter' if _legacy_parse_log_line else 'none'}",
        file=sys.stderr,
    )

    def handle_line(raw: str) -> None:
        ev = parse_hermes_log_line(raw)
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
