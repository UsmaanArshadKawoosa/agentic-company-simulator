import { Agent, Company, SimEvent, SimulationState } from "../types/types";
import { ActivityFeed } from "./ActivityFeed";
import { AgentCard } from "./AgentCard";
import { Metrics } from "./Metrics";
import { OrgChart } from "./OrgChart";

export function CompanyDashboard({
  company,
  agents,
  events,
  sim,
}: {
  company: Company;
  agents: Agent[];
  events: SimEvent[];
  sim: SimulationState | null;
}) {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100">{company.name}</h1>
        <p className="text-sm text-slate-400">{company.mission}</p>
        <p className="mt-1 text-xs uppercase tracking-wide text-slate-500">
          Status: {company.status}
        </p>
      </div>
      <Metrics company={company} sim={sim} />
      <div className="grid gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h2 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
              Agents
            </h2>
            <div className="grid gap-3 sm:grid-cols-2">
              {agents.map((a) => (
                <AgentCard key={a.id} agent={a} />
              ))}
            </div>
          </div>
          <OrgChart agents={agents} />
        </div>
        <ActivityFeed events={events} />
      </div>
    </div>
  );
}
