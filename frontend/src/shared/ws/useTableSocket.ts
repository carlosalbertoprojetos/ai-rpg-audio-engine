import { useEffect, useMemo, useRef, useState } from "react";

type TableEvent = {
  event_id: string;
  event_type: string;
  payload: Record<string, string>;
  occurred_at: string;
};

const WS_BASE = import.meta.env.VITE_WS_BASE_URL ?? "ws://localhost:8000";

export function useTableSocket(tableId: string | null, token: string | null) {
  const [events, setEvents] = useState<TableEvent[]>([]);
  const [connected, setConnected] = useState(false);
  const socketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!tableId || !token) {
      return undefined;
    }
    const socket = new WebSocket(
      `${WS_BASE}/api/v1/ws/tables/${tableId}?token=${encodeURIComponent(token)}`
    );
    socketRef.current = socket;
    socket.onopen = () => setConnected(true);
    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);
    socket.onmessage = (message) => {
      try {
        const parsed = JSON.parse(message.data) as TableEvent;
        setEvents((current) => [parsed, ...current].slice(0, 20));
      } catch {
        // Ignore malformed events from external sources.
      }
    };
    return () => {
      socket.close();
    };
  }, [tableId, token]);

  const lastEvent = useMemo(() => events[0] ?? null, [events]);

  return {
    connected,
    events,
    lastEvent,
  };
}
