# Project Handover: Bang Heri AI Office (Pixel Office)
**Current Version:** v1.0.0  
**Repo:** github.com/herirahmansyah/bang-heri-pixel-office  
**Live URL:** https://bang-heri-pixel-office.vercel.app  
**Backend Repo:** github.com/herirahmansyah/bang-heri-ai-agency  

## Stack
- Frontend: Vite + TypeScript + Canvas 2D (fork dari devhub-cc/AI_PixelCompany-DesignAssets)
- Backend: FastAPI + WebSocket, port 8001
- Deploy: Vercel (frontend auto-deploy dari GitHub push)

## 5 Agent
1. agen-bangheri — Chief of Staff (workspace: Chief of Staff)
2. agen-inbox — Inbox Manager
3. agen-content — Content Studio
4. agen-pm — Project Room
5. agen-admin — Finance & Admin

## Fitur
- Speech bubble dari Hermes VPS log (real-time via WebSocket)
- Mode: ● Live (WebSocket connected) / ○ Demo (simulasi lokal)
- Tombol office event: Musala, Standup, Kerja → trigger speech bubble
- Bahasa Indonesia default

## Cara Jalankan
1. Backend: cd ~/projects/bang-heri-ai-agency/backend && python3 -m uvicorn app.main:app --port 8001 --reload
2. Frontend: cd ~/projects/bang-heri-pixel-office && npm run dev
3. Buka http://localhost:5174

## VPS Live Mode
curl -X POST http://localhost:8001/api/mode -H "Content-Type: application/json" -d '{"mode": "ssh_journal"}'

## Deploy
git push origin main → Vercel auto-deploy
