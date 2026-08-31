import { Company, SimulationState } from "../types/types";

export function Metrics({
  company,
  sim,
}: {
  company: Company;
  sim: SimulationState | null;
}) {
  const items = [
    { label: "Cash", value: `$${company.cash.toLocaleString()}` },
    { label: "Revenue", value: `$${company.revenue.toLocaleString()}` },
    { label: "Expenses", value: `$${company.expenses.toLocaleString()}` },
    { label: "Day", value: String(company.current_day) },
    { label: "Agents", value: String(sim?.agent_count ?? 0) },
    { label: "Events", value: String(sim?.event_count ?? 0) },
  ];
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {items.map((it) => (
        <div
          key={it.label}
          className="rounded-lg border border-slate-700 bg-slate-800 p-3 text-center"
        >
          <div className="text-xs uppercase tracking-wide text-slate-400">
            {it.label}
          </div>
          <div className="mt-1 text-lg font-bold text-slate-100">{it.value}</div>
        </div>
      ))}
    </div>
  );
}
