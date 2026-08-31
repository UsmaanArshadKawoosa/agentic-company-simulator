import { useCallback, useEffect, useMemo, useState } from "react";
import { api } from "../api/api";
import { useWebSocket, ConnectionState } from "../hooks/useWebSocket";
import { OperationsPanel } from "../components/OperationsPanel";
import { Agent, Company, SimEvent, Employee, JobOpening, Candidate, WorkforceSummary, FinancialMetrics, ValuationData, Investor, FundingRound, PipelineEntry, BudgetRequest } from "../types/types";

interface DashboardData {
  company: any;
  agents: any[];
  financials: any;
  customers: any;
  product: any;
  strategy: any;
  campaigns: any[];
  sales: any[];
  tasks: any[];
}

export function CommandCenter({ companyId }: { companyId: number }) {
  const [company, setCompany] = useState<Company | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [events, setEvents] = useState<SimEvent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [speed, setSpeed] = useState<string>("1x");
  const [isRunning, setIsRunning] = useState(false);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [jobs, setJobs] = useState<JobOpening[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [workforce, setWorkforce] = useState<WorkforceSummary | null>(null);

  // Phase 10 state
  const [financials, setFinancials] = useState<FinancialMetrics | null>(null);
  const [valuation, setValuation] = useState<ValuationData | null>(null);
  const [investors, setInvestors] = useState<Investor[]>([]);
  const [fundingRounds, setFundingRounds] = useState<FundingRound[]>([]);
  const [pipeline, setPipeline] = useState<PipelineEntry[]>([]);
  const [budgetRequests, setBudgetRequests] = useState<BudgetRequest[]>([]);
  const [showFinance, setShowFinance] = useState(false);
  const [showOperations, setShowOperations] = useState(false);

  const { connectionState, messages, clearMessages } = useWebSocket(companyId);

  const refresh = useCallback(async () => {
    try {
      const [c, a, e, d, emp, j, cand, wf, fin, val, inv, rounds, pipe, budgets] = await Promise.all([
        api.getCompany(companyId),
        api.getAgents(companyId),
        api.getEvents(companyId),
        api.getDashboard(companyId).catch(() => null),
        api.getEmployees(companyId).catch(() => []),
        api.getJobs(companyId).catch(() => []),
        api.getCandidates(companyId).catch(() => []),
        api.getWorkforce(companyId).catch(() => null),
        api.getFinancials(companyId).catch(() => null),
        api.getValuation(companyId).catch(() => null),
        api.getInvestors(companyId).catch(() => []),
        api.getFundingRounds(companyId).catch(() => []),
        api.getPipeline(companyId).catch(() => []),
        api.getBudgetRequests(companyId).catch(() => []),
      ]);
      setCompany(c);
      setAgents(a);
      setEvents(e);
      setDashboard(d);
      setEmployees(emp);
      setJobs(j);
      setCandidates(cand);
      setWorkforce(wf);
      setFinancials(fin);
      setValuation(val);
      setInvestors(inv);
      setFundingRounds(rounds);
      setPipeline(pipe);
      setBudgetRequests(budgets);
      setIsRunning(c.status === "RUNNING");
    } catch (err) {
      setError(String(err));
    }
  }, [companyId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Process WebSocket messages to update state.
  useEffect(() => {
    if (messages.length === 0) return;
    const lastMsg = messages[messages.length - 1];
    if (lastMsg.type === "simulation.tick" || lastMsg.type === "agent.decision") {
      refresh();
    }
  }, [messages, refresh]);

  const start = useCallback(async () => {
    setLoading(true);
    try {
      await api.startSimulation(companyId);
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [companyId, refresh]);

  const pause = useCallback(async () => {
    setLoading(true);
    try {
      await api.pauseSimulation(companyId);
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [companyId, refresh]);

  const tick = useCallback(async () => {
    setLoading(true);
    try {
      await api.tickSimulation(companyId);
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [companyId, refresh]);

  const resume = useCallback(async () => {
    setLoading(true);
    try {
      await api.resumeSimulation(companyId, speed);
      setIsRunning(true);
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [companyId, speed, refresh]);

  const connectionIndicator = useMemo(() => {
    const colors: Record<ConnectionState, string> = {
      connecting: "bg-yellow-500",
      connected: "bg-emerald-500",
      disconnected: "bg-slate-500",
      reconnecting: "bg-orange-500",
    };
    const labels: Record<ConnectionState, string> = {
      connecting: "CONNECTING",
      connected: "LIVE",
      disconnected: "OFFLINE",
      reconnecting: "RECONNECTING",
    };
    return (
      <span className="flex items-center gap-2 text-xs font-medium">
        <span className={`h-2.5 w-2.5 rounded-full ${colors[connectionState]} animate-pulse`} />
        {labels[connectionState]}
      </span>
    );
  }, [connectionState]);

  if (!company) {
    return <div className="flex h-screen items-center justify-center text-slate-400">Loading company...</div>;
  }

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
      {/* Top Bar */}
      <header className="flex items-center justify-between border-b border-slate-800 bg-slate-900 px-6 py-3">
        <div className="flex items-center gap-6">
          <h1 className="text-lg font-bold">{company.name}</h1>
          <span className="rounded bg-slate-800 px-2 py-1 text-xs">
            Day {company.current_day}
          </span>
          <span className={`rounded px-2 py-1 text-xs font-medium ${
            company.status === "RUNNING" ? "bg-emerald-900 text-emerald-300" :
            company.status === "PAUSED" ? "bg-yellow-900 text-yellow-300" :
            company.status === "FAILED" ? "bg-red-900 text-red-300" :
            "bg-slate-800 text-slate-300"
          }`}>
            {company.status}
          </span>
        </div>
        <div className="flex items-center gap-4">
          {connectionIndicator}
          <button
            onClick={() => setShowOperations(!showOperations)}
            className="rounded bg-orange-900 px-3 py-1.5 text-xs font-semibold hover:bg-orange-700"
          >
            {showOperations ? "Hide Operations" : "Operations"}
          </button>
          <button
            onClick={() => setShowFinance(!showFinance)}
            className="rounded bg-indigo-900 px-3 py-1.5 text-xs font-semibold hover:bg-indigo-700"
          >
            {showFinance ? "Hide Finance" : "Finance"}
          </button>
        </div>
      </header>

      {/* Controls */}
      <div className="flex items-center gap-3 border-b border-slate-800 bg-slate-900/50 px-6 py-2">
        {!isRunning ? (
          <button
            onClick={start}
            disabled={loading}
            className="rounded bg-emerald-600 px-3 py-1.5 text-xs font-semibold hover:bg-emerald-500 disabled:opacity-50"
          >
            Start
          </button>
        ) : (
          <button
            onClick={pause}
            disabled={loading}
            className="rounded bg-yellow-600 px-3 py-1.5 text-xs font-semibold hover:bg-yellow-500 disabled:opacity-50"
          >
            Pause
          </button>
        )}
        <button
          onClick={tick}
          disabled={loading || !isRunning}
          className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-semibold hover:bg-indigo-500 disabled:opacity-50"
        >
          Tick
        </button>
        <button
          onClick={resume}
          disabled={loading || isRunning}
          className="rounded bg-blue-600 px-3 py-1.5 text-xs font-semibold hover:bg-blue-500 disabled:opacity-50"
        >
          Resume
        </button>
        <div className="ml-4 flex items-center gap-2">
          <span className="text-xs text-slate-400">Speed:</span>
          {["1x", "2x", "5x", "10x"].map((s) => (
            <button
              key={s}
              onClick={() => setSpeed(s)}
              className={`rounded px-2 py-1 text-xs ${
                speed === s ? "bg-indigo-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"
              }`}
            >
              {s}
            </button>
          ))}
        </div>
        {error && <span className="ml-auto text-xs text-rose-400">{error}</span>}
      </div>

      {/* Main Content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar - Agent Hierarchy */}
        <aside className="w-64 border-r border-slate-800 bg-slate-900/30 p-4 overflow-y-auto">
          <h2 className="mb-3 text-xs font-semibold uppercase text-slate-500">Agents</h2>
          <AgentHierarchy agents={agents} />
        </aside>

        {/* Center - Activity Feed */}
        <main className="flex flex-1 flex-col overflow-hidden">
          <div className="flex-1 overflow-y-auto p-4">
            <h2 className="mb-3 text-xs font-semibold uppercase text-slate-500">Live Activity</h2>
            <ActivityFeed events={events} agents={agents} />
          </div>
        </main>

        {/* Right Sidebar - Metrics + Finance */}
        <aside className="w-80 border-l border-slate-800 bg-slate-900/30 p-4 overflow-y-auto">
          <h2 className="mb-3 text-xs font-semibold uppercase text-slate-500">Company Health</h2>
          {dashboard && <MetricsPanel dashboard={dashboard} />}
          {workforce && (
            <div className="mt-6">
              <h2 className="mb-3 text-xs font-semibold uppercase text-slate-500">Workforce</h2>
              <WorkforcePanel workforce={workforce} employees={employees} jobs={jobs} candidates={candidates} />
            </div>
          )}

          {/* Phase 10 Finance/Capital Section */}
          {showFinance && (
            <div className="mt-6 space-y-4">
              <h2 className="mb-3 text-xs font-semibold uppercase text-slate-500">Finance & Capital</h2>

              {/* Financial Metrics */}
              {financials && (
                <div className="rounded bg-slate-800/50 p-3 space-y-2">
                  <h3 className="text-[10px] font-semibold uppercase text-slate-500">Financial Metrics</h3>
                  <div className="grid grid-cols-2 gap-2 text-xs">
                    <Metric label="Cash" value={`$${financials.cash.toLocaleString()}`} color="text-emerald-400" />
                    <Metric label="Burn/Day" value={`$${financials.daily_burn.toLocaleString()}`} color="text-red-400" />
                    <Metric label="Runway" value={financials.runway_days ? `${financials.runway_days.toFixed(1)} days` : "∞"} color="text-blue-400" />
                    <Metric label="Health" value={financials.financial_health} color={
                      financials.financial_health === "HEALTHY" ? "text-emerald-400" :
                      financials.financial_health === "AT_RISK" ? "text-yellow-400" :
                      financials.financial_health === "CRITICAL" ? "text-orange-400" : "text-red-400"
                    } />
                  </div>
                  <div className="text-[10px] text-slate-400">
                    Risk: {financials.financial_risk_level} | Score: {(financials.financial_health_score * 100).toFixed(0)}%
                  </div>
                </div>
              )}

              {/* Valuation */}
              {valuation && (
                <div className="rounded bg-slate-800/50 p-3 space-y-2">
                  <h3 className="text-[10px] font-semibold uppercase text-slate-500">Valuation</h3>
                  <div className="text-lg font-bold text-emerald-400">${valuation.valuation.toLocaleString()}</div>
                  <div className="text-[10px] text-slate-400">
                    ARR: ${valuation.annual_revenue.toLocaleString()}
                  </div>
                </div>
              )}

              {/* Funding Rounds */}
              {fundingRounds.length > 0 && (
                <div className="rounded bg-slate-800/50 p-3 space-y-2">
                  <h3 className="text-[10px] font-semibold uppercase text-slate-500">Funding Rounds</h3>
                  {fundingRounds.map((r) => (
                    <div key={r.id} className="flex items-center justify-between text-xs">
                      <span className="font-medium">{r.round_stage}</span>
                      <span className={r.status === "CLOSED" ? "text-emerald-400" : r.status === "FAILED" ? "text-red-400" : "text-yellow-400"}>
                        ${r.amount_raised.toLocaleString()} / ${r.amount_requested.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Pipeline */}
              {pipeline.length > 0 && (
                <div className="rounded bg-slate-800/50 p-3 space-y-2">
                  <h3 className="text-[10px] font-semibold uppercase text-slate-500">Fundraising Pipeline</h3>
                  {pipeline.slice(0, 5).map((p) => (
                    <div key={p.id} className="flex items-center justify-between text-xs">
                      <span className="font-medium">{p.stage}</span>
                      <span className={
                        p.status === "INVESTED" ? "text-emerald-400" :
                        p.status === "PASSED" ? "text-red-400" : "text-yellow-400"
                      }>
                        {p.status}
                      </span>
                    </div>
                  ))}
                </div>
              )}

              {/* Budget Requests */}
              {budgetRequests.length > 0 && (
                <div className="rounded bg-slate-800/50 p-3 space-y-2">
                  <h3 className="text-[10px] font-semibold uppercase text-slate-500">Budget Requests</h3>
                  {budgetRequests.slice(0, 5).map((r) => (
                    <div key={r.id} className="flex items-center justify-between text-xs">
                      <span className="font-medium truncate max-w-[120px]">{r.purpose}</span>
                      <span className={
                        r.status === "ALLOCATED" ? "text-emerald-400" :
                        r.status === "REJECTED" ? "text-red-400" : "text-yellow-400"
                      }>
                        ${r.amount.toLocaleString()}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
          {showOperations && (
            <div className="mt-6">
              <OperationsPanel companyId={companyId} />
            </div>
          )}
        </aside>
      </div>

      {/* Bottom Panel - Agent Details */}
      <footer className="h-48 border-t border-slate-800 bg-slate-900/50 p-4 overflow-x-auto">
        <h2 className="mb-3 text-xs font-semibold uppercase text-slate-500">Agent Activity</h2>
        <div className="flex gap-4">
          {agents.map((agent) => (
            <AgentCard key={agent.id} agent={agent} events={events.filter(e => e.actor_id === agent.id).slice(0, 5)} />
          ))}
        </div>
      </footer>
    </div>
  );
}

function AgentHierarchy({ agents }: { agents: Agent[] }) {
  const ceo = agents.find((a) => a.role === "CEO");
  const cto = agents.find((a) => a.role === "CTO");
  const cmo = agents.find((a) => a.role === "CMO");
  const engineer = agents.find((a) => a.role === "ENGINEER");

  const roleColors: Record<string, string> = {
    CEO: "border-amber-500 bg-amber-950",
    CTO: "border-blue-500 bg-blue-950",
    CMO: "border-purple-500 bg-purple-950",
    ENGINEER: "border-emerald-500 bg-emerald-950",
  };

  const AgentNode = ({ agent, children }: { agent: Agent | undefined; children?: React.ReactNode }) => {
    if (!agent) return null;
    return (
      <div className="ml-3">
        <div className={`rounded border-l-2 p-2 ${roleColors[agent.role] || "border-slate-600 bg-slate-900"}`}>
          <div className="text-xs font-semibold">{agent.role}</div>
          <div className="text-[10px] text-slate-400">{agent.name}</div>
        </div>
        {children && <div className="ml-3 border-l border-slate-700 pl-2">{children}</div>}
      </div>
    );
  };

  return (
    <div className="space-y-1">
      <AgentNode agent={ceo}>
        <AgentNode agent={cto}>
          <AgentNode agent={engineer} />
        </AgentNode>
        <AgentNode agent={cmo} />
      </AgentNode>
    </div>
  );
}

function ActivityFeed({ events, agents }: { events: SimEvent[]; agents: Agent[] }) {
  const agentMap = new Map(agents.map((a) => [a.id, a]));
  const recentEvents = events.slice(-50).reverse();

  const formatEvent = (event: SimEvent) => {
    const agent = event.actor_id ? agentMap.get(event.actor_id) : null;
    const agentLabel = agent ? (
      <span className={`font-medium ${
        agent.role === "CEO" ? "text-amber-400" :
        agent.role === "CTO" ? "text-blue-400" :
        agent.role === "CMO" ? "text-purple-400" :
        "text-emerald-400"
      }`}>{agent.role}</span>
    ) : (
      <span className="text-slate-500">System</span>
    );

    return (
      <div key={event.id} className="flex gap-2 border-b border-slate-800/50 py-1.5 text-xs">
        <span className="w-12 shrink-0 text-slate-500">Day {event.simulation_day}</span>
        <span className="w-16 shrink-0">{agentLabel}</span>
        <span className="text-slate-300">{event.description}</span>
      </div>
    );
  };

  return (
    <div className="space-y-0.5">
      {recentEvents.length === 0 ? (
        <div className="py-8 text-center text-sm text-slate-500">No activity yet</div>
      ) : (
        recentEvents.map(formatEvent)
      )}
    </div>
  );
}

function MetricsPanel({ dashboard }: { dashboard: any }) {
  const { company, financials, customers, product, strategy } = dashboard;

  return (
    <div className="space-y-4">
      {/* Financials */}
      <div>
        <h3 className="mb-2 text-[10px] font-semibold uppercase text-slate-500">Financials</h3>
        <div className="grid grid-cols-2 gap-2">
          <Metric label="Cash" value={`$${financials?.cash?.toLocaleString() || 0}`} color="text-emerald-400" />
          <Metric label="Revenue" value={`$${financials?.revenue?.toLocaleString() || 0}`} color="text-blue-400" />
          <Metric label="Expenses" value={`$${financials?.expenses?.toLocaleString() || 0}`} color="text-red-400" />
          <Metric label="Customers" value={customers?.active || 0} color="text-purple-400" />
        </div>
      </div>

      {/* Product */}
      <div>
        <h3 className="mb-2 text-[10px] font-semibold uppercase text-slate-500">Product</h3>
        <div className="space-y-1">
          <ProgressBar label="Readiness" value={product?.readiness || 0} color="bg-emerald-500" />
          <ProgressBar label="Quality" value={product?.quality || 0} color="bg-blue-500" />
        </div>
      </div>

      {/* Strategy */}
      <div>
        <h3 className="mb-2 text-[10px] font-semibold uppercase text-slate-500">Strategy</h3>
        <div className="space-y-1 text-xs">
          <div className="flex justify-between"><span className="text-slate-400">Segment</span><span>{strategy?.target_segment || "—"}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">Price</span><span>${strategy?.price || 0}</span></div>
          <div className="flex justify-between"><span className="text-slate-400">Mkt Share</span><span>{((strategy?.market_share || 0) * 100).toFixed(1)}%</span></div>
        </div>
      </div>
    </div>
  );
}

function Metric({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="rounded bg-slate-800/50 p-2">
      <div className="text-[10px] text-slate-500">{label}</div>
      <div className={`text-sm font-semibold ${color}`}>{value}</div>
    </div>
  );
}

function ProgressBar({ label, value, color }: { label: string; value: number; color: string }) {
  const pct = Math.round(value * 100);
  return (
    <div>
      <div className="flex justify-between text-[10px] text-slate-400">
        <span>{label}</span>
        <span>{pct}%</span>
      </div>
      <div className="h-1.5 rounded-full bg-slate-800">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

function AgentCard({ agent, events }: { agent: Agent; events: SimEvent[] }) {
  const roleColors: Record<string, string> = {
    CEO: "border-amber-500",
    CTO: "border-blue-500",
    CMO: "border-purple-500",
    ENGINEER: "border-emerald-500",
  };

  return (
    <div className={`min-w-[200px] rounded border-l-2 bg-slate-800/50 p-3 ${roleColors[agent.role] || "border-slate-600"}`}>
      <div className="mb-1 flex items-center justify-between">
        <span className="text-xs font-semibold">{agent.role}</span>
        <span className={`rounded px-1.5 py-0.5 text-[10px] ${
          agent.status === "WORKING" ? "bg-emerald-900 text-emerald-300" :
          agent.status === "BLOCKED" ? "bg-red-900 text-red-300" :
          "bg-slate-700 text-slate-400"
        }`}>{agent.status}</span>
      </div>
      <div className="mb-2 text-[10px] text-slate-500">{agent.name}</div>
      <div className="space-y-0.5">
        {events.slice(0, 3).map((e) => (
          <div key={e.id} className="truncate text-[10px] text-slate-400">
            {e.description}
          </div>
        ))}
        {events.length === 0 && <div className="text-[10px] text-slate-600">No recent activity</div>}
      </div>
    </div>
  );
}

function WorkforcePanel({ workforce, employees, jobs, candidates }: { workforce: WorkforceSummary; employees: Employee[]; jobs: JobOpening[]; candidates: Candidate[] }) {
  const { overview } = workforce;
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-2">
        <Metric label="Headcount" value={overview.headcount} color="text-slate-300" />
        <Metric label="Active" value={overview.active_count} color="text-emerald-400" />
        <Metric label="Payroll" value={`$${overview.payroll.toLocaleString()}`} color="text-red-400" />
        <Metric label="Capacity" value={overview.total_capacity.toFixed(1)} color="text-blue-400" />
        <Metric label="Morale" value={`${(overview.avg_morale * 100).toFixed(0)}%`} color="text-purple-400" />
        <Metric label="Productivity" value={`${(overview.avg_productivity * 100).toFixed(0)}%`} color="text-amber-400" />
      </div>

      {jobs.length > 0 && (
        <div>
          <h3 className="mb-1 text-[10px] font-semibold uppercase text-slate-500">Open Positions</h3>
          <div className="space-y-1">
            {jobs.slice(0, 5).map((j) => (
              <div key={j.id} className="flex items-center justify-between rounded bg-slate-800/50 px-2 py-1 text-[10px]">
                <span className="font-medium">{j.title}</span>
                <span className="text-slate-400">{j.role}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {candidates.length > 0 && (
        <div>
          <h3 className="mb-1 text-[10px] font-semibold uppercase text-slate-500">Candidates</h3>
          <div className="space-y-1">
            {candidates.slice(0, 5).map((c) => (
              <div key={c.id} className="flex items-center justify-between rounded bg-slate-800/50 px-2 py-1 text-[10px]">
                <span className="font-medium">{c.name}</span>
                <span className="text-slate-400">{(c.hiring_score * 100).toFixed(0)}% fit</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {employees.length > 0 && (
        <div>
          <h3 className="mb-1 text-[10px] font-semibold uppercase text-slate-500">Employees</h3>
          <div className="space-y-1">
            {employees.slice(0, 8).map((e) => (
              <div key={e.id} className="flex items-center justify-between rounded bg-slate-800/50 px-2 py-1 text-[10px]">
                <span className="font-medium">{e.name}</span>
                <span className="text-slate-400">{e.role} · ${e.salary.toLocaleString()}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
