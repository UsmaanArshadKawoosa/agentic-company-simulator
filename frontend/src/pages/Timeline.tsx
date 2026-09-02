import { useCallback, useEffect, useState } from "react";
import { api } from "../api/api";
import { Company, Agent, TimelineEvent, Decision, EventCategory } from "../types/types";
import { LoadingState, ErrorState } from "../components/analytics/AnalyticsComponents";

interface TimelinePageProps {
  companyId: number;
  onBack: () => void;
}

const EVENT_CATEGORIES: { value: EventCategory; label: string }[] = [
  { value: "all", label: "All Events" },
  { value: "decisions", label: "Decisions" },
  { value: "financial", label: "Financial" },
  { value: "market", label: "Market" },
  { value: "workforce", label: "Workforce" },
  { value: "product", label: "Product" },
  { value: "operations", label: "Operations" },
  { value: "risk", label: "Risks" },
  { value: "incident", label: "Incidents" },
  { value: "agent", label: "Agent Activity" },
];

const DECISION_TYPES = ["DECISION", "DECIDE", "DECISION_EVALUATED"];
const FINANCIAL_TYPES = ["FINANCIAL_SUMMARY", "FUNDING_ROUND_CREATED", "INVESTMENT_DECIDED", "BUDGET_APPROVED", "BUDGET_REJECTED", "FINANCIAL_DISTRESS"];
const MARKET_TYPES = ["MARKET_UPDATE", "CUSTOMER_ACQUIRED", "CUSTOMER_CHURNED", "PRICE_CHANGED", "TARGET_SEGMENT_CHANGED", "MARKET_SHARE_CHANGED", "COMPETITOR_ACTION"];
const WORKFORCE_TYPES = ["EMPLOYEE_HIRED", "EMPLOYEE_TERMINATED", "EMPLOYEE_PROMOTED", "EMPLOYEE_PERFORMANCE_UPDATED", "WORKFORCE_CAPACITY_CHANGED", "JOB_OPENED"];
const PRODUCT_TYPES = ["PRODUCT_PROGRESS", "FEATURE_COMPLETED", "PRODUCT_QUALITY_UPDATE", "TECHNICAL_DEBT_INCREASED", "MILESTONE_COMPLETED"];
const OPERATIONS_TYPES = ["OBJECTIVE_CREATED", "OBJECTIVE_ACHIEVED", "RESOURCE_ALLOCATED", "PRIORITY_CHANGED"];
const RISK_TYPES = ["RISK_DETECTED", "RISK_RESOLVED", "RISK_ESCALATED"];
const INCIDENT_TYPES = ["INCIDENT_CREATED", "INCIDENT_ESCALATED", "INCIDENT_RESOLVED"];
const AGENT_TYPES = ["OBSERVE", "THINK", "DECIDE", "ACT", "REFLECT", "PLAN_CREATED", "PLAN_COMPLETED", "LESSON_LEARNED"];

function getEventCategoryFilter(category: EventCategory): string[] {
  switch (category) {
    case "decisions":
      return DECISION_TYPES;
    case "financial":
      return FINANCIAL_TYPES;
    case "market":
      return MARKET_TYPES;
    case "workforce":
      return WORKFORCE_TYPES;
    case "product":
      return PRODUCT_TYPES;
    case "operations":
      return OPERATIONS_TYPES;
    case "risk":
      return RISK_TYPES;
    case "incident":
      return INCIDENT_TYPES;
    case "agent":
      return AGENT_TYPES;
    default:
      return [];
  }
}

function getEventColor(eventType: string): string {
  if (DECISION_TYPES.includes(eventType)) return "border-l-amber-500";
  if (FINANCIAL_TYPES.includes(eventType)) return "border-l-emerald-500";
  if (MARKET_TYPES.includes(eventType)) return "border-l-blue-500";
  if (WORKFORCE_TYPES.includes(eventType)) return "border-l-purple-500";
  if (PRODUCT_TYPES.includes(eventType)) return "border-l-cyan-500";
  if (OPERATIONS_TYPES.includes(eventType)) return "border-l-orange-500";
  if (RISK_TYPES.includes(eventType)) return "border-l-yellow-500";
  if (INCIDENT_TYPES.includes(eventType)) return "border-l-red-500";
  if (AGENT_TYPES.includes(eventType)) return "border-l-slate-400";
  return "border-l-slate-600";
}

function getEventCategoryLabel(eventType: string): string {
  if (DECISION_TYPES.includes(eventType)) return "Decision";
  if (FINANCIAL_TYPES.includes(eventType)) return "Financial";
  if (MARKET_TYPES.includes(eventType)) return "Market";
  if (WORKFORCE_TYPES.includes(eventType)) return "Workforce";
  if (PRODUCT_TYPES.includes(eventType)) return "Product";
  if (OPERATIONS_TYPES.includes(eventType)) return "Operations";
  if (RISK_TYPES.includes(eventType)) return "Risk";
  if (INCIDENT_TYPES.includes(eventType)) return "Incident";
  if (AGENT_TYPES.includes(eventType)) return "Agent";
  return "System";
}

export function TimelinePage({ companyId, onBack }: TimelinePageProps) {
  const [company, setCompany] = useState<Company | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [category, setCategory] = useState<EventCategory>("all");
  const [selectedAgentId, setSelectedAgentId] = useState<number | null>(null);
  const [eventLimit, setEventLimit] = useState(25);
  const [expandedEventId, setExpandedEventId] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<"timeline" | "decisions">("timeline");

  const agentMap = new Map(agents.map((a) => [a.id, a]));

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const results = await Promise.allSettled([
        api.getCompany(companyId),
        api.getAgents(companyId),
        api.getTimelineEvents(companyId, {
          event_type: category !== "all" ? getEventCategoryFilter(category).join(",") : undefined,
          agent_id: selectedAgentId || undefined,
          limit: eventLimit,
        }),
        api.getDecisions(companyId, { limit: 50 }),
      ]);

      const [compResult, agsResult, evtsResult, decsResult] = results;

      if (compResult.status === "fulfilled") {
        setCompany(compResult.value);
      }
      if (agsResult.status === "fulfilled") {
        setAgents(agsResult.value);
      }
      if (evtsResult.status === "fulfilled") {
        setEvents(evtsResult.value);
      }
      if (decsResult.status === "fulfilled") {
        setDecisions(decsResult.value.decisions);
      }

      const hasAnySuccess = results.some((r) => r.status === "fulfilled");
      if (!hasAnySuccess) {
        const firstError = results.find((r) => r.status === "rejected");
        if (firstError && firstError.status === "rejected") {
          setError(String(firstError.reason));
        }
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [companyId, category, selectedAgentId, eventLimit]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const filteredEvents = events.filter((e) => {
    if (category === "all") return true;
    const categoryTypes = getEventCategoryFilter(category);
    return categoryTypes.includes(e.event_type);
  });

  if (loading && !company) {
    return (
      <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
        <TimelineHeader company={null} onBack={onBack} onRefresh={refresh} />
        <LoadingState message="Loading timeline..." />
      </div>
    );
  }

  if (error && !company) {
    return (
      <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
        <TimelineHeader company={null} onBack={onBack} onRefresh={refresh} />
        <ErrorState message={error} onRetry={refresh} />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
      <TimelineHeader company={company} onBack={onBack} onRefresh={refresh} />

      <div className="flex-1 overflow-y-auto p-6">
        {/* Tabs */}
        <div className="mb-6 flex gap-2">
          <button
            onClick={() => setActiveTab("timeline")}
            className={`rounded px-4 py-2 text-sm font-medium ${
              activeTab === "timeline" ? "bg-indigo-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"
            }`}
          >
            Timeline
          </button>
          <button
            onClick={() => setActiveTab("decisions")}
            className={`rounded px-4 py-2 text-sm font-medium ${
              activeTab === "decisions" ? "bg-indigo-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"
            }`}
          >
            Decisions ({decisions.length})
          </button>
        </div>

        {activeTab === "timeline" && (
          <>
            {/* Filters */}
            <div className="mb-6 flex flex-wrap items-center gap-4">
              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Category:</span>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value as EventCategory)}
                  className="rounded bg-slate-800 px-2 py-1 text-xs text-slate-200"
                >
                  {EVENT_CATEGORIES.map((cat) => (
                    <option key={cat.value} value={cat.value}>
                      {cat.label}
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Agent:</span>
                <select
                  value={selectedAgentId ?? ""}
                  onChange={(e) => setSelectedAgentId(e.target.value ? Number(e.target.value) : null)}
                  className="rounded bg-slate-800 px-2 py-1 text-xs text-slate-200"
                >
                  <option value="">All Agents</option>
                  {agents.map((a) => (
                    <option key={a.id} value={a.id}>
                      {a.name} ({a.role})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center gap-2">
                <span className="text-xs text-slate-400">Show:</span>
                {[10, 25, 50].map((limit) => (
                  <button
                    key={limit}
                    onClick={() => setEventLimit(limit)}
                    className={`rounded px-2 py-1 text-xs ${
                      eventLimit === limit ? "bg-indigo-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"
                    }`}
                  >
                    {limit}
                  </button>
                ))}
              </div>
            </div>

            {/* Timeline */}
            {filteredEvents.length === 0 ? (
              <div className="py-12 text-center text-sm text-slate-500">
                No simulation events yet. Run the simulation to generate events.
              </div>
            ) : (
              <div className="space-y-2">
                {filteredEvents.map((event) => {
                  const agent = event.actor_id ? agentMap.get(event.actor_id) : null;
                  const isExpanded = expandedEventId === event.id;

                  return (
                    <div
                      key={event.id}
                      className={`rounded border-l-4 bg-slate-800/50 p-3 ${getEventColor(event.event_type)}`}
                    >
                      <div
                        className="flex cursor-pointer items-start justify-between"
                        onClick={() => setExpandedEventId(isExpanded ? null : event.id)}
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <span className="rounded bg-slate-700 px-2 py-0.5 text-[10px] uppercase text-slate-300">
                              {getEventCategoryLabel(event.event_type)}
                            </span>
                            <span className="text-xs text-slate-500">Day {event.day}</span>
                            {agent && (
                              <span className="text-xs font-medium text-slate-400">
                                {agent.name} ({agent.role})
                              </span>
                            )}
                          </div>
                          <p className="mt-1 text-sm text-slate-200">{event.description}</p>
                        </div>
                        <span className="text-xs text-slate-500">{isExpanded ? "▲" : "▼"}</span>
                      </div>

                      {isExpanded && event.meta && Object.keys(event.meta).length > 0 && (
                        <div className="mt-3 rounded bg-slate-900/50 p-3">
                          <div className="text-[10px] font-semibold uppercase text-slate-500">Details</div>
                          <pre className="mt-1 overflow-x-auto text-xs text-slate-400">
                            {JSON.stringify(event.meta, null, 2)}
                          </pre>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </>
        )}

        {activeTab === "decisions" && (
          <DecisionIntelligence
            decisions={decisions}
            agents={agents}
          />
        )}
      </div>
    </div>
  );
}

function DecisionIntelligence({ decisions, agents }: { decisions: Decision[]; agents: Agent[] }) {
  const agentMap = new Map(agents.map((a) => [a.id, a]));

  const successfulCount = decisions.filter((d) => d.evaluation === "SUCCESSFUL").length;
  const failedCount = decisions.filter((d) => d.evaluation === "FAILED").length;
  const partialCount = decisions.filter((d) => d.evaluation === "PARTIAL").length;
  const unknownCount = decisions.filter((d) => d.evaluation === "UNKNOWN").length;

  return (
    <div className="space-y-6">
      {/* Decision Performance Summary */}
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <div className="text-[10px] font-semibold uppercase text-slate-500">Total Decisions</div>
          <div className="mt-1 text-2xl font-bold text-slate-100">{decisions.length}</div>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <div className="text-[10px] font-semibold uppercase text-slate-500">Successful</div>
          <div className="mt-1 text-2xl font-bold text-emerald-400">{successfulCount}</div>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <div className="text-[10px] font-semibold uppercase text-slate-500">Partial</div>
          <div className="mt-1 text-2xl font-bold text-yellow-400">{partialCount}</div>
        </div>
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
          <div className="text-[10px] font-semibold uppercase text-slate-500">Failed</div>
          <div className="mt-1 text-2xl font-bold text-red-400">{failedCount}</div>
        </div>
      </div>

      {/* Decision Table */}
      {decisions.length === 0 ? (
        <div className="py-12 text-center text-sm text-slate-500">
          No decisions recorded yet. Run the simulation to generate decisions.
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-slate-700 text-xs uppercase text-slate-500">
                <th className="p-2">Day</th>
                <th className="p-2">Agent</th>
                <th className="p-2">Decision</th>
                <th className="p-2">Confidence</th>
                <th className="p-2">Expected</th>
                <th className="p-2">Actual</th>
                <th className="p-2">Evaluation</th>
              </tr>
            </thead>
            <tbody>
              {decisions.map((d) => {
                const agent = d.agent_id ? agentMap.get(d.agent_id) : undefined;
                return (
                  <DecisionRow key={d.id} decision={d} agent={agent} />
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {unknownCount > 0 && (
        <div className="text-xs text-slate-500">
          {unknownCount} decision(s) pending evaluation.
        </div>
      )}
    </div>
  );
}

function DecisionRow({ decision, agent }: { decision: Decision; agent?: Agent }) {
  const [expanded, setExpanded] = useState(false);

  const evaluationColor =
    decision.evaluation === "SUCCESSFUL"
      ? "text-emerald-400"
      : decision.evaluation === "FAILED"
      ? "text-red-400"
      : decision.evaluation === "PARTIAL"
      ? "text-yellow-400"
      : "text-slate-400";

  return (
    <>
      <tr
        className="cursor-pointer border-b border-slate-800 hover:bg-slate-800/50"
        onClick={() => setExpanded(!expanded)}
      >
        <td className="p-2 text-slate-400">{decision.simulation_day}</td>
        <td className="p-2 text-slate-300">{agent ? `${agent.name} (${agent.role})` : "—"}</td>
        <td className="p-2 text-slate-200">{decision.action}</td>
        <td className="p-2 text-slate-400">
          {decision.confidence !== null ? `${(decision.confidence * 100).toFixed(0)}%` : "—"}
        </td>
        <td className="p-2 text-slate-400">
          {decision.expected_value !== null ? decision.expected_value.toFixed(1) : "—"}
        </td>
        <td className="p-2 text-slate-400">
          {decision.actual_value !== null ? decision.actual_value.toFixed(1) : "—"}
        </td>
        <td className={`p-2 font-medium ${evaluationColor}`}>{decision.evaluation}</td>
      </tr>
      {expanded && (
        <tr>
          <td colSpan={7} className="bg-slate-900/50 p-4">
            <div className="grid gap-4 md:grid-cols-2">
              {decision.reasoning && (
                <div>
                  <div className="text-[10px] font-semibold uppercase text-slate-500">Reasoning</div>
                  <p className="mt-1 text-xs text-slate-300">{decision.reasoning}</p>
                </div>
              )}
              {decision.outcome && (
                <div>
                  <div className="text-[10px] font-semibold uppercase text-slate-500">Outcome</div>
                  <p className="mt-1 text-xs text-slate-300">{decision.outcome}</p>
                </div>
              )}
              {decision.expected_outcome && (
                <div>
                  <div className="text-[10px] font-semibold uppercase text-slate-500">Expected Outcome</div>
                  <p className="mt-1 text-xs text-slate-300">{decision.expected_outcome}</p>
                </div>
              )}
              {decision.expectation_status && (
                <div>
                  <div className="text-[10px] font-semibold uppercase text-slate-500">Expectation Status</div>
                  <p className="mt-1 text-xs text-slate-300">{decision.expectation_status}</p>
                </div>
              )}
            </div>
          </td>
        </tr>
      )}
    </>
  );
}

function TimelineHeader({ company, onBack, onRefresh }: { company: Company | null; onBack: () => void; onRefresh: () => void }) {
  return (
    <header className="flex items-center justify-between border-b border-slate-800 bg-slate-900 px-6 py-3">
      <div className="flex items-center gap-4">
        <button
          onClick={onBack}
          className="rounded bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-600"
        >
          Back to Command Center
        </button>
        <h1 className="text-lg font-bold">{company?.name ?? "Company"} — Timeline</h1>
      </div>
      <button
        onClick={onRefresh}
        className="rounded bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-600"
      >
        Refresh
      </button>
    </header>
  );
}
