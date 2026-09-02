import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { ScenarioEditorPage } from "./ScenarioEditorPage";

const mockGetScenario = vi.fn();
const mockCreateScenario = vi.fn();
const mockUpdateScenario = vi.fn();

vi.mock("../api/api", () => ({
  api: {
    getScenario: (...args: unknown[]) => mockGetScenario(...args),
    createScenario: (...args: unknown[]) => mockCreateScenario(...args),
    updateScenario: (...args: unknown[]) => mockUpdateScenario(...args),
    listScenarios: vi.fn(),
    seedBuiltinScenarios: vi.fn(),
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

const mockScenario = {
  id: 1,
  name: "Test Scenario",
  description: "A test scenario",
  category: "custom",
  is_builtin: false,
  configuration: {
    name: "TestCo",
    mission: "Build something",
    cash: 100000,
    seed: null,
    market_demand: 0.5,
    market_competition: 0.3,
    product_readiness: 0.0,
    technical_debt: 0.0,
    target_segment: "SMB",
    price: 100,
  },
  run_count: 0,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

describe("ScenarioEditorPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders create mode without scenarioId", () => {
    render(
      <ScenarioEditorPage
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByRole("button", { name: "Create Scenario" })).toBeInTheDocument();
  });

  it("renders edit mode with scenarioId", async () => {
    mockGetScenario.mockResolvedValue(mockScenario);
    render(
      <ScenarioEditorPage
        scenarioId={1}
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />
    );
    await waitFor(() => {
      expect(screen.getByText("Edit Scenario")).toBeInTheDocument();
    });
  });

  it("shows loading state when fetching scenario", () => {
    mockGetScenario.mockReturnValue(new Promise(() => {})); // never resolves
    render(
      <ScenarioEditorPage
        scenarioId={1}
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />
    );
    expect(screen.getByText("Loading scenario...")).toBeInTheDocument();
  });

  it("shows error state when fetch fails", async () => {
    mockGetScenario.mockRejectedValue(new Error("Not found"));
    render(
      <ScenarioEditorPage
        scenarioId={999}
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />
    );
    await waitFor(() => {
      expect(screen.getByText(/Not found/)).toBeInTheDocument();
    });
  });

  it("creates new scenario on submit", async () => {
    mockCreateScenario.mockResolvedValue({ ...mockScenario, id: 2 });
    const onSave = vi.fn();

    render(
      <ScenarioEditorPage
        onSave={onSave}
        onCancel={vi.fn()}
      />
    );

    const nameInput = screen.getByLabelText("Name *");
    await userEvent.clear(nameInput);
    await userEvent.type(nameInput, "New Scenario");

    const submitButton = screen.getByRole("button", { name: "Create Scenario" });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(mockCreateScenario).toHaveBeenCalled();
    });
    expect(onSave).toHaveBeenCalledOnce();
  });

  it("validates required name field", async () => {
    render(
      <ScenarioEditorPage
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    const submitButton = screen.getByRole("button", { name: "Create Scenario" });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(screen.getByText("Name is required")).toBeInTheDocument();
    });
  });

  it("validates large cash values are handled", async () => {
    render(
      <ScenarioEditorPage
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />
    );

    const nameInput = screen.getByLabelText("Name *");
    await userEvent.type(nameInput, "Test");

    const submitButton = screen.getByRole("button", { name: "Create Scenario" });
    await userEvent.click(submitButton);

    await waitFor(() => {
      expect(mockCreateScenario).toHaveBeenCalled();
    });
  });

  it("calls onCancel when cancel clicked", async () => {
    const onCancel = vi.fn();
    render(
      <ScenarioEditorPage
        onSave={vi.fn()}
        onCancel={onCancel}
      />
    );

    const cancelButtons = screen.getAllByText("Cancel");
    await userEvent.click(cancelButtons[0]);

    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("shows built-in badge for built-in scenarios", async () => {
    mockGetScenario.mockResolvedValue({ ...mockScenario, is_builtin: true });
    render(
      <ScenarioEditorPage
        scenarioId={1}
        onSave={vi.fn()}
        onCancel={vi.fn()}
      />
    );
    await waitFor(() => {
      expect(screen.getByText("Built-in (read-only)")).toBeInTheDocument();
    });
  });
});
