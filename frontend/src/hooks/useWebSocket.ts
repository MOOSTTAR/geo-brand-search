import { useEffect, useRef, useState, useCallback } from "react";
import type { WsMessage } from "../api/types";

const WS_URL = "ws://localhost:8000/ws";
const MAX_RETRIES = 5;

export function useWebSocket(onMessage: (msg: WsMessage) => void) {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);
  const onMessageRef = useRef(onMessage);
  onMessageRef.current = onMessage;

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setIsConnected(true);
      retriesRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data);
        onMessageRef.current(msg);
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;
      if (retriesRef.current < MAX_RETRIES) {
        const delay = Math.min(1000 * 2 ** retriesRef.current, 30000);
        retriesRef.current += 1;
        setTimeout(connect, delay);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    connect();
    return () => {
      wsRef.current?.close();
    };
  }, [connect]);

  const send = useCallback((msg: WsMessage) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(msg));
    }
  }, []);

  return { isConnected, send };
}
