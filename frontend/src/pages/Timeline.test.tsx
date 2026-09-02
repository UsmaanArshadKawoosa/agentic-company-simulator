import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { TimelinePage } from "./Timeline";

const mockGetCompany = vi.fn();
const mockGetAgents = vi.fn();
const mockGetTimelineEvents = vi.fn();
const mockGetDecisions = vi.fn();

vi.mock("../api/api", () => ({
  api: {
    getCompany: (...args: unknown[]) => mockGetCompany(...args),
    getAgents: (...args: unknown[]) => mockGetAgents(...args),
    getTimelineEvents: (...args: unknown[]) => mockGetTimelineEvents(...args),
    getDecisions: (...args: unknown[]) => mockGetDecisions(...args),
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

const agentsData = [
  { id: 1, company_id: 1, name: "CEO Agent", role: "CEO", status: "ACTIVE", current_task: null, created_day: 1 },
  { id: 2, company_id: 1, name: "CFO Agent", role: "CFO", status: "ACTIVE", current_task: null, created_day: 1 },
];

const eventsData = [
  {
    id: 1,
    day: 10,
    event_type: "DECISION",
    description: "Changed pricing strategy",
    actor_id: 1,
    meta: { action: "SET_PRICE", confidence: 0.85 },
  },
  {
    id: 2,
    day: 10,
    event_type: "FINANCIAL_SUMMARY",
    description: "Revenue increased",
    actor_id: null,
    meta: { financial: { cash: 100000, revenue: 5000 } },
  },
];

const decisionsData = {
  company_id: 1,
  count: 2,
  decisions: [
    {
      id: 1,
      agent_id: 1,
      action: "SET_PRICE",
      reasoning: "Market conditions favor higher pricing",
      outcome: "Price updated successfully",
      simulation_day: 10,
      evaluation: "SUCCESSFUL",
      confidence: 0.85,
      expected_outcome: "Increase revenue by 10%",
      expected_value: 10.0,
      actual_value: 12.5,
      expectation_status: "MET",
    },
    {
      id: 2,
      agent_id: 2,
      action: "HIRE",
      reasoning: "Need more engineering capacity",
      outcome: "Job posting created",
      simulation_day: 9,
      evaluation: "PARTIAL",
      confidence: 0.7,
      expected_outcome: "Hire senior engineer",
      expected_value: 1.0,
      actual_value: 0.0,
      expectation_status: "PENDING",
    },
  ],
};

describe("TimelinePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetCompany.mockResolvedValue(companyData);
    mockGetAgents.mockResolvedValue(agentsData);
    mockGetTimelineEvents.mockResolvedValue(eventsData);
    mockGetDecisions.mockResolvedValue(decisionsData);
  });

  it("renders loading state initially", () => {
    render(<TimelinePage companyId={1} onBack={vi.fn()} />);
    expect(screen.getByText("Loading timeline...")).toBeInTheDocument();
  });

  it("renders company name in header after loading", async () => {
    render(<TimelinePage companyId={1} onBack={vi.fn()} />);
    await waitFor(() => {
      expect(screen.getByText(/Test Company/)).toBeInTheDocument();
    });
  });

  it("renders timeline events", async () => {
    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Changed pricing strategy")).toBeInTheDocument();
      expect(screen.getByText("Revenue increased")).toBeInTheDocument();
    });
  });

  it("renders event day markers", async () => {
    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getAllByText("Day 10")).toHaveLength(2);
    });
  });

  it("renders event category labels", async () => {
    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      const categoryBadges = screen.getAllByText(/Decision|Financial/);
      expect(categoryBadges.length).toBeGreaterThanOrEqual(2);
    });
  });

  it("renders tabs", async () => {
    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByRole("button", { name: "Timeline" })).toBeInTheDocument();
      expect(screen.getByRole("button", { name: /Decisions/ })).toBeInTheDocument();
    });
  });

  it("switches to decisions tab", async () => {
    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Changed pricing strategy")).toBeInTheDocument();
    });

    const decisionsTab = screen.getByRole("button", { name: /Decisions/ });
    await userEvent.click(decisionsTab);

    await waitFor(() => {
      expect(screen.getByText("SET_PRICE")).toBeInTheDocument();
      expect(screen.getByText("HIRE")).toBeInTheDocument();
    });
  });

  it("renders decision table with columns", async () => {
    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Changed pricing strategy")).toBeInTheDocument();
    });

    const decisionsTab = screen.getByRole("button", { name: /Decisions/ });
    await userEvent.click(decisionsTab);

    await waitFor(() => {
      expect(screen.getByText("Confidence")).toBeInTheDocument();
      expect(screen.getByText("Expected")).toBeInTheDocument();
      expect(screen.getByText("Actual")).toBeInTheDocument();
      expect(screen.getByText("Evaluation")).toBeInTheDocument();
    });
  });

  it("renders evaluation badges", async () => {
    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Changed pricing strategy")).toBeInTheDocument();
    });

    const decisionsTab = screen.getByRole("button", { name: /Decisions/ });
    await userEvent.click(decisionsTab);

    await waitFor(() => {
      expect(screen.getByText("SUCCESSFUL")).toBeInTheDocument();
      expect(screen.getByText("PARTIAL")).toBeInTheDocument();
    });
  });

  it("renders decision performance summary", async () => {
    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Changed pricing strategy")).toBeInTheDocument();
    });

    const decisionsTab = screen.getByRole("button", { name: /Decisions/ });
    await userEvent.click(decisionsTab);

    await waitFor(() => {
      expect(screen.getByText("Total Decisions")).toBeInTheDocument();
      expect(screen.getByText("2")).toBeInTheDocument();
      expect(screen.getByText("Successful")).toBeInTheDocument();
    });
  });

  it("renders category filter", async () => {
    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("All Events")).toBeInTheDocument();
    });
  });

  it("renders agent filter", async () => {
    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("All Agents")).toBeInTheDocument();
    });
  });

  it("renders limit selector", async () => {
    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("10")).toBeInTheDocument();
      expect(screen.getByText("25")).toBeInTheDocument();
      expect(screen.getByText("50")).toBeInTheDocument();
    });
  });

  it("calls onBack when back button clicked", async () => {
    const onBack = vi.fn();
    render(<TimelinePage companyId={1} onBack={onBack} />);

    await waitFor(() => {
      expect(screen.getByText("Back to Command Center")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("Back to Command Center"));
    expect(onBack).toHaveBeenCalledOnce();
  });

  it("handles empty events", async () => {
    mockGetTimelineEvents.mockResolvedValue([]);

    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/No simulation events yet/)).toBeInTheDocument();
    });
  });

  it("handles API errors gracefully", async () => {
    mockGetCompany.mockRejectedValue(new Error("Network error"));
    mockGetAgents.mockRejectedValue(new Error("Network error"));
    mockGetTimelineEvents.mockRejectedValue(new Error("Network error"));
    mockGetDecisions.mockRejectedValue(new Error("Network error"));

    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
    });
  });

  it("renders retry button on error", async () => {
    mockGetCompany.mockRejectedValue(new Error("Network error"));
    mockGetAgents.mockRejectedValue(new Error("Network error"));
    mockGetTimelineEvents.mockRejectedValue(new Error("Network error"));
    mockGetDecisions.mockRejectedValue(new Error("Network error"));

    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Retry")).toBeInTheDocument();
    });
  });

  it("renders refresh button", async () => {
    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Refresh")).toBeInTheDocument();
    });
  });

  it("expands event details on click", async () => {
    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Changed pricing strategy")).toBeInTheDocument();
    });

    await userEvent.click(screen.getByText("Changed pricing strategy"));

    await waitFor(() => {
      expect(screen.getByText("Details")).toBeInTheDocument();
    });
  });

  it("shows pending evaluation count", async () => {
    mockGetDecisions.mockResolvedValue({
      company_id: 1,
      count: 1,
      decisions: [
        {
          id: 1,
          agent_id: 1,
          action: "SET_PRICE",
          reasoning: "Test",
          outcome: null,
          simulation_day: 10,
          evaluation: "UNKNOWN",
          confidence: 0.5,
          expected_outcome: null,
          expected_value: null,
          actual_value: null,
          expectation_status: null,
        },
      ],
    });

    render(<TimelinePage companyId={1} onBack={vi.fn()} />);

    await waitFor(() => {
      expect(screen.getByText("Changed pricing strategy")).toBeInTheDocument();
    });

    const decisionsTab = screen.getByRole("button", { name: /Decisions/ });
    await userEvent.click(decisionsTab);

    await waitFor(() => {
      expect(screen.getByText(/pending evaluation/)).toBeInTheDocument();
    });
  });
});
