import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";

const withEnv = (vars: Record<string, string | undefined>) => {
  // Replace the Vite env object for the duration of a test.
  (import.meta as ImportMeta & { env: Record<string, string | undefined> }).env = {
    ...((import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env ?? {}),
    ...vars,
  };
};

describe("api/base.ts — production URL resolution", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    withEnv({ VITE_API_BASE_URL: undefined, VITE_WS_BASE_URL: undefined });
    vi.unstubAllGlobals();
  });

  it("uses the relative /api path in dev (no env vars set)", async () => {
    withEnv({ VITE_API_BASE_URL: undefined, VITE_WS_BASE_URL: undefined });
    const { resolveApiBaseUrl } = await import("../api/base");
    expect(resolveApiBaseUrl()).toBe("/api");
  });

  it("appends /api to an absolute VITE_API_BASE_URL", async () => {
    withEnv({
      VITE_API_BASE_URL: "https://agentic-company-simulator.onrender.com",
      VITE_WS_BASE_URL: undefined,
    });
    const { resolveApiBaseUrl } = await import("../api/base");
    expect(resolveApiBaseUrl()).toBe(
      "https://agentic-company-simulator.onrender.com/api",
    );
  });

  it("does not double-append /api when the env value already ends with it", async () => {
    withEnv({
      VITE_API_BASE_URL: "https://agentic-company-simulator.onrender.com/api",
      VITE_WS_BASE_URL: undefined,
    });
    const { resolveApiBaseUrl } = await import("../api/base");
    expect(resolveApiBaseUrl()).toBe(
      "https://agentic-company-simulator.onrender.com/api",
    );
  });

  it("returns an empty VITE_API_BASE_URL as the dev fallback", async () => {
    withEnv({ VITE_API_BASE_URL: "", VITE_WS_BASE_URL: "" });
    const { resolveApiBaseUrl } = await import("../api/base");
    expect(resolveApiBaseUrl()).toBe("/api");
  });

  it("builds a wss:// WebSocket URL from VITE_WS_BASE_URL", async () => {
    withEnv({
      VITE_API_BASE_URL: undefined,
      VITE_WS_BASE_URL: "wss://agentic-company-simulator.onrender.com",
    });
    const { resolveWebSocketUrl } = await import("../api/base");
    expect(resolveWebSocketUrl(42)).toBe(
      "wss://agentic-company-simulator.onrender.com/api/ws/companies/42",
    );
  });

  it("falls back to window.location.origin in dev when no WS env is set", async () => {
    withEnv({ VITE_WS_BASE_URL: undefined });
    // jsdom default origin is "http://localhost:3000".
    const { resolveWebSocketUrl } = await import("../api/base");
    expect(resolveWebSocketUrl(1)).toBe(
      `${window.location.origin}/api/ws/companies/1`,
    );
  });

  it("never points at localhost in production configuration", async () => {
    withEnv({
      VITE_API_BASE_URL: "https://agentic-company-simulator.onrender.com",
      VITE_WS_BASE_URL: "wss://agentic-company-simulator.onrender.com",
    });
    const { resolveApiBaseUrl, resolveWebSocketUrl } = await import("../api/base");
    const api = resolveApiBaseUrl();
    const ws = resolveWebSocketUrl(1);
    expect(api).not.toMatch(/localhost|127\.0\.0\.1/);
    expect(ws).not.toMatch(/localhost|127\.0\.0\.1/);
  });
});
