import { useCallback, useEffect, useState } from "react";
import { api } from "../api/api";
import { Scenario, ScenarioConfiguration } from "../types/types";
import { ErrorState, LoadingState } from "../components/analytics/AnalyticsComponents";

interface ScenariosPageProps {
  onBack: () => void;
  onViewScenario: (id: number) => void;
  onRunExperiment: (id: number) => void;
  onCreateScenario?: () => void;
  onEditScenario?: (id: number) => void;
}

const CATEGORY_COLORS: Record<string, string> = {
  startup: "bg-emerald-900 text-emerald-300",
  growth: "bg-blue-900 text-blue-300",
  financial: "bg-amber-900 text-amber-300",
  market: "bg-purple-900 text-purple-300",
  workforce: "bg-orange-900 text-orange-300",
  product: "bg-cyan-900 text-cyan-300",
  custom: "bg-slate-700 text-slate-300",
};

export function ScenariosPage({ onBack, onViewScenario, onRunExperiment, onCreateScenario, onEditScenario }: ScenariosPageProps) {
  const [scenarios, setScenarios] = useState<Scenario[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [seeding, setSeeding] = useState(false);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const data = await api.listScenarios();
      setScenarios(data);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleSeedBuiltins = async () => {
    setSeeding(true);
    setError(null);
    try {
      await api.seedBuiltinScenarios();
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setSeeding(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
        <ScenariosHeader onBack={onBack} onSeed={handleSeedBuiltins} seeding={seeding} onCreate={onCreateScenario} />
        <LoadingState message="Loading scenarios..." />
      </div>
    );
  }

  if (error && scenarios.length === 0) {
    return (
      <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
        <ScenariosHeader onBack={onBack} onSeed={handleSeedBuiltins} seeding={seeding} onCreate={onCreateScenario} />
        <ErrorState message={error} onRetry={refresh} />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
      <ScenariosHeader onBack={onBack} onSeed={handleSeedBuiltins} seeding={seeding} onCreate={onCreateScenario} />

      <div className="flex-1 overflow-y-auto p-6">
        {scenarios.length === 0 ? (
          <div className="py-12 text-center">
            <div className="text-lg text-slate-400">No scenarios yet</div>
            <p className="mt-2 text-sm text-slate-500">
              Seed built-in scenarios or create your own to get started.
            </p>
            <button
              onClick={handleSeedBuiltins}
              disabled={seeding}
              className="mt-4 rounded bg-indigo-600 px-4 py-2 text-sm font-semibold hover:bg-indigo-500 disabled:opacity-50"
            >
              {seeding ? "Seeding..." : "Seed Built-in Scenarios"}
            </button>
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {scenarios.map((scenario) => (
              <ScenarioCard
                key={scenario.id}
                scenario={scenario}
                onView={() => onViewScenario(scenario.id)}
                onRun={() => onRunExperiment(scenario.id)}
                onEdit={onEditScenario ? () => onEditScenario(scenario.id) : undefined}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function ScenarioCard({
  scenario,
  onView,
  onRun,
  onEdit,
}: {
  scenario: Scenario;
  onView: () => void;
  onRun: () => void;
  onEdit?: () => void;
}) {
  const config = scenario.configuration as ScenarioConfiguration | undefined;
  const categoryColor = CATEGORY_COLORS[scenario.category] || CATEGORY_COLORS.custom;

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-slate-100">{scenario.name}</h3>
            {scenario.is_builtin && (
              <span className="rounded bg-slate-700 px-1.5 py-0.5 text-[10px] text-slate-400">
                BUILT-IN
              </span>
            )}
          </div>
          <span className={`mt-1 inline-block rounded px-2 py-0.5 text-xs ${categoryColor}`}>
            {scenario.category}
          </span>
        </div>
      </div>

      <p className="mt-2 text-sm text-slate-400 line-clamp-2">
        {scenario.description || "No description"}
      </p>

      {config && (
        <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
          <div className="rounded bg-slate-900/50 p-2">
            <div className="text-slate-500">Cash</div>
            <div className="font-medium text-slate-200">
              ${config.cash?.toLocaleString() ?? "—"}
            </div>
          </div>
          <div className="rounded bg-slate-900/50 p-2">
            <div className="text-slate-500">Market</div>
            <div className="font-medium text-slate-200">
              {config.target_segment ?? "—"}
            </div>
          </div>
        </div>
      )}

      <div className="mt-3 flex items-center justify-between">
        <span className="text-xs text-slate-500">
          {scenario.run_count} run{scenario.run_count !== 1 ? "s" : ""}
        </span>
        <div className="flex gap-2">
          {onEdit && !scenario.is_builtin && (
            <button
              onClick={onEdit}
              className="rounded bg-slate-600 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-500"
            >
              Edit
            </button>
          )}
          <button
            onClick={onView}
            className="rounded bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-600"
          >
            View
          </button>
          <button
            onClick={onRun}
            className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-semibold hover:bg-indigo-500"
          >
            Run
          </button>
        </div>
      </div>
    </div>
  );
}

function ScenariosHeader({
  onBack,
  onSeed,
  seeding,
  onCreate,
}: {
  onBack: () => void;
  onSeed: () => void;
  seeding: boolean;
  onCreate?: () => void;
}) {
  return (
    <header className="flex items-center justify-between border-b border-slate-800 bg-slate-900 px-6 py-3">
      <div className="flex items-center gap-4">
        <button
          onClick={onBack}
          className="rounded bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-600"
        >
          Back to Companies
        </button>
        <h1 className="text-lg font-bold">Scenario Library</h1>
      </div>
      <div className="flex items-center gap-3">
        {onCreate && (
          <button
            onClick={onCreate}
            className="rounded bg-indigo-600 px-3 py-1.5 text-xs font-semibold hover:bg-indigo-500"
          >
            Create Scenario
          </button>
        )}
        <button
          onClick={onSeed}
          disabled={seeding}
          className="rounded bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-600 disabled:opacity-50"
        >
          {seeding ? "Seeding..." : "Seed Built-ins"}
        </button>
      </div>
    </header>
  );
}
