# Project Handover: Bang Heri AI Office
**Current Version:** v1.1.0  
**Repo:** github.com/herirahmansyah/bang-heri-pixel-office  
**Live URL:** https://bang-heri-pixel-office.vercel.app  
**Backend Repo:** github.com/herirahmansyah/bang-heri-ai-agency  

---

## 1. Arsitektur Sistem

### Komponen
1. **Frontend Pixel Office** — fork AI_PixelCompany-DesignAssets, Vite+TypeScript, deploy Vercel
2. **Backend FastAPI** — WebSocket relay, SSH telemetry dari Hermes VPS, port 8001
3. **pixel-agents** — visualisasi kantor pixel, jalan di VPS port 7890
4. **Hermes Adapter** — konversi log Hermes → JSONL format Claude Code

### Flow Data

```
                    ┌──────────────────────────────────────────────┐
                    │            VPS (Hermes Gateway)               │
                    │  hermes-gateway.service · ~/.hermes/logs/      │
                    │  agent.log + gateway.log                      │
                    └───────────────┬──────────────────────────────┘
                                    │ tail -f (read-only)
              ┌─────────────────────┴─────────────────────┐
              │                                           │
   (A) SSH telemetry                               (B) Hermes Adapter
   backend/app/main.py                            scripts/hermes_to_claude_transcript.py
   ssh -o BatchMode=yes VPS                        tail -f agent.log
   → hermes_adapter.parse_log_line()                → hermes_adapter.parse_log_line()
   → broadcast WebSocket                            → JSONL format Claude Code
              │                                           │
              │ ws://localhost:8001/ws/frontend           ▼
              │                                    ~/.claude/projects/
              ▼                                    -home-bang-hermes-office/
   ┌────────────────────┐                           <agentId>.jsonl
   │  Frontend (Vercel) │                                     │
   │  Pixel Office      │                                     ▼
   │  Canvas 2D         │                            pixel-agents (port 7890)
   │  speech bubble     │                            → kantor pixel visual
   └────────────────────┘
```

**Mode tampilan di header frontend:**
- `● Live` — WebSocket terhubung ke backend (data real-time dari Hermes VPS)
- `○ Demo` — backend tidak ada; frontend memakai simulasi lokal (pesan acak tiap 4 detik)

### Agent Mapping (5 agen)

| Agent ID | Workspace / Ruangan | Peran | Koordinat (x,y) |
|---|---|---|---|
| `agen-bangheri` | Chief of Staff | Orchestrator, monitor seluruh agen | (2, 2) |
| `agen-inbox` | Inbox Manager | Email & Lead, klasifikasi HOT/WARM/COLD | (6, 2) |
| `agen-content` | Content Studio | Content Strategist, riset tren AI UMKM | (2, 6) |
| `agen-pm` | Project Room | Project Manager, WO & deadline | (6, 6) |
| `agen-admin` | Finance & Admin | Administrasi, budget & laporan | (4, 4) |

Sumber agent ID ada di dua tempat (harus sinkron):
- `backend/app/hermes_adapter.py` → `AGENT_IDS`
- `src/company.config.ts` → `WORKSPACES[].id` + `WORKSPACES[].worker.id`

---

## 2. Backend API (FastAPI, port 8001)

Base: `http://localhost:8001` — sumber kode di repo `bang-heri-ai-agency/backend/`

| Method | Endpoint | Fungsi |
|---|---|---|
| GET | `/health` | Status backend + mode stream aktif |
| GET | `/api/mode` | Baca mode sumber data (`simulation` \| `ssh_journal`) |
| POST | `/api/mode` | Ganti mode sumber data |
| POST | `/api/office-event` | Broadcast event kantor (`musala` \| `standup` \| `work`) |
| GET | `/api/agents` | Daftar profil SOUL semua agen |
| GET | `/api/agents/{agent_id}` | Isi `SOUL.md` satu agen (read-only) |
| WS | `/ws/frontend` | Stream AgentEvent ke frontend |

**Format AgentEvent** (dipakai frontend + adapter):

```json
{
  "agentId": "agen-content",
  "action": "working",
  "message": "🔧 Mengonfigurasi toolset platform",
  "timestamp": "2026-10-21T08:50:00+00:00",
  "toolUsed": "web_search",
  "targetX": 2,
  "targetY": 6,
  "targetDesk": "musala"
}
```

`action` hanya punya tiga nilai: `idle` | `working` | `moving`.

### Mode Streaming

| Mode | Sumber | Env |
|---|---|---|
| `simulation` (default) | Event dummy dari backend, tiap 3 detik | `STREAM_MODE=simulation` |
| `ssh_journal` | `tail -f ~/.hermes/logs/agent.log` di VPS via SSH read-only | `STREAM_MODE=ssh_journal` |

Prinsip **Zero-VPS-Intrusion**: SSH `BatchMode=yes`, hanya `tail`/`journalctl` read-only, tidak ada port publik baru, tidak ada perintah destruktif.

```bash
# Ganti ke live VPS
curl -X POST http://localhost:8001/api/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "ssh_journal"}'

# balik ke simulasi
curl -X POST http://localhost:8001/api/mode \
  -H "Content-Type: application/json" \
  -d '{"mode": "simulation"}'
```

---

## 3. Hermes Adapter (backend/app/hermes_adapter.py)

Parser read-only, mengubah baris log Hermes → `AgentEvent` dengan narasi natural. Dua pola deteksi:

**Pattern A — Modul Hermes (systemd/journal + file log)**

| Pola log | Agen | Action |
|---|---|---|
| `hermes_plugins.platforms__telegram.adapter` | agen-bangheri | working |
| `hermes_cli.tools_config` | agen-content | working |
| `agent.auxiliary_client` / `auxiliary_unavailable` | agen-admin | working |
| `hermes_cli.mem_trim` | agen-admin | working |
| `gateway.run: kanban dispatcher` | agen-pm | working |
| `gateway.run: Cron scheduler` | agen-pm | working |
| `gateway.run: Gateway housekeeping` | agen-admin | working |
| `gateway.run: inbound message` | agen-inbox | working |
| `gateway.run: response ready` | agen-inbox | working |
| `gateway.platforms.base` | agen-inbox | working |

**Pattern B — Tag eksplisit & tool call**
- Tag agen eksplisit: `agen-inbox`, `agen-content`, `agen-pm`, `agen-admin`, `agen-bangheri` (prioritas tertinggi)
- Tool call: `web_search`, `save_memory`, `send_telegram`, `file_io`, `read_memory`, `write_memory`

**Privasi:** ID numerik Telegram (≥6 digit) otomatis disensor menjadi `<ID>`. Pesan balon dipotong maksimal 40 karakter.

---

## 4. Pipeline Hermes → Claude Code (pixel-agents)

`scripts/hermes_to_claude_transcript.py` membaca log Hermes via `tail -f`, mem-parse dengan `hermes_adapter`, lalu menulis **JSONL format Claude Code** — format yang dipahami `pixel-agents` untuk menampilkan aktivitas agen sebagai karakter yang bergerak.

- Output: `~/.claude/projects/-home-bang-hermes-office/<agentId>.jsonl` (1 file per agen)
- `action=working` → record `assistant` dengan content `tool_use`
- `action=moving` → record `assistant` dengan content `text`
- `action=idle` → record `user` dengan content `tool_result`
- Struktur record: `type`, `uuid`, `parentUuid` (rantai), `timestamp`, `sessionId`, `isSidechain`, `message{role, content, usage, model}`

`pixel-agents` otomatis memindai `~/.claude/projects/<project>/` → menampilkan kantor pixel + hook Claude Code terpasang di `~/.pixel-agents/hooks/claude-hook.js`.

**Setup satu-klik:**

```bash
bash scripts/setup_hermes_pixel.sh          # daemon (pixel-agents + adapter)
bash scripts/setup_hermes_pixel.sh --no-daemon
```

Script ini: menyalin adapter ke `~/.local/bin/`, menjalankan `pixel-agents` (127.0.0.1), lalu menjalankan adapter di background. PID & log: `.pixel-agents.pid`, `.hermes_adapter.pid`, `.pixel-agents.log`, `.hermes_adapter.log`.

---

## 5. Environment Variables

| Variable | Default | Lokasi | Keterangan |
|---|---|---|---|
| `STREAM_MODE` | `simulation` | backend | `simulation` \| `ssh_journal` |
| `VPS_SSH_TARGET` | `ubuntu@your-vps-ip` | backend | Target SSH VPS (BatchMode, read-only) |
| `HERMES_LOG_PATH` | `~/.hermes/logs/agent.log` | adapter | Path log Hermes yang di-tail |
| `CLAUDE_PROJECT` | `-home-bang-hermes-office` | adapter | Nama folder project Claude Code |
| `HERMES_ADAPTER_PATH` | — | adapter | Override lokasi `hermes_adapter.py` |

> Jangan pernah commit `.env` / API key ke GitHub.

---

## 6. Cara Jalankan (Lokal)

```bash
# 1. Backend (terminal 1)
cd ~/projects/bang-heri-ai-agency/backend
python3 -m uvicorn app.main:app --port 8001 --reload

# 2. Frontend (terminal 2)
cd ~/projects/bang-heri-pixel-office
npm install
npm run dev
```

Buka http://localhost:5174 (port 5173 juga didukung; CORS mengizinkan keduanya).

**Mode live dari VPS** (backend harus sudah jalan):
```bash
curl -X POST http://localhost:8001/api/mode -H "Content-Type: application/json" -d '{"mode": "ssh_journal"}'
```

**Build & preview:**
```bash
npm run build     # tsc --noEmit && vite build
npm run preview
```

---

## 7. VPS (Hermes Gateway)

- VPS: Tencent Cloud Ubuntu 22.04.5, 2 vCPU / 1.9 GB RAM / 40 GB disk
- Service: systemd **user** unit `hermes-gateway.service`
- Log: `journalctl --user -u hermes-gateway -f` dan file `~/.hermes/logs/{agent,gateway}.log`
- SSH key saja (tanpa password) agar `BatchMode=yes` berhasil

```bash
journalctl --user -u hermes-gateway -n 50 --no-pager
journalctl --user -u hermes-gateway -f        # live
systemctl --user status hermes-gateway
```

---

## 8. Deploy

Frontend: `git push origin main` → Vercel auto-deploy (project `bang-heri-pixel-office`).

```bash
git add -A
git commit -m "feat: ..."
git push origin main
```

> Catatan: URL WebSocket di frontend saat ini hardcode ke `ws://localhost:8001/ws/frontend`.
> Agar live di domain Vercel, arahkan ke URL backend publik (wss://) — lihat bagian Roadmap.

---

## 9. Struktur Folder

```
bang-heri-pixel-office/
├── backend/app/hermes_adapter.py     # parser log Hermes → AgentEvent
├── scripts/
│   ├── hermes_to_claude_transcript.py # adapter log → JSONL Claude Code
│   └── setup_hermes_pixel.sh          # setup pixel-agents + adapter
├── src/
│   ├── DemoApp.tsx                    # shell: header, status bar, event office
│   ├── OfficeWorld.tsx                # renderer Canvas 2D (world, karakter, furnitur)
│   ├── company.config.ts              # tema, 5 workspace, roster
│   ├── i18n.ts                        # 5 bahasa (en/zh/ko/vi/id)
│   ├── hooks/useHermesSocket.ts       # koneksi WebSocket + auto-reconnect
│   └── game/                          # office-world, workflow, office-events
├── public/                            # sprites karakter & aset furnitur
├── design/, guide/                    # dokumentasi desain
└── HANDOVER.md
```

---

## 10. Fitur Saat Ini

- Speech bubble real-time di atas kepala agen (dari Hermes VPS log)
- Indikator mode: `● Live` / `○ Demo` (auto-reconnect WebSocket tiap 3 detik)
- Tombol office event: 🕌 Musala, 🤝 Standup, 💻 Kerja (hold simulasi 15 detik)
- Fallback lokal bila backend mati (pesan demo acak + pesan event hardcoded)
- 5 workspace, 5 bahasa UI, default Bahasa Indonesia
- Sanitasi privasi ID Telegram otomatis

---

## 11. Troubleshooting

| Gejala | Penyebab | Solusi |
|---|---|---|
| `● Live` tidak berubah jadi Live | Backend mati / port 8001 mati | `curl http://localhost:8001/health` |
| `ModuleNotFoundError: No module named 'hermes_adapter'` | Adapter disalin ke `~/.local/bin` tapi `hermes_adapter.py` tidak ditemukan | Set `HERMES_ADAPTER_PATH=/path/ke/backend/app` atau jalankan skrip dari dalam repo |
| Mode live tapi tidak ada event | SSH ke VPS gagal / `VPS_SSH_TARGET` salah | `ssh -o BatchMode=yes $VPS_SSH_TARGET 'tail -n 5 ~/.hermes/logs/agent.log'` |
| Balon chat kosong | Log Hermes tidak memuat pola yang dikenali | Tambahkan regex baru di `hermes_adapter.py` (pola A/B) |
| Frontend `401` saat build | TypeScript error | `npm run build` (menjalankan `tsc --noEmit`) |
| pixel-agents tidak bisa diakses | Port ephemeral berubah tiap start | Ambil URL + token dari `.pixel-agents.log` |

---

## 12. Guardrail (Tidak Boleh Dilanggar)

- ❌ Agen **dilarang** mengirim email atau posting sosial media otomatis — hanya boleh membuat DRAF.
- ❌ Jangan commit `.env`, API key, atau kredensial Telegram ke GitHub.
- ❌ Jangan mengubah/menulis file di VPS dari adapter — parsing harus tetap read-only.
- ✅ Perubahan `SOUL.md` harus di-deploy ulang ke VPS (`~/.hermes/skills/.../SKILL.md`) **dan** di-commit.
- ✅ Semua perubahan besar mengikuti format Work Order (WO) dengan checkpoint jelas.

---

## 13. Roadmap / TODO

- [ ] Arahkan WebSocket frontend ke URL backend publik (`wss://`) agar status Live di domain Vercel
- [ ] Deploy backend FastAPI ke VPS sebagai systemd service (port 8001 internal + reverse proxy/tunnel)
- [ ] Simpan adapter di `backend/app/hermes_adapter.py` sebagai single source of truth (sinkronisasi dua repo)
- [ ] Tambah unit test parser untuk pola Hermes baru (`backend/tests/test_hermes_adapter.py`)
- [ ] Hapus file runtime dari repo (`.pid`, `.log`, `__pycache__`) dan tambahkan ke `.gitignore`
- [ ] Rapikan: hapus `dist/` dan `design/` duplikat bila sudah deprecated

---

## 14. Referensi Cepat

```bash
# Status service & log
systemctl --user status hermes-gateway
journalctl --user -u hermes-gateway -f

# Backend
curl http://localhost:8001/health
curl http://localhost:8001/api/mode
curl http://localhost:8001/api/agents

# Pipeline pixel
cat .pixel-agents.log          # URL + token
cat .hermes_adapter.log        # status adapter
ls ~/.claude/projects/-home-bang-hermes-office/

# Frontend
npm run dev
```
