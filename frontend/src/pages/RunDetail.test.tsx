import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { RunDetailPage } from "./RunDetail";

const mockGetScenario = vi.fn();
const mockGetSimulationRun = vi.fn();

vi.mock("../api/api", () => ({
  api: {
    getScenario: (...args: unknown[]) => mockGetScenario(...args),
    getSimulationRun: (...args: unknown[]) => mockGetSimulationRun(...args),
    seedBuiltinScenarios: vi.fn(),
    listScenarios: vi.fn(),
    createScenario: vi.fn(),
    updateScenario: vi.fn(),
    deleteScenario: vi.fn(),
    duplicateScenario: vi.fn(),
    createRun: vi.fn(),
    listRuns: vi.fn(),
    executeRun: vi.fn(),
    runExperiment: vi.fn(),
    getExperimentResults: vi.fn(),
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

const mockRun = {
  id: 1,
  scenario_id: 1,
  company_id: 10,
  seed: 1000,
  status: "COMPLETED",
  simulation_days: 50,
  configuration_snapshot: {
    name: "TestCo",
    mission: "Build something",
    cash: 100000,
    market_demand: 0.5,
    market_competition: 0.3,
  },
  final_metrics: {
    current_day: 51,
    cash: 150000,
    revenue: 25000,
    expenses: 18000,
    profit: 7000,
    active_customers: 120,
    market_share: 0.15,
    valuation: 500000,
    product_readiness: 0.6,
  },
  started_at: "2024-01-01T00:00:00Z",
  completed_at: "2024-01-01T00:05:00Z",
  error_message: null,
  created_at: "2024-01-01T00:00:00Z",
};

const mockScenario = {
  id: 1,
  name: "Test Scenario",
  description: "Test",
  category: "custom",
  is_builtin: false,
  configuration: {},
  run_count: 1,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

describe("RunDetailPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetSimulationRun.mockResolvedValue(mockRun);
    mockGetScenario.mockResolvedValue(mockScenario);
  });

  it("renders loading state initially", () => {
    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );
    expect(screen.getByText("Loading run details...")).toBeInTheDocument();
  });

  it("renders run details after loading", async () => {
    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText("Run Overview")).toBeInTheDocument();
    });
  });

  it("renders run ID in title", async () => {
    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText("Run #1")).toBeInTheDocument();
    });
  });

  it("renders seed and status", async () => {
    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText("1000")).toBeInTheDocument();
    });
  });

  it("renders final metrics for completed runs", async () => {
    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText("Final Metrics")).toBeInTheDocument();
    });
  });

  it("renders configuration snapshot", async () => {
    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText("Configuration Snapshot")).toBeInTheDocument();
    });
  });

  it("renders configuration snapshot values", async () => {
    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getAllByText("TestCo").length).toBeGreaterThanOrEqual(1);
    });
  });

  it("handles run not found error", async () => {
    mockGetSimulationRun.mockRejectedValue(new Error("Run not found"));

    render(
      <RunDetailPage runId={999} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText(/not found|error/i)).toBeInTheDocument();
    });
  });

  it("calls onBack when back button clicked", async () => {
    const onBack = vi.fn();
    render(
      <RunDetailPage runId={1} onBack={onBack} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText("Back to Experiment")).toBeInTheDocument();
    });

    const backButton = screen.getByText("Back to Experiment");
    backButton.click();
    expect(onBack).toHaveBeenCalledOnce();
  });

  it("calls onOpenAnalytics when Analytics button clicked", async () => {
    const onOpenAnalytics = vi.fn();
    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={onOpenAnalytics} onOpenTimeline={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText("Open Analytics")).toBeInTheDocument();
    });

    const analyticsButton = screen.getByText("Open Analytics");
    analyticsButton.click();
    expect(onOpenAnalytics).toHaveBeenCalledWith(10);
  });

    it("loads and displays scenario name after run loads", async () => {
    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText("Run Overview")).toBeInTheDocument();
    });

    expect(mockGetSimulationRun).toHaveBeenCalledWith(1);
    await waitFor(() => {
      expect(mockGetScenario).toHaveBeenCalledWith(mockRun.scenario_id);
    });
  });

  it("renders scenario name in subtitle", async () => {
    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Run #1/i })).toBeInTheDocument();
    });

    const subtitle = screen.getByText("Test Scenario", { selector: "p" });
    expect(subtitle).toBeInTheDocument();
  });

  it("calls onOpenTimeline when Timeline button clicked", async () => {
    const onOpenTimeline = vi.fn();
    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={onOpenTimeline} />
    );

    await waitFor(() => {
      expect(screen.getByText("Open Timeline")).toBeInTheDocument();
    });

    const timelineButton = screen.getByText("Open Timeline");
    timelineButton.click();
    expect(onOpenTimeline).toHaveBeenCalledWith(10);
  });

  it("calls onOpenTimeline when View Decisions clicked", async () => {
    const onOpenTimeline = vi.fn();
    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={onOpenTimeline} />
    );

    await waitFor(() => {
      expect(screen.getByText("View Decisions")).toBeInTheDocument();
    });

    const decisionsButton = screen.getByText("View Decisions");
    decisionsButton.click();
    expect(onOpenTimeline).toHaveBeenCalledWith(10);
  });

  it("does not render action buttons for non-completed runs", async () => {
    mockGetSimulationRun.mockResolvedValue({
      ...mockRun,
      status: "PENDING",
      company_id: 10,
    });

    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.queryByText("Open Analytics")).not.toBeInTheDocument();
    });
    expect(screen.queryByText("Open Timeline")).not.toBeInTheDocument();
    expect(screen.queryByText("View Decisions")).not.toBeInTheDocument();
  });

  it("does not render action buttons when company_id is null", async () => {
    mockGetSimulationRun.mockResolvedValue({
      ...mockRun,
      company_id: null,
    });

    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.queryByText("Open Analytics")).not.toBeInTheDocument();
    });
  });

  it("renders retry button on error", async () => {
    mockGetSimulationRun.mockRejectedValue(new Error("Network error"));

    render(


      <RunDetailPage runId={999} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );

     await waitFor(() => {
      expect(screen.getByText("Retry")).toBeInTheDocument();
    });
  });

  it("retry button re-fetches run data", async () => {
    mockGetSimulationRun.mockRejectedValueOnce(new Error("Network error"));
    mockGetSimulationRun.mockResolvedValueOnce(mockRun);
    mockGetScenario.mockResolvedValueOnce(mockScenario);

    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText("Retry")).toBeInTheDocument();
    });

    const retryButton = screen.getByText("Retry");
    retryButton.click();

    await waitFor(() => {
      expect(screen.getByText("Run Overview")).toBeInTheDocument();
    });
    expect(mockGetSimulationRun).toHaveBeenCalledTimes(2);
  });

  it("handles failed run status", async () => {
    mockGetSimulationRun.mockResolvedValue({
      ...mockRun,
      status: "FAILED",
      error_message: "Simulation crashed",
      final_metrics: null,
    });

    render(
      <RunDetailPage runId={1} onBack={vi.fn()} onOpenAnalytics={vi.fn()} onOpenTimeline={vi.fn()} />
    );

    await waitFor(() => {
      expect(screen.getByText("Run Failed")).toBeInTheDocument();
    });
  });
});
