export type AgentRole = "CEO" | "CTO" | "CMO" | "ENGINEER";
export type AgentStatus = "IDLE" | "WORKING" | "BLOCKED" | "OFFLINE";
export type CompanyStatus =
  | "CREATED"
  | "RUNNING"
  | "PAUSED"
  | "FAILED"
  | "COMPLETED";

export interface Company {
  id: number;
  name: string;
  mission: string;
  cash: number;
  revenue: number;
  expenses: number;
  current_day: number;
  status: CompanyStatus;
  seed?: number;
  infrastructure_cost?: number;
  product_readiness?: number;
  product_quality?: number;
  technical_debt?: number;
  marketing_effectiveness?: number;
  sales_effectiveness?: number;
  target_segment?: string;
  price?: number;
  positioning?: string;
  brand_strength?: number;
  market_share_cache?: number;
  created_at: string;
  updated_at: string;
}

export interface Agent {
  id: number;
  company_id: number;
  name: string;
  role: AgentRole;
  personality: Record<string, number> | null;
  skills: string[] | null;
  authority: number;
  budget: number;
  morale: number;
  energy: number;
  workload: number;
  status: AgentStatus;
  manager_id: number | null;
  created_at: string;
  updated_at: string;
}

export interface SimEvent {
  id: number;
  company_id: number;
  actor_id: number | null;
  event_type: string;
  description: string;
  target_type: string | null;
  target_id: number | null;
  meta: Record<string, unknown> | null;
  simulation_day: number;
  created_at: string;
}

export interface SimulationState {
  company_id: number;
  status: CompanyStatus;
  current_day: number;
  agents: Agent[];
  recent_events: SimEvent[];
  agent_count: number;
  event_count: number;
}

export interface Employee {
  id: number;
  company_id: number;
  name: string;
  role: string;
  status: string;
  salary: number;
  capacity: number;
  skills: string[] | null;
  experience: number;
  performance_score: number;
  morale: number;
  productivity: number;
  hired_day: number | null;
  fired_day: number | null;
  manager_id: number | null;
}

export interface JobOpening {
  id: number;
  company_id: number;
  role: string;
  title: string;
  description: string;
  required_skills: string[] | null;
  salary_min: number;
  salary_max: number;
  capacity_required: number;
  created_day: number;
  status: string;
}

export interface Candidate {
  id: number;
  company_id: number;
  job_opening_id: number | null;
  name: string;
  role: string;
  skills: string[] | null;
  experience: number;
  salary_expectation: number;
  productivity_potential: number;
  culture_fit: number;
  reliability: number;
  hiring_score: number;
  status: string;
  evaluation_notes: string | null;
}

export interface WorkforceSummary {
  company_id: number;
  current_day: number;
  overview: {
    headcount: number;
    active_count: number;
    onboarding_count: number;
    underperforming_count: number;
    payroll: number;
    total_capacity: number;
    avg_morale: number;
    avg_productivity: number;
  };
  capacity_by_role: Record<string, number>;
}

// Phase 10 financial/capital types
export interface FinancialMetrics {
  cash: number;
  revenue: number;
  expenses: number;
  profit: number;
  daily_burn: number;
  runway_days: number | null;
  financial_health_score: number;
  financial_health: string;
  financial_risk_level: string;
}

export interface ValuationData {
  valuation: number;
  annual_revenue: number;
  growth_factor: number;
  readiness_bonus: number;
  quality_bonus: number;
  market_share_bonus: number;
  customer_bonus: number;
  runway_factor: number;
}

export interface Investor {
  id: number;
  name: string;
  preferred_stage: string;
  check_size_min: number;
  check_size_max: number;
  risk_tolerance: number;
  sector_preference: string;
  ownership_expectation: number;
  reputation: number;
  interest_score: number;
}

export interface FundingRound {
  id: number;
  round_stage: string;
  amount_requested: number;
  amount_raised: number;
  valuation: number;
  pre_money_valuation: number;
  post_money_valuation: number;
  equity_sold: number;
  status: string;
  day_opened: number;
  day_closed: number | null;
}

export interface PipelineEntry {
  id: number;
  investor_id: number | null;
  funding_round_id: number | null;
  status: string;
  stage: string;
  interest_score: number;
  notes: string | null;
  day_updated: number;
}

export interface CapTableEntry {
  id: number;
  owner_type: string;
  owner_id: number | null;
  owner_name: string;
  ownership_percentage: number;
  shares: number;
  notes: string | null;
}

export interface BudgetRequest {
  id: number;
  requester_id: number;
  approver_id: number | null;
  amount: number;
  approved_amount: number;
  purpose: string;
  status: string;
  requested_day: number;
  decided_day: number | null;
  decision_notes: string | null;
}
