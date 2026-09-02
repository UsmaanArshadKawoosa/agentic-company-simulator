import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ExperimentPage } from "./Experiment";

const mockGetExperimentResults = vi.fn();
const mockListRuns = vi.fn();
const mockRunExperiment = vi.fn();

vi.mock("../api/api", () => ({
  api: {
    getExperimentResults: (...args: unknown[]) => mockGetExperimentResults(...args),
    listRuns: (...args: unknown[]) => mockListRuns(...args),
    runExperiment: (...args: unknown[]) => mockRunExperiment(...args),
    seedBuiltinScenarios: vi.fn(),
    listScenarios: vi.fn(),
    getScenario: vi.fn(),
    createScenario: vi.fn(),
    updateScenario: vi.fn(),
    deleteScenario: vi.fn(),
    duplicateScenario: vi.fn(),
    createRun: vi.fn(),
    executeRun: vi.fn(),
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

const mockExperiment = {
  scenario_id: 1,
  scenario_name: "Test Scenario",
  total_runs: 3,
  completed_runs: 2,
  runs: [
    {
      run_id: 1,
      seed: 1000,
      status: "COMPLETED",
      simulation_days: 50,
      final_day: 51,
      metrics: {
        cash: 150000,
        revenue: 25000,
        expenses: 18000,
        profit: 7000,
        active_customers: 120,
        market_share: 0.15,
        valuation: 500000,
        current_day: 51,
      },
    },
    {
      run_id: 2,
      seed: 1100,
      status: "COMPLETED",
      simulation_days: 50,
      final_day: 51,
      metrics: {
        cash: 80000,
        revenue: 15000,
        expenses: 20000,
        profit: -5000,
        active_customers: 80,
        market_share: 0.08,
        valuation: 300000,
        current_day: 51,
      },
    },
  ],
  summary: {
    cash: { best: 150000, worst: 80000, average: 115000, median: 115000 },
    revenue: { best: 25000, worst: 15000, average: 20000, median: 20000 },
    active_customers: { best: 120, worst: 80, average: 100, median: 100 },
    market_share: { best: 0.15, worst: 0.08, average: 0.115, median: 0.115 },
  },
};

const mockRuns = [
  {
    id: 1,
    scenario_id: 1,
    company_id: 10,
    seed: 1000,
    status: "COMPLETED",
    simulation_days: 50,
    configuration_snapshot: {},
    final_metrics: mockExperiment.runs[0].metrics,
    started_at: "2024-01-01T00:00:00Z",
    completed_at: "2024-01-01T00:01:00Z",
    error_message: null,
    created_at: "2024-01-01T00:00:00Z",
  },
  {
    id: 2,
    scenario_id: 1,
    company_id: 11,
    seed: 1100,
    status: "COMPLETED",
    simulation_days: 50,
    configuration_snapshot: {},
    final_metrics: mockExperiment.runs[1].metrics,
    started_at: "2024-01-01T00:00:00Z",
    completed_at: "2024-01-01T00:01:00Z",
    error_message: null,
    created_at: "2024-01-01T00:00:00Z",
  },
];

const defaultProps = {
  scenarioId: 1,
  onBack: vi.fn(),
  onViewRun: vi.fn(),
  onViewCompany: vi.fn(),
};

describe("ExperimentPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    defaultProps.onBack = vi.fn();
    defaultProps.onViewRun = vi.fn();
    defaultProps.onViewCompany = vi.fn();
    mockGetExperimentResults.mockResolvedValue(mockExperiment);
    mockListRuns.mockResolvedValue(mockRuns);
    mockRunExperiment.mockResolvedValue(mockRuns);
  });

  it("renders loading state initially", () => {
    render(<ExperimentPage {...defaultProps} />);
    expect(screen.getByText("Loading experiment results...")).toBeInTheDocument();
  });

  it("renders experiment results after loading", async () => {
    render(<ExperimentPage {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText("Run Results")).toBeInTheDocument();
    });
  });

  it("renders summary cards", async () => {
    render(<ExperimentPage {...defaultProps} />);
    await waitFor(() => {
      const summaryCards = screen.getAllByText(/Cash|Revenue|Customers|Market Share/);
      expect(summaryCards.length).toBeGreaterThanOrEqual(4);
    });
  });

  it("renders run data in table", async () => {
    render(<ExperimentPage {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText("#1")).toBeInTheDocument();
      expect(screen.getByText("#2")).toBeInTheDocument();
    });
  });

  it("renders seed values", async () => {
    render(<ExperimentPage {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText("1000")).toBeInTheDocument();
      expect(screen.getByText("1100")).toBeInTheDocument();
    });
  });

  it("renders export buttons", async () => {
    render(<ExperimentPage {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText("Export CSV")).toBeInTheDocument();
      expect(screen.getByText("Export JSON")).toBeInTheDocument();
    });
  });

  it("renders run experiment button", async () => {
    render(<ExperimentPage {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText("Run Experiment")).toBeInTheDocument();
    });
  });

  it("renders run configuration inputs", async () => {
    render(<ExperimentPage {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText("Runs:")).toBeInTheDocument();
      expect(screen.getByText("Days:")).toBeInTheDocument();
    });
  });

  it("renders empty state when no results", async () => {
    mockGetExperimentResults.mockResolvedValue({
      scenario_id: 1,
      scenario_name: "Test",
      total_runs: 0,
      completed_runs: 0,
      runs: [],
      summary: {},
    });
    mockListRuns.mockResolvedValue([]);

    render(<ExperimentPage {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText("No experiment results yet")).toBeInTheDocument();
    });
  });

  it("renders inspect button for completed runs", async () => {
    render(<ExperimentPage {...defaultProps} />);
    await waitFor(() => {
      const inspectButtons = screen.getAllByText("Detail");
      expect(inspectButtons.length).toBe(2);
    });
  });

  it("calls onViewRun when Detail clicked", async () => {
    const onViewRun = vi.fn();
    render(<ExperimentPage {...defaultProps} onViewRun={onViewRun} />);

    await waitFor(() => {
      expect(screen.getAllByText("Detail").length).toBeGreaterThan(0);
    });

    const detailButtons = screen.getAllByText("Detail");
    await userEvent.click(detailButtons[0]);

    expect(onViewRun).toHaveBeenCalledWith(1);
  });

  it("renders failed runs section if any", async () => {
    mockListRuns.mockResolvedValue([
      ...mockRuns,
      {
        id: 3,
        scenario_id: 1,
        company_id: null,
        seed: 1200,
        status: "FAILED",
        simulation_days: 50,
        configuration_snapshot: {},
        final_metrics: null,
        started_at: "2024-01-01T00:00:00Z",
        completed_at: "2024-01-01T00:01:00Z",
        error_message: "Simulation failed",
        created_at: "2024-01-01T00:00:00Z",
      },
    ]);

    render(<ExperimentPage {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText("Failed Runs")).toBeInTheDocument();
    });
  });

  it("calls onBack when back button clicked", async () => {
    const onBack = vi.fn();
    render(<ExperimentPage {...defaultProps} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Back to Scenarios")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("Back to Scenarios"));
    expect(onBack).toHaveBeenCalledOnce();
  });

  it("handles API error gracefully", async () => {
    mockGetExperimentResults.mockRejectedValue(new Error("Network error"));
    mockListRuns.mockRejectedValue(new Error("Network error"));

    render(<ExperimentPage {...defaultProps} />);
    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });
});
