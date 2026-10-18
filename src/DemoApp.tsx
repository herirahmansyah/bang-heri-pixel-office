import type { CSSProperties } from "react";
import { useEffect, useMemo, useRef, useState } from "react";
import { STATUS_LABELS, THEME, WORKSPACES } from "./company.config";
import { LOCALES, LOCALE_LABELS, localized, type Locale, type LocalizedText } from "./i18n";
import { OfficeWorld } from "./OfficeWorld";
import { useHermesSocket } from "./hooks/useHermesSocket";
import type { WorkflowStatus } from "./game/workflow";

const themeStyle = {
  "--color-app": THEME.app,
  "--color-frame": THEME.frame,
  "--color-panel": THEME.panel,
  "--color-surface": THEME.surface,
  "--color-line": THEME.line,
  "--color-edge": THEME.edge,
  "--color-floor": THEME.floor,
  "--color-cream": THEME.cream,
  "--color-ink": THEME.ink,
  "--color-muted": THEME.muted,
  "--color-skin": THEME.skin,
  "--color-wood": THEME.wood,
  "--color-wood-dark": THEME.woodDark,
  "--color-screen": THEME.screen,
  "--color-green": THEME.green,
  "--color-amber": THEME.amber,
  "--color-red": THEME.red,
  "--color-focus": THEME.focus,
  "--color-shadow": THEME.shadow,
} as CSSProperties;

/** Demo-only copy. Product copy lives in i18n.ts and company.config.ts. */
const UI = {
  title: {
    ko: "픽셀 오피스 디자인 데모",
    en: "Bang Heri AI Office",
    zh: "像素办公室设计演示",
    vi: "Bản demo thiết kế văn phòng pixel",
    id: "Bang Heri AI Office",
  },
  preview: {
    ko: "상태 미리보기",
    en: "State preview",
    zh: "状态预览",
    vi: "Xem trước trạng thái",
    id: "Status Agen",
  },
  clock: {
    ko: "데모 화면",
    en: "Demo view",
    zh: "演示画面",
    vi: "Màn hình demo",
    id: "Tampilan demo",
  },
} satisfies Record<string, LocalizedText>;

export function DemoApp() {
  const [locale, setLocale] = useState<Locale>("en");
  const [activeId, setActiveId] = useState<string | null>(null);
  const [simulatedMessages, setSimulatedMessages] = useState<Record<string, string>>({});
  const officeEventTimeout = useRef<ReturnType<typeof setTimeout> | null>(null);

  const { statuses, events, connected } = useHermesSocket();

  const PRIMARY_AGENT_IDS = useMemo(() => WORKSPACES.map((w) => w.worker.id), []);

  const SIMULATION_MESSAGES = [
    "Selamat pagi, siap bekerja!",
    "Laporan siap dikirim.",
    "Menunggu persetujuan klien.",
    "Sedang mengedit konten...",
    "Rapat dimulai segera.",
    "File sudah diunggah.",
    "Perlu review segera.",
    "Semua sistem normal.",
  ];

  useEffect(() => {
    if (connected) return;
    const interval = setInterval(() => {
      const agentId = PRIMARY_AGENT_IDS[Math.floor(Math.random() * PRIMARY_AGENT_IDS.length)];
      const message = SIMULATION_MESSAGES[Math.floor(Math.random() * SIMULATION_MESSAGES.length)];
      setSimulatedMessages((prev) => ({ ...prev, [agentId]: message }));
    }, 4000);
    return () => clearInterval(interval);
  }, [connected, PRIMARY_AGENT_IDS]);

  const handleOfficeEvent = async (type: "musala" | "standup" | "work") => {
    try {
      const res = await fetch("http://localhost:8001/api/office-event", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ event: type }),
      });
      const data = await res.json();
      // Extract events from backend response and update agentMessages directly
      const backendEvents: Array<{ agentId: string; message: string }> = data.events ?? [];
      for (const ev of backendEvents) {
        if (ev.agentId && ev.message) {
          setSimulatedMessages((prev) => ({ ...prev, [ev.agentId]: ev.message }));
        }
      }
    } catch {
      // Silent fail if backend is not running
    }
  };

  const agentMessages = useMemo(() => {
    const latest: Record<string, string> = {};
    for (const event of events) {
      latest[event.agentId] = event.message;
    }
    for (const [agentId, text] of Object.entries(simulatedMessages)) {
      latest[agentId] = text;
    }
    for (const agentId of Object.keys(latest)) {
      latest[agentId] = (latest[agentId] ?? "").slice(0, 60);
    }
    return latest;
  }, [events, simulatedMessages]);

  const workerToWorkspace = useMemo(() => {
    const map: Record<string, string> = {};
    for (const workspace of WORKSPACES) {
      map[workspace.worker.id] = workspace.id;
    }
    return map;
  }, []);

  const workspaceStatuses = useMemo(() => {
    const map: Record<string, WorkflowStatus> = {};
    for (const workspace of WORKSPACES) {
      map[workspace.id] = "idle";
    }
    for (const [agentId, status] of Object.entries(statuses)) {
      const wsId = workerToWorkspace[agentId];
      if (wsId) {
        map[wsId] = status === "idle" ? "idle" : "running";
      }
    }
    return map;
  }, [statuses]);

  return (
    <div className="app-shell demo-shell" data-draftroom-shell="" style={themeStyle}>
      <header className="demo-bar">
        <strong>{localized(UI.title, locale)}</strong>
        <div className="demo-subtitle">Kantor AI Otonom • Lombok, NTB</div>
        <select
          aria-label="language"
          onChange={(event) => setLocale(event.target.value as Locale)}
          value={locale}
        >
          {LOCALES.map((code) => (
            <option key={code} value={code}>
              {LOCALE_LABELS[code]}
            </option>
          ))}
        </select>
        <span className="demo-preview-label">{localized(UI.preview, locale)}</span>
        <div className="demo-states">
          <button
            className={activeId === null ? "on" : ""}
            onClick={() => setActiveId(null)}
            type="button"
          >
            {localized(STATUS_LABELS.idle, locale)}
          </button>
          {WORKSPACES.map((workspace) => (
            <button
              className={activeId === workspace.id ? "on" : ""}
              key={workspace.id}
              onClick={() => setActiveId(workspace.id)}
              type="button"
            >
              {localized(workspace.name, locale)}
            </button>
          ))}
        </div>
        <div className="demo-events">
          <button type="button" onClick={() => handleOfficeEvent("musala")} className="office-event-btn">🕌 Musala</button>
          <button type="button" onClick={() => handleOfficeEvent("standup")} className="office-event-btn">🤝 Standup</button>
          <button type="button" onClick={() => handleOfficeEvent("work")} className="office-event-btn">💻 Kerja</button>
        </div>
        <div className="demo-header-right">
          <span
            className="demo-connection"
            style={{
              fontSize: 12,
              fontWeight: 600,
              color: connected ? "#22c55e" : "#f59e0b",
            }}
          >
            {connected ? "● Live" : "○ Demo"}
          </span>
          {activeId && (
            <span className="demo-active-zone">
              {localized(
                (WORKSPACES.find((w) => w.id === activeId)?.name ??
                  { ko: "", en: "", zh: "", vi: "", id: "" }) as LocalizedText,
                locale
              )}
            </span>
          )}
        </div>
      </header>

      <div className="workspace-layout demo-layout">
        <section className="office-panel" data-pane="office">
          <OfficeWorld
            activeWorkspaceId={activeId}
            agentMessages={agentMessages}
            clock={{ label: localized(UI.clock, locale), time: "--:--" }}
            locale={locale}
            officeEvents={[]}
            onOfficeEvent={handleOfficeEvent}
            ready={true}
            workflowStatus={activeId ? "running" : "idle"}
            workspaceStatuses={workspaceStatuses}
          />
        </section>
      </div>

    </div>
  );
}
