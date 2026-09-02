import { render, screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { CommandCenter } from "../pages/CommandCenter";

const mockGetCompany = vi.fn();
const mockGetEvents = vi.fn();
const mockGetAgents = vi.fn();
const mockStartSimulation = vi.fn();
const mockTickSimulation = vi.fn();

// Mock WebSocket
class MockWebSocket {
  static instances: MockWebSocket[] = [];
  onopen: (() => void) | null = null;
  onmessage: ((event: { data: string }) => void) | null = null;
  onclose: ((event: { wasClean: boolean }) => void) | null = null;
  onerror: (() => void) | null = null;
  readyState = 0;
  sent: string[] = [];

  constructor(public url: string) {
    MockWebSocket.instances.push(this);
  }

  send(data: string) {
    this.sent.push(data);
  }

  close() {
    this.readyState = 3;
    this.onclose?.({ wasClean: true });
  }
}

vi.mock("../api/api", () => ({
  api: {
    listCompanies: vi.fn().mockResolvedValue([]),
    createCompany: vi.fn().mockResolvedValue({}),
    getCompany: (...args: unknown[]) => mockGetCompany(...args),
    getAgents: (...args: unknown[]) => mockGetAgents(...args),
    getEvents: (...args: unknown[]) => mockGetEvents(...args),
    getDashboard: vi.fn().mockResolvedValue(null),
    getEmployees: vi.fn().mockResolvedValue([]),
    getJobs: vi.fn().mockResolvedValue([]),
    getCandidates: vi.fn().mockResolvedValue([]),
    getWorkforce: vi.fn().mockResolvedValue(null),
    getFinancials: vi.fn().mockResolvedValue(null),
    getValuation: vi.fn().mockResolvedValue(null),
    getInvestors: vi.fn().mockResolvedValue([]),
    getFundingRounds: vi.fn().mockResolvedValue([]),
    getPipeline: vi.fn().mockResolvedValue([]),
    getBudgetRequests: vi.fn().mockResolvedValue([]),
    startSimulation: (...args: unknown[]) => mockStartSimulation(...args),
    pauseSimulation: vi.fn().mockResolvedValue({ message: "paused", state: null }),
    tickSimulation: (...args: unknown[]) => mockTickSimulation(...args),
    resumeSimulation: vi.fn().mockResolvedValue({ message: "resumed", state: null }),
    getSimulation: vi.fn().mockResolvedValue(null),
    getObjectives: vi.fn().mockResolvedValue([]),
    createObjective: vi.fn().mockResolvedValue({}),
    updateObjective: vi.fn().mockResolvedValue({}),
    getRisks: vi.fn().mockResolvedValue([]),
    createRisk: vi.fn().mockResolvedValue({}),
    getIncidents: vi.fn().mockResolvedValue([]),
    getResources: vi.fn().mockResolvedValue([]),
    getOperationalStatus: vi.fn().mockResolvedValue({}),
  },
}));

describe("CommandCenter", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    MockWebSocket.instances = [];
    vi.stubGlobal("WebSocket", MockWebSocket);

    // Default mock implementations
    mockGetCompany.mockResolvedValue({
      id: 1,
      name: "Test Company",
      mission: "Build great products",
      cash: 100000,
      revenue: 0,
      expenses: 0,
      current_day: 1,
      status: "CREATED" as const,
      seed: 42,
    });
    mockGetAgents.mockResolvedValue([
      { id: 1, name: "Alice", role: "CEO", status: "IDLE" },
      { id: 2, name: "Bob", role: "CTO", status: "WORKING" },
    ]);
    mockGetEvents.mockResolvedValue([
      { id: 1, description: "Company 'Test Company' was created.", simulation_day: 1 },
    ]);
    mockStartSimulation.mockResolvedValue({ message: "started", state: null });
    mockTickSimulation.mockResolvedValue({ message: "ticked", state: null });
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("renders loading state initially", () => {
    mockGetCompany.mockReturnValue(new Promise(() => {}));
    render(<CommandCenter companyId={1} />);
    expect(screen.getByText("Loading company...")).toBeInTheDocument();
  });

  it("renders company name and status after loading", async () => {
    render(<CommandCenter companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Test Company")).toBeInTheDocument();
    });
    expect(screen.getByText("CREATED")).toBeInTheDocument();
    // "Day 1" appears in both header badge and activity feed
    expect(screen.getAllByText("Day 1").length).toBeGreaterThanOrEqual(1);
  });

  it("renders simulation controls", async () => {
    render(<CommandCenter companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Test Company")).toBeInTheDocument();
    });

    expect(screen.getByRole("button", { name: "Start" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Tick" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Resume" })).toBeInTheDocument();
  });

  it("shows Pause button when simulation is running", async () => {
    mockGetCompany.mockResolvedValue({
      id: 1,
      name: "Test Company",
      mission: "Build great products",
      cash: 100000,
      revenue: 0,
      expenses: 0,
      current_day: 1,
      status: "RUNNING" as const,
      seed: 42,
    });
    render(<CommandCenter companyId={1} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Pause" })).toBeInTheDocument();
    });
  });

  it("calls startSimulation when Start is clicked", async () => {
    render(<CommandCenter companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Test Company")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: "Start" }));

    await waitFor(() => {
      expect(mockStartSimulation).toHaveBeenCalledWith(1);
    });
  });

  it("calls tickSimulation when Tick is clicked", async () => {
    mockGetCompany.mockResolvedValue({
      id: 1,
      name: "Test Company",
      mission: "Build great products",
      cash: 100000,
      revenue: 0,
      expenses: 0,
      current_day: 1,
      status: "RUNNING" as const,
      seed: 42,
    });
    render(<CommandCenter companyId={1} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Tick" })).toBeInTheDocument();
    });

    await userEvent.click(screen.getByRole("button", { name: "Tick" }));

    await waitFor(() => {
      expect(mockTickSimulation).toHaveBeenCalledWith(1);
    });
  });

  it("shows error state when company fetch fails", async () => {
    mockGetCompany.mockRejectedValue(new Error("Company not found"));
    render(<CommandCenter companyId={999} />);

    await waitFor(() => {
      expect(screen.getByText(/Company not found/i)).toBeInTheDocument();
    });
  });

  it("shows retry button on error", async () => {
    mockGetCompany.mockRejectedValue(new Error("Network error"));
    render(<CommandCenter companyId={1} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Retry" })).toBeInTheDocument();
    });
  });

  it("renders agents in the hierarchy", async () => {
    render(<CommandCenter companyId={1} />);

    await waitFor(() => {
      // Alice appears in both Agents sidebar and Agent Activity footer
      expect(screen.getAllByText("Alice").length).toBeGreaterThanOrEqual(1);
      expect(screen.getAllByText("Bob").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("renders activity feed with events", async () => {
    render(<CommandCenter companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText(/Company 'Test Company' was created/i)).toBeInTheDocument();
    });
  });

  it("shows empty activity feed when no events", async () => {
    mockGetEvents.mockResolvedValue([]);
    render(<CommandCenter companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Test Company")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText(/No activity yet/i)).toBeInTheDocument();
    });
  });

  it("toggles Operations panel visibility", async () => {
    render(<CommandCenter companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Test Company")).toBeInTheDocument();
    });

    const opsButton = screen.getByRole("button", { name: "Operations" });
    await userEvent.click(opsButton);

    expect(screen.getByText("Objectives")).toBeInTheDocument();
    expect(screen.getByText("Risks")).toBeInTheDocument();
    expect(screen.getByText("Incidents")).toBeInTheDocument();
  });

  it("shows connection indicator", async () => {
    render(<CommandCenter companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Test Company")).toBeInTheDocument();
    });

    // Should show one of the connection states
    const hasConnectionState =
      screen.queryByText("CONNECTING") ||
      screen.queryByText("LIVE") ||
      screen.queryByText("OFFLINE") ||
      screen.queryByText("RECONNECTING");
    expect(hasConnectionState).toBeTruthy();
  });
});
