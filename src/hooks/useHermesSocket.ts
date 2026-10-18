import { useEffect, useState } from "react";

export type AgentStatus = "idle" | "working" | "moving";

export interface AgentEvent {
  agentId: string;
  action: AgentStatus;
  message: string;
  timestamp: string;
}

export function useHermesSocket(url = "ws://localhost:8001/ws/frontend") {
  const [statuses, setStatuses] = useState<Record<string, AgentStatus>>({});
  const [events, setEvents] = useState<AgentEvent[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    let ws: WebSocket;
    let retryTimeout: ReturnType<typeof setTimeout>;

    const connect = () => {
      ws = new WebSocket(url);
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        retryTimeout = setTimeout(connect, 3000);
      };
      ws.onmessage = (e) => {
        try {
          const ev: AgentEvent = JSON.parse(e.data);
          setStatuses(prev => ({ ...prev, [ev.agentId]: ev.action }));
          setEvents(prev => [ev, ...prev].slice(0, 50));
        } catch {}
      };
    };

    connect();
    return () => {
      ws?.close();
      clearTimeout(retryTimeout);
    };
  }, [url]);

  return { statuses, events, connected };
}
