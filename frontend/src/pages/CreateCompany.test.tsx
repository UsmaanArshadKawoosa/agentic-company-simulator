import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, it, expect, vi, beforeEach } from "vitest";
import { CreateCompany } from "../pages/CreateCompany";

const mockCreateCompany = vi.fn();

vi.mock("../api/api", () => ({
  api: {
    listCompanies: vi.fn().mockResolvedValue([]),
    createCompany: (...args: unknown[]) => mockCreateCompany(...args),
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

describe("CreateCompany", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockCreateCompany.mockReset();
  });

  it("renders form with name and mission fields", () => {
    render(<CreateCompany onCreated={vi.fn()} onCancel={vi.fn()} />);
    expect(screen.getByRole("textbox", { name: "Name" })).toBeInTheDocument();
    expect(screen.getByRole("textbox", { name: "Mission" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create Company" })).toBeInTheDocument();
  });

  it("submits form and calls onCreated with company id", async () => {
    const onCreated = vi.fn();
    mockCreateCompany.mockResolvedValue({ id: 1, name: "New Startup" });
    render(<CreateCompany onCreated={onCreated} onCancel={vi.fn()} />);

    await userEvent.type(screen.getByRole("textbox", { name: "Name" }), "New Startup");
    await userEvent.type(screen.getByRole("textbox", { name: "Mission" }), "Democratize AI");
    await userEvent.click(screen.getByRole("button", { name: "Create Company" }));

    await waitFor(() => {
      expect(mockCreateCompany).toHaveBeenCalledWith("New Startup", "Democratize AI");
      expect(onCreated).toHaveBeenCalledWith(1);
    });
  });

  it("shows loading state during submission", async () => {
    let resolveCreate: (value: { id: number }) => void;
    mockCreateCompany.mockReturnValue(
      new Promise((resolve) => { resolveCreate = resolve; })
    );
    render(<CreateCompany onCreated={vi.fn()} onCancel={vi.fn()} />);

    await userEvent.type(screen.getByRole("textbox", { name: "Name" }), "Test");
    await userEvent.click(screen.getByRole("button", { name: "Create Company" }));

    expect(screen.getByText("Creating...")).toBeInTheDocument();
    // Button text changes to "Creating..." while submitting
    expect(screen.getByRole("button", { name: "Creating..." })).toBeDisabled();

    resolveCreate!({ id: 1 });
    await waitFor(() => {
      expect(screen.queryByText("Creating...")).not.toBeInTheDocument();
    });
  });

  it("shows error message on API failure", async () => {
    mockCreateCompany.mockRejectedValue(new Error("Company name already exists"));
    render(<CreateCompany onCreated={vi.fn()} onCancel={vi.fn()} />);

    await userEvent.type(screen.getByRole("textbox", { name: "Name" }), "Duplicate");
    await userEvent.click(screen.getByRole("button", { name: "Create Company" }));

    await waitFor(() => {
      expect(screen.getByText(/already exists/i)).toBeInTheDocument();
    });
  });

  it("calls cancel when Cancel button is clicked", async () => {
    const onCancel = vi.fn();
    render(<CreateCompany onCreated={vi.fn()} onCancel={onCancel} />);

    await userEvent.click(screen.getByRole("button", { name: "Cancel" }));
    expect(onCancel).toHaveBeenCalledOnce();
  });

  it("does not render Cancel button when onCancel is not provided", () => {
    render(<CreateCompany onCreated={vi.fn()} />);
    expect(screen.queryByRole("button", { name: "Cancel" })).not.toBeInTheDocument();
  });

  it("validates required name field", () => {
    render(<CreateCompany onCreated={vi.fn()} onCancel={vi.fn()} />);
    const nameInput = screen.getByRole("textbox", { name: "Name" });
    expect(nameInput).toBeRequired();
  });
});
