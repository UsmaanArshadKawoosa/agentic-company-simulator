import { Agent, Company, SimEvent, SimulationState, Employee, JobOpening, Candidate, WorkforceSummary } from "../types/types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Request failed (${res.status}): ${text}`);
  }
  return (await res.json()) as T;
}

export const api = {
  createCompany: (name: string, mission: string) =>
    request<Company>("/companies", {
      method: "POST",
      body: JSON.stringify({ name, mission }),
    }),
  getCompany: (id: number) => request<Company>(`/companies/${id}`),
  getAgents: (id: number) => request<Agent[]>(`/companies/${id}/agents`),
  getEvents: (id: number) => request<SimEvent[]>(`/companies/${id}/events`),
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
};
