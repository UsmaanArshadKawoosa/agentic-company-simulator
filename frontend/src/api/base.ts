// Centralized resolution of backend base URLs for the API client and the
// WebSocket hook. This is the ONLY place that decides where the browser
// should call the FastAPI backend.
//
// In development the Vite proxy forwards /api and the WebSocket /api/ws to
// the local FastAPI service, so leaving both env vars unset keeps the
// existing dev workflow intact (relative paths, no hard-coded host).
//
// In production the frontend is served from Vercel and the backend lives
// on Render, so the deployment configuration supplies:
//   VITE_API_BASE_URL  e.g. "https://agentic-company-simulator.onrender.com"
//   VITE_WS_BASE_URL   e.g. "wss://agentic-company-simulator.onrender.com"
//
// Production builds MUST NOT depend on window.location.host for the backend
// (that would point at the Vercel origin, not Render).

const trimTrailingSlash = (value: string): string =>
  value.endsWith("/") ? value.slice(0, -1) : value;

const readEnv = (key: string): string | undefined => {
  // Vite injects import.meta.env.* at build time. Using bracket access keeps
  // the code tree-shakable and avoids TypeScript complaints about unknown
  // custom env keys.
  const env = (import.meta as ImportMeta & { env?: Record<string, string | undefined> }).env;
  const raw = env?.[key];
  return typeof raw === "string" && raw.length > 0 ? raw : undefined;
};

/**
 * Resolves the REST API base URL.
 *
 * Examples:
 *   - dev (no env):        "/api"
 *   - VITE_API_BASE_URL set: "https://agentic-company-simulator.onrender.com/api"
 */
export function resolveApiBaseUrl(): string {
  const explicit = readEnv("VITE_API_BASE_URL");
  if (explicit) {
    return `${trimTrailingSlash(explicit)}/api`;
  }
  return "/api";
}

/**
 * Resolves the WebSocket base URL.
 *
 * Returns ONLY the scheme + host (no path), e.g. "wss://example.com" or, in
 * dev with the Vite proxy, the current window origin.
 *
 * The hook appends "/api/ws/companies/<id>".
 */
export function resolveWsBaseUrl(): string {
  const explicit = readEnv("VITE_WS_BASE_URL");
  if (explicit) {
    return trimTrailingSlash(explicit);
  }
  // Dev fallback: use the current origin so requests flow through the
  // Vite proxy (which forwards /api/ws to the local FastAPI service).
  if (typeof window !== "undefined" && window.location?.origin) {
    return window.location.origin;
  }
  return "";
}

/**
 * Helper used by the WebSocket hook to compute a full ws/wss URL for a
 * given company id.
 */
export function resolveWebSocketUrl(companyId: number): string {
  const base = resolveWsBaseUrl();
  if (!base) return "";
  return `${base}/api/ws/companies/${companyId}`;
}
