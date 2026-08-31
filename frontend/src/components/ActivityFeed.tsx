import { SimEvent } from "../types/types";

export function ActivityFeed({ events }: { events: SimEvent[] }) {
  const recent = [...events].reverse();
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-900 p-4">
      <h3 className="mb-3 text-sm font-semibold uppercase tracking-wide text-slate-400">
        Activity Feed
      </h3>
      <ul className="max-h-96 space-y-2 overflow-y-auto text-sm">
        {recent.map((e) => (
          <li key={e.id} className="border-b border-slate-800 pb-2">
            <div className="flex items-center gap-2">
              <span className="rounded bg-slate-700 px-2 py-0.5 text-[10px] uppercase text-indigo-200">
                {e.event_type}
              </span>
              <span className="text-xs text-slate-500">Day {e.simulation_day}</span>
            </div>
            <p className="mt-1 text-slate-300">{e.description}</p>
          </li>
        ))}
        {recent.length === 0 && (
          <li className="text-sm text-slate-500">No activity yet.</li>
        )}
      </ul>
    </div>
  );
}
