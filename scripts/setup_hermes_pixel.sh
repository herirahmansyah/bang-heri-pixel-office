#!/usr/bin/env bash
# setup_hermes_pixel.sh — Siapkan pipeline Hermes → Claude Code transcript.
#
# Langkah:
#   1. Salin/tautkan adapter ke VPS path (~/.local/bin)
#   2. Jalankan pixel-agents di project hermes-office (baca JSONL dari ~/.claude/projects)
#   3. Jalankan hermes_to_claude_transcript.py di background (tail -f agent.log)
#
# Output JSONL: ~/.claude/projects/-home-bang-hermes-office/<agentId>.jsonl
#
# Usage: bash scripts/setup_hermes_pixel.sh [--no-daemon]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ADAPTER_SRC="${SCRIPT_DIR}/hermes_to_claude_transcript.py"
ADAPTER_DST="${HOME}/.local/bin/hermes_to_claude_transcript.py"
PROJECT_NAME="bang-heri-pixel-office"
CLAUDE_PROJECT_DIR="-home-bang-hermes-office"

DAEMON=1
if [ "${1:-}" = "--no-daemon" ]; then
    DAEMON=0
fi

echo "[setup] Project dir : ${PROJECT_DIR}"
echo "[setup] Claude proj  : ${CLAUDE_PROJECT_DIR}"

# ---------------------------------------------------------------------------
# 1. Pastikan adapter ada di VPS path
# ---------------------------------------------------------------------------
mkdir -p "${HOME}/.local/bin"
if [ ! -f "${ADAPTER_SRC}" ]; then
    echo "[ERROR] Adapter tidak ditemukan: ${ADAPTER_SRC}" >&2
    exit 1
fi
# Salin (overwrite) agar selalu sinkron dengan versi terbaru
cp -f "${ADAPTER_SRC}" "${ADAPTER_DST}"
chmod +x "${ADAPTER_DST}"
echo "[setup] Adapter dipasang di: ${ADAPTER_DST}"

# Pastikan backend/app/hermes_adapter.py bisa diimpor oleh adapter
if [ ! -d "${PROJECT_DIR}/backend/app" ]; then
    echo "[ERROR] backend/app tidak ditemukan di ${PROJECT_DIR}" >&2
    exit 1
fi

# ---------------------------------------------------------------------------
# 2. Jalankan pixel-agents (baca JSONL dari ~/.claude/projects)
# ---------------------------------------------------------------------------
# pixel-agents membaca transcript Claude Code secara otomatis dari
# ~/.claude/projects/<project>/, jadi kita cukup start server di project dir.
# Output JSONL yang ditulis adapter akan langsung terbaca oleh pixel-agents.
#
# Catatan: port dipilih otomatis (ephemeral). Gunakan --port jika perlu fixed port.
PIDFILE_PA="${PROJECT_DIR}/.pixel-agents.pid"
pid_pa=$(cat "${PIDFILE_PA}" 2>/dev/null || echo "")
if [ -f "${PIDFILE_PA}" ] && [ -n "${pid_pa}" ] && kill -0 "${pid_pa}" 2>/dev/null; then
    echo "[setup] pixel-agents sudah berjalan (pid=${pid_pa})"
else
    echo "[setup] Menjalankan pixel-agents..."
    nohup pixel-agents \
        --host 127.0.0.1 \
        > "${PROJECT_DIR}/.pixel-agents.log" 2>&1 &
    echo $! > "${PIDFILE_PA}"
    echo "[setup] pixel-agents pid=$(cat "${PIDFILE_PA}") log=${PROJECT_DIR}/.pixel-agents.log"
    sleep 2
fi

# ---------------------------------------------------------------------------
# 3. Jalankan adapter di background (tail -f agent.log)
# ---------------------------------------------------------------------------
PIDFILE_AD="${PROJECT_DIR}/.hermes_adapter.pid"
pid_ad=$(cat "${PIDFILE_AD}" 2>/dev/null || echo "")
if [ -f "${PIDFILE_AD}" ] && [ -n "${pid_ad}" ] && kill -0 "${pid_ad}" 2>/dev/null; then
    echo "[setup] Adapter sudah berjalan (pid=${pid_ad})"
else
    echo "[setup] Menjalankan Hermes adapter..."
    nohup python3 "${ADAPTER_DST}" \
        --project "${CLAUDE_PROJECT_DIR}" \
        > "${PROJECT_DIR}/.hermes_adapter.log" 2>&1 &
    echo $! > "${PIDFILE_AD}"
    echo "[setup] Adapter pid=$(cat "${PIDFILE_AD}") log=${PROJECT_DIR}/.hermes_adapter.log"
fi

echo ""
echo "[setup] Selesai."
echo "  - JSONL output: ${HOME}/.claude/projects/${CLAUDE_PROJECT_DIR}/<agentId>.jsonl"
echo "  - Buka URL pixel-agents (lihat .pixel-agents.log) untuk melihat office."
echo ""
echo "[setup] Untuk testing lokal tanpa daemon: python3 ${ADAPTER_DST} --once --project ${CLAUDE_PROJECT_DIR}"