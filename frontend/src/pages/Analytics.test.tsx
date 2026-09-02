import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { AnalyticsPage } from "./Analytics";

const mockGetCompany = vi.fn();
const mockGetHistory = vi.fn();
const mockGetFinancials = vi.fn();
const mockGetValuation = vi.fn();
const mockGetWorkforce = vi.fn();
const mockGetMarketData = vi.fn();
const mockGetCompetitorsData = vi.fn();
const mockGetSalesOpportunities = vi.fn();
const mockGetObjectives = vi.fn();
const mockGetRisks = vi.fn();
const mockGetIncidents = vi.fn();

vi.mock("../api/api", () => ({
  api: {
    getCompany: (...args: unknown[]) => mockGetCompany(...args),
    getHistory: (...args: unknown[]) => mockGetHistory(...args),
    getFinancials: (...args: unknown[]) => mockGetFinancials(...args),
    getValuation: (...args: unknown[]) => mockGetValuation(...args),
    getWorkforce: (...args: unknown[]) => mockGetWorkforce(...args),
    getMarketData: (...args: unknown[]) => mockGetMarketData(...args),
    getCompetitorsData: (...args: unknown[]) => mockGetCompetitorsData(...args),
    getSalesOpportunities: (...args: unknown[]) => mockGetSalesOpportunities(...args),
    getObjectives: (...args: unknown[]) => mockGetObjectives(...args),
    getRisks: (...args: unknown[]) => mockGetRisks(...args),
    getIncidents: (...args: unknown[]) => mockGetIncidents(...args),
  },
}));

const companyData = {
  id: 1,
  name: "Test Company",
  mission: "Build great products",
  cash: 100000,
  revenue: 5000,
  expenses: 3000,
  current_day: 10,
  status: "RUNNING" as const,
  seed: 42,
  created_at: "2024-01-01T00:00:00Z",
  updated_at: "2024-01-01T00:00:00Z",
};

const historyData = {
  company_id: 1,
  data_points: 3,
  series: [
    { day: 1, cash: 100000, revenue: 0, expenses: 1000, profit: -1000, active_customers: 0, daily_burn: 1000, runway_days: 100, financial_health_score: 0.9 },
    { day: 2, cash: 99000, revenue: 500, expenses: 1200, profit: -700, active_customers: 1, daily_burn: 700, runway_days: 141, financial_health_score: 0.85 },
    { day: 3, cash: 98300, revenue: 1000, expenses: 1500, profit: -500, active_customers: 2, daily_burn: 500, runway_days: 196, financial_health_score: 0.88 },
  ],
};

describe("AnalyticsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetCompany.mockResolvedValue(companyData);
    mockGetHistory.mockResolvedValue(historyData);
    mockGetFinancials.mockResolvedValue({
      cash: 98300,
      revenue: 1000,
      expenses: 1500,
      profit: -500,
      daily_burn: 500,
      runway_days: 196,
      financial_health_score: 0.88,
      financial_health: "HEALTHY",
      financial_risk_level: "LOW",
    });
    mockGetValuation.mockResolvedValue({
      valuation: 1000000,
      annual_revenue: 12000,
      growth_factor: 1.2,
      readiness_bonus: 0.1,
      quality_bonus: 0.05,
      market_share_bonus: 0.02,
      customer_bonus: 0.03,
      runway_factor: 1.0,
    });
    mockGetWorkforce.mockResolvedValue({
      company_id: 1,
      current_day: 10,
      overview: {
        headcount: 5,
        active_count: 4,
        onboarding_count: 1,
        underperforming_count: 0,
        payroll: 5000,
        total_capacity: 20,
        avg_morale: 0.8,
        avg_productivity: 0.75,
      },
      capacity_by_role: { ENGINEER: 10, SALES: 5, MARKETING: 5 },
    });
    mockGetMarketData.mockResolvedValue({
      segments: [
        { name: "SMB", type: "SMB", size: 1000, demand: 0.6, price_sensitivity: 0.5, avg_customer_value: 500, sales_cycle_days: 14 },
        { name: "Enterprise", type: "ENTERPRISE", size: 500, demand: 0.4, price_sensitivity: 0.3, avg_customer_value: 5000, sales_cycle_days: 60 },
      ],
      company: { target_segment: "SMB", price: 100, market_share: 0.05, brand_strength: 0.3 },
    });
    mockGetCompetitorsData.mockResolvedValue([
      { id: 1, name: "Competitor A", market_share: 0.3, price: 120, product_quality: 0.7, brand_strength: 0.6, target_segment: "SMB", strategy: "cost_leadership" },
      { id: 2, name: "Competitor B", market_share: 0.25, price: 150, product_quality: 0.8, brand_strength: 0.7, target_segment: "Enterprise", strategy: "differentiation" },
    ]);
    mockGetSalesOpportunities.mockResolvedValue([
      { id: 1, name: "Deal A", segment: "SMB", value: 5000, stage: "PROSPECT", created_day: 5, expected_close_day: 20 },
      { id: 2, name: "Deal B", segment: "Enterprise", value: 25000, stage: "NEGOTIATE", created_day: 8, expected_close_day: 25 },
    ]);
    mockGetObjectives.mockResolvedValue([
      { id: 1, company_id: 1, parent_id: null, title: "Launch MVP", description: null, objective_type: "STRATEGIC", status: "ACTIVE", priority: 1, progress: 0.5, expected_outcome: null, owner_id: 1, created_day: 1, completed_day: null },
      { id: 2, company_id: 1, parent_id: null, title: "Hire Engineer", description: null, objective_type: "OPERATIONAL", status: "COMPLETED", priority: 2, progress: 1.0, expected_outcome: null, owner_id: 1, created_day: 2, completed_day: 5 },
    ]);
    mockGetRisks.mockResolvedValue([
      { id: 1, company_id: 1, risk_type: "RUNWAY", severity: "MEDIUM", source: null, description: null, affected_entity_type: null, affected_entity_id: null, status: "ACTIVE", mitigation_actions: null, detected_day: 3, resolved_day: null },
    ]);
    mockGetIncidents.mockResolvedValue([]);
  });

  it("renders loading state initially", () => {
    render(<AnalyticsPage companyId={1} onBack={vi.fn()} />);
    expect(screen.getByText("Loading analytics...")).toBeInTheDocument();
  });

  it("renders company name in header after loading", async () => {
    render(<AnalyticsPage companyId={1} onBack={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText(/Test Company/)).toBeInTheDocument();
    });
  });

  it("renders executive KPI cards", async () => {
    render(<AnalyticsPage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Cash")).toBeInTheDocument();
      expect(screen.getByText("$100,000")).toBeInTheDocument();
      expect(screen.getByText("Revenue")).toBeInTheDocument();
    });
  });

  it("renders financial KPIs", async () => {
    render(<AnalyticsPage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Daily Burn")).toBeInTheDocument();
      expect(screen.getByText("$500")).toBeInTheDocument();
      expect(screen.getByText("Runway")).toBeInTheDocument();
    });
  });

  it("renders workforce section", async () => {
    render(<AnalyticsPage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Headcount")).toBeInTheDocument();
      expect(screen.getByText("5")).toBeInTheDocument();
      expect(screen.getByText("Active")).toBeInTheDocument();
    });
  });

  it("renders operational health section", async () => {
    render(<AnalyticsPage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Active Objectives")).toBeInTheDocument();
      expect(screen.getByText("Active Risks")).toBeInTheDocument();
      expect(screen.getByText("Open Incidents")).toBeInTheDocument();
    });
  });

  it("renders time range selector", async () => {
    render(<AnalyticsPage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Last 10")).toBeInTheDocument();
      expect(screen.getByText("Last 25")).toBeInTheDocument();
      expect(screen.getByText("Last 50")).toBeInTheDocument();
    });
  });

  it("calls onBack when back button clicked", async () => {
    const onBack = vi.fn();
    render(<AnalyticsPage companyId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Cash")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("Back to Command Center"));
    expect(onBack).toHaveBeenCalledOnce();
  });

  it("changes time range when clicked", async () => {
    render(<AnalyticsPage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Cash")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("Last 50"));
    expect(screen.getByText("Last 50")).toHaveClass("bg-indigo-600");
  });

  it("renders refresh button", async () => {
    render(<AnalyticsPage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Refresh")).toBeInTheDocument();
    });
  });

  it("handles API errors gracefully", async () => {
    mockGetCompany.mockRejectedValueOnce(new Error("Network error"));
    mockGetHistory.mockRejectedValueOnce(new Error("Network error"));
    mockGetFinancials.mockRejectedValueOnce(new Error("Network error"));
    mockGetValuation.mockRejectedValueOnce(new Error("Network error"));
    mockGetWorkforce.mockRejectedValueOnce(new Error("Network error"));
    mockGetMarketData.mockRejectedValueOnce(new Error("Network error"));
    mockGetCompetitorsData.mockRejectedValueOnce(new Error("Network error"));
    mockGetSalesOpportunities.mockRejectedValueOnce(new Error("Network error"));
    mockGetObjectives.mockRejectedValueOnce(new Error("Network error"));
    mockGetRisks.mockRejectedValueOnce(new Error("Network error"));
    mockGetIncidents.mockRejectedValueOnce(new Error("Network error"));

    render(<AnalyticsPage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Failed to load analytics data/)).toBeInTheDocument();
    });
  });

  it("renders chart sections", async () => {
    render(<AnalyticsPage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Financial Performance")).toBeInTheDocument();
      expect(screen.getByText("Market Intelligence")).toBeInTheDocument();
      expect(screen.getByText("Workforce")).toBeInTheDocument();
    });
  });
});
