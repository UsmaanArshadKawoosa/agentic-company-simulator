import { Agent } from "../types/types";

export function OrgChart({ agents }: { agents: Agent[] }) {
  const order = ["CEO", "CTO", "CMO", "ENGINEER"];
  const childrenOf = (id: number) =>
    agents
      .filter((a) => a.manager_id === id)
      .sort((a, b) => order.indexOf(a.role) - order.indexOf(b.role));

  const renderNode = (agent: Agent, depth: number) => (
    <div key={agent.id} style={{ marginLeft: depth * 20 }}>
      <div className="my-1 inline-block rounded border border-slate-700 bg-slate-800 px-3 py-1 text-sm">
        <span className="font-semibold text-slate-100">{agent.name}</span>{" "}
        <span className="text-xs text-indigo-300">({agent.role})</span>
      </div>
      {childrenOf(agent.id).map((child) => renderNode(child, depth + 1))}
    </div>
  );

  const roots = agents.filter((a) => a.manager_id === null);

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
        Organization Chart
      </h3>
      {roots.length > 0 ? (
        roots.map((r) => renderNode(r, 0))
      ) : (
        <p className="text-sm text-slate-500">No agents yet.</p>
      )}
    </div>
  );
}
