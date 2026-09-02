import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { CompanyList } from "../pages/CompanyList";

const mockListCompanies = vi.fn();

vi.mock("../api/api", () => ({
  api: {
    listCompanies: (...args: unknown[]) => mockListCompanies(...args),
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

const mockCompany = {
  id: 1,
  name: "Test Company",
  mission: "Build great products",
  cash: 100000,
  revenue: 0,
  expenses: 0,
  current_day: 1,
  status: "CREATED" as const,
  seed: 42,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

describe("CompanyList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockListCompanies.mockResolvedValue([mockCompany]);
  });

  it("renders loading state initially", () => {
    mockListCompanies.mockReturnValue(new Promise(() => {})); // never resolves
    render(<CompanyList onSelect={vi.fn()} onCreateNew={vi.fn()} />);
    expect(screen.getByText("Loading companies...")).toBeInTheDocument();
  });

  it("renders empty state when no companies exist", async () => {
    mockListCompanies.mockResolvedValue([]);
    render(<CompanyList onSelect={vi.fn()} onCreateNew={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText(/No companies yet/i)).toBeInTheDocument();
    });
  });

  it("renders list of companies", async () => {
    mockListCompanies.mockResolvedValue([
      mockCompany,
      { ...mockCompany, id: 2, name: "Second Company" },
    ]);
    render(<CompanyList onSelect={vi.fn()} onCreateNew={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Test Company")).toBeInTheDocument();
      expect(screen.getByText("Second Company")).toBeInTheDocument();
    });
  });

  it("displays company status and day", async () => {
    render(<CompanyList onSelect={vi.fn()} onCreateNew={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("CREATED")).toBeInTheDocument();
      expect(screen.getByText("Day 1")).toBeInTheDocument();
    });
  });

  it("calls onSelect when a company is clicked", async () => {
    const onSelect = vi.fn();
    render(<CompanyList onSelect={onSelect} onCreateNew={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Test Company")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("Test Company"));
    expect(onSelect).toHaveBeenCalledWith(1);
  });

  it("calls onCreateNew when Create Company button is clicked", async () => {
    const onCreateNew = vi.fn();
    mockListCompanies.mockResolvedValue([]);
    render(<CompanyList onSelect={vi.fn()} onCreateNew={onCreateNew} />);

    await waitFor(() => {
      expect(screen.getByText(/No companies yet/i)).toBeInTheDocument();
    });

    const createButtons = screen.getAllByText("Create Company");
    await userEvent.click(createButtons[0]);
    expect(onCreateNew).toHaveBeenCalledOnce();
  });

  it("shows error state when API fails", async () => {
    mockListCompanies.mockRejectedValue(new Error("Network error"));
    render(<CompanyList onSelect={vi.fn()} onCreateNew={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Network error/i)).toBeInTheDocument();
    });
  });

  it("shows cash and revenue for each company", async () => {
    render(<CompanyList onSelect={vi.fn()} onCreateNew={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/\$100,000/)).toBeInTheDocument();
    });
  });
});
