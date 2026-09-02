import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { OperationsPanel } from "../components/OperationsPanel";

const mockGetObjectives = vi.fn();
const mockCreateObjective = vi.fn();
const mockGetRisks = vi.fn();
const mockGetIncidents = vi.fn();

vi.mock("../api/api", () => ({
  api: {
    listCompanies: vi.fn().mockResolvedValue([]),
    createCompany: vi.fn().mockResolvedValue({}),
    getCompany: vi.fn().mockResolvedValue({}),
    getAgents: vi.fn().mockResolvedValue([]),
    getEvents: vi.fn().mockResolvedValue([]),
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
    startSimulation: vi.fn().mockResolvedValue({ message: "started", state: null }),
    pauseSimulation: vi.fn().mockResolvedValue({ message: "paused", state: null }),
    tickSimulation: vi.fn().mockResolvedValue({ message: "ticked", state: null }),
    resumeSimulation: vi.fn().mockResolvedValue({ message: "resumed", state: null }),
    getSimulation: vi.fn().mockResolvedValue(null),
    getObjectives: (...args: unknown[]) => mockGetObjectives(...args),
    createObjective: (...args: unknown[]) => mockCreateObjective(...args),
    updateObjective: vi.fn().mockResolvedValue({}),
    getRisks: (...args: unknown[]) => mockGetRisks(...args),
    createRisk: vi.fn().mockResolvedValue({}),
    getIncidents: (...args: unknown[]) => mockGetIncidents(...args),
    getResources: vi.fn().mockResolvedValue([]),
    getOperationalStatus: vi.fn().mockResolvedValue({}),
  },
}));

describe("OperationsPanel", () => {
  beforeEach(() => {
    vi.clearAllMocks();

    // Default mock implementations
    mockGetObjectives.mockResolvedValue([]);
    mockCreateObjective.mockResolvedValue({});
    mockGetRisks.mockResolvedValue([]);
    mockGetIncidents.mockResolvedValue([]);
  });

  it("renders objectives section", async () => {
    render(<OperationsPanel companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Objectives")).toBeInTheDocument();
    });
  });

  it("renders objectives list with titles", async () => {
    mockGetObjectives.mockResolvedValue([
      { id: 1, title: "Launch MVP", status: "IN_PROGRESS", priority: 1, progress: 30 },
    ]);
    render(<OperationsPanel companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Launch MVP")).toBeInTheDocument();
    });
  });

  it("renders risks section with risk types", async () => {
    mockGetRisks.mockResolvedValue([
      { id: 1, risk_type: "RUNWAY", severity: "MEDIUM", status: "ACTIVE" },
    ]);
    render(<OperationsPanel companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Risks")).toBeInTheDocument();
      expect(screen.getByText("RUNWAY")).toBeInTheDocument();
    });
  });

  it("renders incidents section with incident types", async () => {
    mockGetIncidents.mockResolvedValue([
      { id: 1, incident_type: "PRODUCT_DELAY", severity: "HIGH", status: "ACTIVE" },
    ]);
    render(<OperationsPanel companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Incidents")).toBeInTheDocument();
      expect(screen.getByText("PRODUCT_DELAY")).toBeInTheDocument();
    });
  });

  it("shows empty state when no objectives", async () => {
    mockGetObjectives.mockResolvedValue([]);
    render(<OperationsPanel companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("No objectives yet")).toBeInTheDocument();
    });
  });

  it("shows empty state when no risks", async () => {
    mockGetRisks.mockResolvedValue([]);
    render(<OperationsPanel companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("No active risks")).toBeInTheDocument();
    });
  });

  it("shows empty state when no incidents", async () => {
    mockGetIncidents.mockResolvedValue([]);
    render(<OperationsPanel companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("No active incidents")).toBeInTheDocument();
    });
  });

  it("shows create objective form when + Add is clicked", async () => {
    render(<OperationsPanel companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Objectives")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("+ Add"));

    expect(screen.getByPlaceholderText("Objective title")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Description (optional)")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create Objective" })).toBeInTheDocument();
  });

  it("creates objective when form is submitted", async () => {
    render(<OperationsPanel companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("Objectives")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("+ Add"));
    await userEvent.type(screen.getByPlaceholderText("Objective title"), "New Goal");
    await userEvent.type(screen.getByPlaceholderText("Description (optional)"), "Important goal");
    await userEvent.click(screen.getByRole("button", { name: "Create Objective" }));

    await waitFor(() => {
      expect(mockCreateObjective).toHaveBeenCalledWith(1, "New Goal", "Important goal");
    });
  });

  it("shows error state when API fails", async () => {
    mockGetObjectives.mockRejectedValue(new Error("Failed to load"));
    render(<OperationsPanel companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load/i)).toBeInTheDocument();
    });
  });

  it("does not poll when visible is false", async () => {
    render(<OperationsPanel companyId={1} visible={false} />);

    await waitFor(() => {
      expect(screen.getByText("Objectives")).toBeInTheDocument();
    });

    const initialCallCount = mockGetObjectives.mock.calls.length;

    // Wait a bit and verify no additional calls are made
    await new Promise((resolve) => setTimeout(resolve, 100));

    expect(mockGetObjectives.mock.calls.length).toBe(initialCallCount);
  });

  it("displays severity colors correctly", async () => {
    mockGetRisks.mockResolvedValue([
      { id: 1, risk_type: "RUNWAY", severity: "MEDIUM", status: "ACTIVE" },
    ]);
    render(<OperationsPanel companyId={1} />);

    await waitFor(() => {
      expect(screen.getByText("RUNWAY")).toBeInTheDocument();
    });

    const severityBadge = screen.getByText("MEDIUM");
    expect(severityBadge).toHaveClass("text-yellow-400");
  });
});
