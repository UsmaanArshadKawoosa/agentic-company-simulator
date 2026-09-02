import { vi } from "vitest";
import { Company, Agent, SimEvent, Objective, Risk, Incident } from "../types/types";

export const mockCompany: Company = {
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

export const mockAgents: Agent[] = [
  {
    id: 1,
    company_id: 1,
    name: "Alice",
    role: "CEO" as const,
    personality: null,
    skills: ["leadership"],
    authority: 100,
    budget: 50000,
    morale: 0.9,
    energy: 0.8,
    workload: 0.3,
    status: "IDLE" as const,
    manager_id: null,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
  {
    id: 2,
    company_id: 1,
    name: "Bob",
    role: "CTO" as const,
    personality: null,
    skills: ["engineering"],
    authority: 80,
    budget: 30000,
    morale: 0.85,
    energy: 0.7,
    workload: 0.4,
    status: "WORKING" as const,
    manager_id: 1,
    created_at: "2024-01-01T00:00:00Z",
    updated_at: "2024-01-01T00:00:00Z",
  },
];

export const mockEvents: SimEvent[] = [
  {
    id: 1,
    company_id: 1,
    actor_id: null,
    event_type: "COMPANY_CREATED",
    description: "Company 'Test Company' was created.",
    target_type: "company",
    target_id: 1,
    meta: {},
    simulation_day: 1,
    created_at: "2024-01-01T00:00:00Z",
  },
];

export const mockObjectives: Objective[] = [
  {
    id: 1,
    company_id: 1,
    parent_id: null,
    title: "Launch MVP",
    description: "Ship the first version",
    objective_type: "STRATEGIC",
    status: "IN_PROGRESS",
    priority: 1,
    progress: 30,
    expected_outcome: "Product launched",
    owner_id: 1,
    created_day: 1,
    completed_day: null,
  },
];

export const mockRisks: Risk[] = [
  {
    id: 1,
    company_id: 1,
    risk_type: "RUNWAY",
    severity: "MEDIUM",
    source: "simulation",
    description: "Cash runway declining",
    affected_entity_type: "company",
    affected_entity_id: 1,
    status: "ACTIVE",
    mitigation_actions: null,
    detected_day: 5,
    resolved_day: null,
  },
];

export const mockIncidents: Incident[] = [
  {
    id: 1,
    company_id: 1,
    incident_type: "PRODUCT_DELAY",
    severity: "HIGH",
    description: "Feature delivery delayed",
    status: "ACTIVE",
    detected_day: 10,
    resolved_day: null,
    root_cause: "Underestimated complexity",
    impact_assessment: "2 week delay",
    related_risk_id: null,
  },
];

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export function createMockApi(overrides: Record<string, any> = {}) {
  const base = {
    listCompanies: vi.fn().mockResolvedValue([mockCompany]),
    createCompany: vi.fn().mockResolvedValue(mockCompany),
    getCompany: vi.fn().mockResolvedValue(mockCompany),
    getAgents: vi.fn().mockResolvedValue(mockAgents),
    getEvents: vi.fn().mockResolvedValue(mockEvents),
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
    getObjectives: vi.fn().mockResolvedValue(mockObjectives),
    createObjective: vi.fn().mockResolvedValue(mockObjectives[0]),
    updateObjective: vi.fn().mockResolvedValue(mockObjectives[0]),
    getRisks: vi.fn().mockResolvedValue(mockRisks),
    createRisk: vi.fn().mockResolvedValue(mockRisks[0]),
    getIncidents: vi.fn().mockResolvedValue(mockIncidents),
    getResources: vi.fn().mockResolvedValue([]),
    getOperationalStatus: vi.fn().mockResolvedValue({}),
  };
  return { ...base, ...overrides };
}
