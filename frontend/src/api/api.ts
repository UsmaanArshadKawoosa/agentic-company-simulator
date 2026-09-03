import { Agent, Company, SimEvent, SimulationState, Employee, JobOpening, Candidate, WorkforceSummary, Objective, Risk, Incident, ResourceAllocation, HistoryResponse, MarketData, CompetitorData, SalesOpportunity, TimelineEvent, TimelineResponse, Decision, DecisionsResponse, Scenario, ScenarioCreate, SimulationRun, ExperimentResult } from "../types/types";
import { resolveApiBaseUrl } from "./base";

const BASE = resolveApiBaseUrl();

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    let detail: string;
    try {
      const json = await res.json();
      detail = (json && (json.detail || json.message)) || JSON.stringify(json);
    } catch {
      try {
        detail = await res.text();
      } catch {
        detail = `Request failed (${res.status})`;
      }
    }
    throw new Error(typeof detail === "string" && detail ? detail : `Request failed (${res.status})`);
  }
  return (await res.json()) as T;
}

export const api = {
  // Companies
  listCompanies: () => request<Company[]>("/companies"),
  createCompany: (name: string, mission: string) =>
    request<Company>("/companies", {
      method: "POST",
      body: JSON.stringify({ name, mission }),
    }),
  getCompany: (id: number) => request<Company>(`/companies/${id}`),
  getAgents: (id: number) => request<Agent[]>(`/companies/${id}/agents`),
  getEvents: (id: number) => request<SimEvent[]>(`/companies/${id}/events`),
  // Simulation
  startSimulation: (id: number) =>
    request<{ message: string; state: SimulationState }>(
      `/simulation/${id}/start`,
      { method: "POST" }
    ),
  pauseSimulation: (id: number) =>
    request<{ message: string; state: SimulationState }>(
      `/simulation/${id}/pause`,
      { method: "POST" }
    ),
  tickSimulation: (id: number) =>
    request<{ message: string; state: SimulationState }>(
      `/simulation/${id}/tick`,
      { method: "POST" }
    ),
  resumeSimulation: (id: number, speed: string = "1x") =>
    request<{ message: string; state: SimulationState }>(
      `/simulation/${id}/resume?speed=${speed}`,
      { method: "POST" }
    ),
  getSimulation: (id: number) => request<SimulationState>(`/simulation/${id}`),
  getDashboard: (id: number) => request<any>(`/simulation/${id}/dashboard`),
  getTimeline: (id: number, params?: { day?: number; event_type?: string; agent_id?: number; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.day) qs.set("day", String(params.day));
    if (params?.event_type) qs.set("event_type", params.event_type);
    if (params?.agent_id) qs.set("agent_id", String(params.agent_id));
    if (params?.limit) qs.set("limit", String(params.limit));
    return request<any[]>(`/simulation/${id}/timeline?${qs.toString()}`);
  },
  getPlans: (id: number) => request<any[]>(`/simulation/${id}/plans`),
  getExpectations: (id: number) => request<any[]>(`/simulation/${id}/expectations`),
  getAgentMetrics: (id: number) => request<any[]>(`/simulation/${id}/agent-metrics`),
  getMarket: (id: number) => request<any>(`/simulation/${id}/market`),
  getCompetitors: (id: number) => request<any[]>(`/simulation/${id}/competitors`),
  getStrategy: (id: number) => request<any>(`/simulation/${id}/strategy`),
  getCampaigns: (id: number) => request<any[]>(`/simulation/${id}/campaigns`),
  getSales: (id: number) => request<any[]>(`/simulation/${id}/sales`),
  // Analytics endpoints
  getHistory: (id: number, limit: number = 50) => request<HistoryResponse>(`/simulation/${id}/history?limit=${limit}`),
  getMarketData: (id: number) => request<MarketData>(`/simulation/${id}/market`),
  getCompetitorsData: (id: number) => request<CompetitorData[]>(`/simulation/${id}/competitors`),
  getSalesOpportunities: (id: number) => request<SalesOpportunity[]>(`/simulation/${id}/sales`),
  getAgentMetricsData: (id: number) => request<any[]>(`/simulation/${id}/agent-metrics`),
  // Timeline & Decisions endpoints
  getTimelineEvents: (id: number, params?: { event_type?: string; agent_id?: number; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.event_type) qs.set("event_type", params.event_type);
    if (params?.agent_id) qs.set("agent_id", String(params.agent_id));
    if (params?.limit) qs.set("limit", String(params.limit));
    return request<TimelineEvent[]>(`/simulation/${id}/timeline?${qs.toString()}`);
  },
  getDecisions: (id: number, params?: { agent_id?: number; limit?: number }) => {
    const qs = new URLSearchParams();
    if (params?.agent_id) qs.set("agent_id", String(params.agent_id));
    if (params?.limit) qs.set("limit", String(params.limit));
    return request<DecisionsResponse>(`/simulation/${id}/decisions?${qs.toString()}`);
  },
  // Workforce
  getEmployees: (id: number) => request<Employee[]>(`/workforce/companies/${id}/employees`),
  getJobs: (id: number) => request<JobOpening[]>(`/workforce/companies/${id}/jobs`),
  getCandidates: (id: number) => request<Candidate[]>(`/workforce/companies/${id}/candidates`),
  getWorkforce: (id: number) => request<WorkforceSummary>(`/workforce/companies/${id}/workforce`),
  // Phase 10 financial/capital endpoints
  getFinancials: (id: number) => request<any>(`/simulation/${id}/financials`),
  getValuation: (id: number) => request<any>(`/simulation/${id}/valuation`),
  getInvestors: (id: number) => request<any[]>(`/simulation/${id}/investors`),
  getFundingRounds: (id: number) => request<any[]>(`/simulation/${id}/funding-rounds`),
  getPipeline: (id: number) => request<any[]>(`/simulation/${id}/pipeline`),
  getCapTable: (id: number) => request<any[]>(`/simulation/${id}/cap-table`),
  getBudgetRequests: (id: number) => request<any[]>(`/simulation/${id}/budget-requests`),
  // Phase 11 operations endpoints
  getObjectives: (id: number) => request<Objective[]>(`/operations/companies/${id}/objectives`),
  createObjective: (id: number, title: string, description: string = "", objective_type: string = "OPERATIONAL", priority: number = 1) =>
    request<Objective>(`/operations/companies/${id}/objectives?title=${encodeURIComponent(title)}&description=${encodeURIComponent(description)}&objective_type=${objective_type}&priority=${priority}`, { method: "POST" }),
  updateObjective: (companyId: number, objectiveId: number, updates: { progress?: number; priority?: number; status?: string }) => {
    const qs = new URLSearchParams();
    if (updates.progress !== undefined) qs.set("progress", String(updates.progress));
    if (updates.priority !== undefined) qs.set("priority", String(updates.priority));
    if (updates.status !== undefined) qs.set("status", updates.status);
    return request<Objective>(`/operations/companies/${companyId}/objectives/${objectiveId}?${qs.toString()}`, { method: "PATCH" });
  },
  getRisks: (id: number) => request<Risk[]>(`/operations/companies/${id}/risks`),
  createRisk: (id: number, risk_type: string, severity: string = "MEDIUM", source: string = "", description: string = "") =>
    request<Risk>(`/operations/companies/${id}/risks?risk_type=${encodeURIComponent(risk_type)}&severity=${severity}&source=${encodeURIComponent(source)}&description=${encodeURIComponent(description)}`, { method: "POST" }),
  getIncidents: (id: number) => request<Incident[]>(`/operations/companies/${id}/incidents`),
  getResources: (id: number) => request<ResourceAllocation[]>(`/operations/companies/${id}/resources`),
  getOperationalStatus: (id: number) => request<{
    company_id: number;
    current_day: number;
    attention: Record<string, unknown>;
    resources: Record<string, unknown>;
    risks: Array<{ id: number; risk_type: string; severity: string; status: string; detected_day: number }>;
    incidents: Array<{ id: number; incident_type: string; severity: string; status: string; detected_day: number }>;
    objectives: Array<{ id: number; title: string; status: string; priority: number; progress: number }>;
  }>(`/operations/companies/${id}/status`),
  // --- Scenario & Experiment endpoints ---
  seedBuiltinScenarios: () => request<{ message: string }>(`/scenarios/seed-builtins`, { method: "POST" }),
  listScenarios: () => request<Scenario[]>(`/scenarios`),
  getScenario: (id: number) => request<Scenario>(`/scenarios/${id}`),
  createScenario: (scenario: ScenarioCreate) => request<Scenario>(`/scenarios`, { method: "POST", body: JSON.stringify(scenario) }),
  updateScenario: (id: number, scenario: Partial<ScenarioCreate>) => request<Scenario>(`/scenarios/${id}`, { method: "PUT", body: JSON.stringify(scenario) }),
  deleteScenario: (id: number) => request<void>(`/scenarios/${id}`, { method: "DELETE" }),
  duplicateScenario: (id: number) => request<Scenario>(`/scenarios/${id}/duplicate`, { method: "POST" }),
  createRun: (scenarioId: number, seed: number | null, simulationDays: number) => request<SimulationRun>(`/scenarios/${scenarioId}/runs`, { method: "POST", body: JSON.stringify({ seed, simulation_days: simulationDays }) }),
  listRuns: (scenarioId: number) => request<SimulationRun[]>(`/scenarios/${scenarioId}/runs`),
  executeRun: (runId: number) => request<SimulationRun>(`/scenarios/runs/${runId}/execute`, { method: "POST" }),
  runExperiment: (scenarioId: number, numRuns: number, simulationDays: number) => request<SimulationRun[]>(`/scenarios/${scenarioId}/run-experiment?num_runs=${numRuns}&simulation_days=${simulationDays}`, { method: "POST" }),
   getExperimentResults: (scenarioId: number) => request<ExperimentResult>(`/scenarios/${scenarioId}/experiment`),
   getSimulationRun: (runId: number) => request<SimulationRun>(`/scenarios/runs/${runId}`),
};
