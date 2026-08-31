import { Agent } from "../types/types";

const STATUS_COLORS: Record<string, string> = {
  IDLE: "bg-slate-600",
  WORKING: "bg-emerald-600",
  BLOCKED: "bg-amber-600",
  OFFLINE: "bg-rose-700",
};

export function AgentCard({ agent }: { agent: Agent }) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-slate-100">{agent.name}</h3>
        <span className="rounded bg-indigo-700 px-2 py-0.5 text-xs font-bold">
          {agent.role}
        </span>
      </div>
      <div className="mt-2 flex items-center gap-2 text-xs text-slate-300">
        <span
          className={`rounded px-2 py-0.5 text-white ${
            STATUS_COLORS[agent.status] ?? "bg-slate-600"
          }`}
        >
          {agent.status}
        </span>
        <span>Authority: {agent.authority}</span>
      </div>
      <div className="mt-2 text-xs text-slate-400">
        <div>Morale: {(agent.morale * 100).toFixed(0)}%</div>
        <div>Energy: {(agent.energy * 100).toFixed(0)}%</div>
        <div>Workload: {(agent.workload * 100).toFixed(0)}%</div>
      </div>
      {agent.skills && agent.skills.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1">
          {agent.skills.map((s) => (
            <span
              key={s}
              className="rounded bg-slate-700 px-2 py-0.5 text-[10px] text-slate-200"
            >
              {s}
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
