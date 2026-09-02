import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

class MockWebSocket {
  static instances: MockWebSocket[] = [];
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: ((event: { wasClean: boolean; code: number }) => void) | null = null;
  onerror: (() => void) | null = null;
  readyState = 0;
  sent: string[] = [];
  public url = "";

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  send(data: string) {
    this.sent.push(data);
  }

  close(code = 1000) {
    this.readyState = 3;
    this.onclose?.({ wasClean: code === 1000, code });
  }
}

describe("useWebSocket", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    MockWebSocket.instances = [];
    vi.stubGlobal("WebSocket", MockWebSocket);
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.unstubAllGlobals();
  });

  it("starts in disconnected state when companyId is null", async () => {
    const { useWebSocket } = await import("../hooks/useWebSocket");
    const { result } = renderHook(() => useWebSocket(null));

    expect(result.current.connectionState).toBe("disconnected");
  });

  it("connects when companyId is provided", async () => {
    const { useWebSocket } = await import("../hooks/useWebSocket");
    const { result } = renderHook(() => useWebSocket(1));

    // Wait for connection attempt
    await act(async () => {
      vi.advanceTimersByTime(100);
    });

    expect(MockWebSocket.instances.length).toBe(1);
    expect(result.current.connectionState).toBe("connecting");
  });

  it("transitions to connected on open", async () => {
    const { useWebSocket } = await import("../hooks/useWebSocket");
    const { result } = renderHook(() => useWebSocket(1));

    await act(async () => {
      vi.advanceTimersByTime(100);
    });

    const ws = MockWebSocket.instances[0];
    act(() => {
      ws.readyState = 1;
      ws.onopen?.();
    });

    expect(result.current.connectionState).toBe("connected");
  });

  it("receives messages", async () => {
    const { useWebSocket } = await import("../hooks/useWebSocket");
    const { result } = renderHook(() => useWebSocket(1));

    await act(async () => {
      vi.advanceTimersByTime(100);
    });

    const ws = MockWebSocket.instances[0];
    act(() => {
      ws.readyState = 1;
      ws.onopen?.();
    });

    act(() => {
      ws.onmessage?.({ data: JSON.stringify({ type: "test", payload: {} }) });
    });

    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].type).toBe("test");
  });

  it("ignores malformed messages", async () => {
    const { useWebSocket } = await import("../hooks/useWebSocket");
    const { result } = renderHook(() => useWebSocket(1));

    await act(() => {
      vi.advanceTimersByTime(100);
    });

    const ws = MockWebSocket.instances[0];
    act(() => {
      ws.readyState = 1;
      ws.onopen?.();
    });

    act(() => {
      ws.onmessage?.({ data: "not valid json" });
    });

    expect(result.current.messages).toHaveLength(0);
  });

  it("does not reconnect on clean close", async () => {
    const { useWebSocket } = await import("../hooks/useWebSocket");
    const { result } = renderHook(() => useWebSocket(1));

    await act(async () => {
      vi.advanceTimersByTime(100);
    });

    const ws = MockWebSocket.instances[0];
    act(() => {
      ws.readyState = 1;
      ws.onopen?.();
    });

    act(() => {
      ws.close(1000); // clean close
    });

    expect(result.current.connectionState).toBe("disconnected");

    // Advance time - should not reconnect
    await act(async () => {
      vi.advanceTimersByTime(5000);
    });

    // Only one instance should exist (no reconnect)
    expect(MockWebSocket.instances.length).toBe(1);
  });

  it("reconnects on unclean close", async () => {
    const { useWebSocket } = await import("../hooks/useWebSocket");
    renderHook(() => useWebSocket(1));

    await act(async () => {
      vi.advanceTimersByTime(100);
    });

    const ws = MockWebSocket.instances[0];
    act(() => {
      ws.readyState = 1;
      ws.onopen?.();
    });

    act(() => {
      ws.close(1006); // abnormal closure
    });

    expect(MockWebSocket.instances.length).toBe(1);

    // After delay, should reconnect
    await act(async () => {
      vi.advanceTimersByTime(1100);
    });

    expect(MockWebSocket.instances.length).toBe(2);
  });

  it("does not connect when companyId is null", async () => {
    const { useWebSocket } = await import("../hooks/useWebSocket");
    renderHook(() => useWebSocket(null));

    await act(async () => {
      vi.advanceTimersByTime(100);
    });

    expect(MockWebSocket.instances.length).toBe(0);
  });

  it("clears messages", async () => {
    const { useWebSocket } = await import("../hooks/useWebSocket");
    const { result } = renderHook(() => useWebSocket(1));

    await act(() => {
      vi.advanceTimersByTime(100);
    });

    const ws = MockWebSocket.instances[0];
    act(() => {
      ws.readyState = 1;
      ws.onopen?.();
    });

    act(() => {
      ws.onmessage?.({ data: JSON.stringify({ type: "test" }) });
    });

    expect(result.current.messages).toHaveLength(1);

    act(() => {
      result.current.clearMessages();
    });

    expect(result.current.messages).toHaveLength(0);
  });

  it("sends messages when connected", async () => {
    const { useWebSocket } = await import("../hooks/useWebSocket");
    const { result } = renderHook(() => useWebSocket(1));

    await act(async () => {
      vi.advanceTimersByTime(100);
    });

    const ws = MockWebSocket.instances[0];
    act(() => {
      ws.readyState = MockWebSocket.OPEN;
      ws.onopen?.();
    });

    // Verify connection is established
    expect(result.current.connectionState).toBe("connected");

    act(() => {
      result.current.sendMessage({ type: "ping" });
    });

    expect(ws.sent).toHaveLength(1);
    expect(JSON.parse(ws.sent[0])).toEqual({ type: "ping" });
  });
});
