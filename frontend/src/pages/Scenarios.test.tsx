import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ScenariosPage } from "./Scenarios";

const mockSeedBuiltinScenarios = vi.fn();
const mockListScenarios = vi.fn();

vi.mock("../api/api", () => ({
  api: {
    seedBuiltinScenarios: (...args: unknown[]) => mockSeedBuiltinScenarios(...args),
    listScenarios: (...args: unknown[]) => mockListScenarios(...args),
    getScenario: vi.fn(),
    createScenario: vi.fn(),
    updateScenario: vi.fn(),
    deleteScenario: vi.fn(),
    duplicateScenario: vi.fn(),
    createRun: vi.fn(),
    listRuns: vi.fn(),
    executeRun: vi.fn(),
    runExperiment: vi.fn(),
    getExperimentResults: vi.fn(),
    // Include all other API methods to avoid mock issues
    listCompanies: vi.fn(),
    createCompany: vi.fn(),
    getCompany: vi.fn(),
    getAgents: vi.fn(),
    getEvents: vi.fn(),
    startSimulation: vi.fn(),
    pauseSimulation: vi.fn(),
    tickSimulation: vi.fn(),
    resumeSimulation: vi.fn(),
    getSimulation: vi.fn(),
    getDashboard: vi.fn(),
    getTimeline: vi.fn(),
    getPlans: vi.fn(),
    getExpectations: vi.fn(),
    getAgentMetrics: vi.fn(),
    getMarket: vi.fn(),
    getCompetitors: vi.fn(),
    getStrategy: vi.fn(),
    getCampaigns: vi.fn(),
    getSales: vi.fn(),
    getHistory: vi.fn(),
    getMarketData: vi.fn(),
    getCompetitorsData: vi.fn(),
    getSalesOpportunities: vi.fn(),
    getAgentMetricsData: vi.fn(),
    getEmployees: vi.fn(),
    getJobs: vi.fn(),
    getCandidates: vi.fn(),
    getWorkforce: vi.fn(),
    getFinancials: vi.fn(),
    getValuation: vi.fn(),
    getInvestors: vi.fn(),
    getFundingRounds: vi.fn(),
    getPipeline: vi.fn(),
    getCapTable: vi.fn(),
    getBudgetRequests: vi.fn(),
    getObjectives: vi.fn(),
    createObjective: vi.fn(),
    updateObjective: vi.fn(),
    getRisks: vi.fn(),
    createRisk: vi.fn(),
    getIncidents: vi.fn(),
    getResources: vi.fn(),
    getOperationalStatus: vi.fn(),
    getTimelineEvents: vi.fn(),
    getDecisions: vi.fn(),
  },
}));

const mockScenarios = [
  {
    id: 1,
    name: "Normal Startup",
    description: "Balanced starting conditions",
    category: "startup",
    is_builtin: true,
    configuration: { name: "Startup", cash: 100000, target_segment: "SMB" },
    run_count: 5,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: 2,
    name: "Cash Crisis",
    description: "Limited cash and high burn",
    category: "financial",
    is_builtin: true,
    configuration: { name: "StrugglingCo", cash: 30000, target_segment: "SMB" },
    run_count: 2,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
];

describe("ScenariosPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListScenarios.mockResolvedValue(mockScenarios);
    mockSeedBuiltinScenarios.mockResolvedValue({ message: "OK" });
  });

  it("renders loading state initially", () => {
    render(
      <ScenariosPage
        onBack={vi.fn()}
        onViewScenario={vi.fn()}
        onRunExperiment={vi.fn()}
      />
    );
    expect(screen.getByText("Loading scenarios...")).toBeInTheDocument();
  });

  it("renders scenario cards after loading", async () => {
    render(
      <ScenariosPage
        onBack={vi.fn()}
        onViewScenario={vi.fn()}
        onRunExperiment={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Normal Startup")).toBeInTheDocument();
      expect(screen.getByText("Cash Crisis")).toBeInTheDocument();
    });
  });

  it("renders scenario descriptions", async () => {
    render(
      <ScenariosPage
        onBack={vi.fn()}
        onViewScenario={vi.fn()}
        onRunExperiment={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Balanced starting conditions")).toBeInTheDocument();
      expect(screen.getByText("Limited cash and high burn")).toBeInTheDocument();
    });
  });

  it("renders run counts", async () => {
    render(
      <ScenariosPage
        onBack={vi.fn()}
        onViewScenario={vi.fn()}
        onRunExperiment={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("5 runs")).toBeInTheDocument();
      expect(screen.getByText("2 runs")).toBeInTheDocument();
    });
  });

  it("renders category badges", async () => {
    render(
      <ScenariosPage
        onBack={vi.fn()}
        onViewScenario={vi.fn()}
        onRunExperiment={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("startup")).toBeInTheDocument();
      expect(screen.getByText("financial")).toBeInTheDocument();
    });
  });

  it("renders empty state when no scenarios", async () => {
    mockListScenarios.mockResolvedValue([]);

    render(
      <ScenariosPage
        onBack={vi.fn()}
        onViewScenario={vi.fn()}
        onRunExperiment={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("No scenarios yet")).toBeInTheDocument();
    });
  });

  it("renders seed builtins button", async () => {
    render(
      <ScenariosPage
        onBack={vi.fn()}
        onViewScenario={vi.fn()}
        onRunExperiment={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Seed Built-ins")).toBeInTheDocument();
    });
  });

  it("calls onViewScenario when View clicked", async () => {
    const onViewScenario = vi.fn();
    render(
      <ScenariosPage
        onBack={vi.fn()}
        onViewScenario={onViewScenario}
        onRunExperiment={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Normal Startup")).toBeInTheDocument();
    });

    const viewButtons = screen.getAllByText("View");
    await userEvent.click(viewButtons[0]);

    expect(onViewScenario).toHaveBeenCalledWith(1);
  });

  it("calls onRunExperiment when Run clicked", async () => {
    const onRunExperiment = vi.fn();
    render(
      <ScenariosPage
        onBack={vi.fn()}
        onViewScenario={vi.fn()}
        onRunExperiment={onRunExperiment}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Normal Startup")).toBeInTheDocument();
    });

    const runButtons = screen.getAllByText("Run");
    await userEvent.click(runButtons[0]);

    expect(onRunExperiment).toHaveBeenCalledWith(1);
  });

  it("handles API error gracefully", async () => {
    mockListScenarios.mockRejectedValue(new Error("Network error"));

    render(
      <ScenariosPage
        onBack={vi.fn()}
        onViewScenario={vi.fn()}
        onRunExperiment={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });

  it("renders retry button on error", async () => {
    mockListScenarios.mockRejectedValue(new Error("Network error"));

    render(
      <ScenariosPage
        onBack={vi.fn()}
        onViewScenario={vi.fn()}
        onRunExperiment={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Retry")).toBeInTheDocument();
    });
  });

  it("calls onBack when back button clicked", async () => {
    const onBack = vi.fn();
    render(
      <ScenariosPage
        onBack={onBack}
        onViewScenario={vi.fn()}
        onRunExperiment={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText("Back to Companies")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("Back to Companies"));
    expect(onBack).toHaveBeenCalledOnce();
  });
});
