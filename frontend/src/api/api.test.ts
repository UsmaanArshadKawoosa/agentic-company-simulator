import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock fetch globally
const mockFetch = vi.fn();
vi.stubGlobal("fetch", mockFetch);

describe("API Client", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("makes GET request to list companies", async () => {
    const { api } = await import("../api/api");
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => [{ id: 1, name: "Test" }],
    });

    const result = await api.listCompanies();
    expect(mockFetch).toHaveBeenCalledWith("/api/companies", expect.any(Object));
    expect(result).toEqual([{ id: 1, name: "Test" }]);
  });

  it("makes POST request to create company", async () => {
    const { api } = await import("../api/api");
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ id: 1, name: "New Company" }),
    });

    await api.createCompany("New Company", "Mission");
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/companies",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ name: "New Company", mission: "Mission" }),
      })
    );
  });

  it("throws error with JSON detail on 400 response", async () => {
    const { api } = await import("../api/api");
    mockFetch.mockResolvedValue({
      ok: false,
      status: 400,
      json: async () => ({ detail: "Invalid input" }),
    });

    await expect(api.createCompany("", "")).rejects.toThrow("Invalid input");
  });

  it("throws error with JSON detail on 409 response", async () => {
    const { api } = await import("../api/api");
    mockFetch.mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ detail: "Company name already exists" }),
    });

    await expect(api.createCompany("Duplicate", "")).rejects.toThrow("Company name already exists");
  });

  it("handles non-JSON error response gracefully", async () => {
    const { api } = await import("../api/api");
    mockFetch.mockResolvedValue({
      ok: false,
      status: 500,
      json: async () => { throw new Error("Invalid JSON"); },
      text: async () => "Internal Server Error",
    });

    await expect(api.listCompanies()).rejects.toThrow("Internal Server Error");
  });

  it("handles completely unparseable error response", async () => {
    const { api } = await import("../api/api");
    mockFetch.mockResolvedValue({
      ok: false,
      status: 503,
      json: async () => { throw new Error("Invalid JSON"); },
      text: async () => { throw new Error("Cannot read body"); },
    });

    await expect(api.listCompanies()).rejects.toThrow("Request failed (503)");
  });

  it("sends correct headers", async () => {
    const { api } = await import("../api/api");
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => [],
    });

    await api.listCompanies();
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/companies",
      expect.objectContaining({
        headers: { "Content-Type": "application/json" },
      })
    );
  });

  it("handles simulation start", async () => {
    const { api } = await import("../api/api");
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ message: "started", state: { company_id: 1 } }),
    });

    const result = await api.startSimulation(1);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/simulation/1/start",
      expect.objectContaining({ method: "POST" })
    );
    expect(result.message).toBe("started");
  });

  it("handles operations endpoints", async () => {
    const { api } = await import("../api/api");
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => [{ id: 1, title: "Objective" }],
    });

    const result = await api.getObjectives(1);
    expect(mockFetch).toHaveBeenCalledWith(
      "/api/operations/companies/1/objectives",
      expect.any(Object)
    );
    expect(result).toEqual([{ id: 1, title: "Objective" }]);
  });

  it("creates objective with query params", async () => {
    const { api } = await import("../api/api");
    mockFetch.mockResolvedValue({
      ok: true,
      json: async () => ({ id: 1, title: "New" }),
    });

    await api.createObjective(1, "New", "Desc", "STRATEGIC", 2);
    expect(mockFetch).toHaveBeenCalledWith(
      expect.stringContaining("title=New"),
      expect.objectContaining({ method: "POST" })
    );
  });
});
