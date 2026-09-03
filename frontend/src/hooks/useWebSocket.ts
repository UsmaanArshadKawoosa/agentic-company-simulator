import { useCallback, useEffect, useRef, useState } from "react";
import { resolveWebSocketUrl } from "../api/base";

export type ConnectionState = "connecting" | "connected" | "disconnected" | "reconnecting";

export interface WebSocketMessage {
  type: string;
  company_id?: number;
  day?: number;
  payload?: Record<string, unknown>;
  agent_id?: number;
  agent_role?: string;
  message?: string;
  client_id?: string;
}

export function useWebSocket(companyId: number | null) {
  const [connectionState, setConnectionState] = useState<ConnectionState>("disconnected");
  const [messages, setMessages] = useState<WebSocketMessage[]>([]);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 10;

  const connect = useCallback(() => {
    if (companyId === null) return;

    // Close existing connection.
    if (wsRef.current) {
      wsRef.current.close();
    }

    setConnectionState("connecting");

    const wsUrl = resolveWebSocketUrl(companyId);

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnectionState("connected");
      reconnectAttempts.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as WebSocketMessage;
        setMessages((prev) => [...prev.slice(-500), data]); // Keep last 500 messages.
      } catch {
        // Ignore malformed messages.
      }
    };

    ws.onclose = (event) => {
      setConnectionState("disconnected");
      wsRef.current = null;

      // Attempt reconnect if not intentionally closed.
      if (!event.wasClean && reconnectAttempts.current < maxReconnectAttempts) {
        setConnectionState("reconnecting");
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectTimeoutRef.current = setTimeout(() => {
          reconnectAttempts.current += 1;
          connect();
        }, delay);
      }
    };

    ws.onerror = () => {
      // onclose will be called after this.
    };
  }, [companyId]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    if (wsRef.current) {
      wsRef.current.close(1000, "Intentional disconnect");
      wsRef.current = null;
    }
    setConnectionState("disconnected");
  }, []);

  const sendMessage = useCallback((message: Record<string, unknown>) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  const clearMessages = useCallback(() => {
    setMessages([]);
  }, []);

  // Auto-connect when companyId changes.
  useEffect(() => {
    if (companyId !== null) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [companyId, connect, disconnect]);

  // Send ping every 30 seconds to keep connection alive.
  useEffect(() => {
    if (connectionState !== "connected") return;
    const interval = setInterval(() => {
      sendMessage({ type: "ping", timestamp: Date.now() });
    }, 30000);
    return () => clearInterval(interval);
  }, [connectionState, sendMessage]);

  return {
    connectionState,
    messages,
    sendMessage,
    clearMessages,
    connect,
    disconnect,
  };
}
