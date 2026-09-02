import { useCallback, useEffect, useState } from "react";
import { api } from "../api/api";
import { ExperimentResult, MetricSummary, SimulationRun } from "../types/types";
import { ErrorState, LoadingState } from "../components/analytics/AnalyticsComponents";
import { ExperimentCharts } from "../components/experiment/ExperimentCharts";

interface ExperimentPageProps {
  scenarioId: number;
  onBack: () => void;
  onViewRun: (runId: number) => void;
  onViewCompany: (companyId: number) => void;
}

export function ExperimentPage({ scenarioId, onBack, onViewRun, onViewCompany }: ExperimentPageProps) {
  const [experiment, setExperiment] = useState<ExperimentResult | null>(null);
  const [runs, setRuns] = useState<SimulationRun[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [numRuns, setNumRuns] = useState(3);
  const [numDays, setNumDays] = useState(50);
  const [running, setRunning] = useState(false);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const [expData, runsData] = await Promise.all([
        api.getExperimentResults(scenarioId),
        api.listRuns(scenarioId),
      ]);
      setExperiment(expData);
      setRuns(runsData);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [scenarioId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const handleRunExperiment = async () => {
    setRunning(true);
    setError(null);
    try {
      await api.runExperiment(scenarioId, numRuns, numDays);
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setRunning(false);
    }
  };

  const handleExportCSV = () => {
    if (!experiment) return;
    const headers = [
      "run_id",
      "seed",
      "status",
      "simulation_days",
      "final_day",
      "cash",
      "revenue",
      "expenses",
      "profit",
      "active_customers",
      "market_share",
      "valuation",
    ];
    const rows = experiment.runs.map((r) => [
      r.run_id,
      r.seed,
      r.status,
      r.simulation_days,
      r.final_day,
      r.metrics.cash ?? "",
      r.metrics.revenue ?? "",
      r.metrics.expenses ?? "",
      r.metrics.profit ?? "",
      r.metrics.active_customers ?? "",
      r.metrics.market_share ?? "",
      r.metrics.valuation ?? "",
    ]);
    const csv = [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    downloadFile(csv, `experiment_${scenarioId}.csv`, "text/csv");
  };

  const handleExportJSON = () => {
    if (!experiment) return;
    const json = JSON.stringify(experiment, null, 2);
    downloadFile(json, `experiment_${scenarioId}.json`, "application/json");
  };

  if (loading) {
    return (
      <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
        <ExperimentHeader
          onBack={onBack}
          onRun={handleRunExperiment}
          onExportCSV={handleExportCSV}
          onExportJSON={handleExportJSON}
          running={running}
          numRuns={numRuns}
          numDays={numDays}
          onNumRunsChange={setNumRuns}
          onNumDaysChange={setNumDays}
          hasData={!!experiment && experiment.completed_runs > 0}
        />
        <LoadingState message="Loading experiment results..." />
      </div>
    );
  }

  if (error && !experiment) {
    return (
      <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
        <ExperimentHeader
          onBack={onBack}
          onRun={handleRunExperiment}
          onExportCSV={handleExportCSV}
          onExportJSON={handleExportJSON}
          running={running}
          numRuns={numRuns}
          numDays={numDays}
          onNumRunsChange={setNumRuns}
          onNumDaysChange={setNumDays}
          hasData={false}
        />
        <ErrorState message={error} onRetry={refresh} />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
      <ExperimentHeader
        onBack={onBack}
        onRun={handleRunExperiment}
        onExportCSV={handleExportCSV}
        onExportJSON={handleExportJSON}
        running={running}
        numRuns={numRuns}
        numDays={numDays}
        onNumRunsChange={setNumRuns}
        onNumDaysChange={setNumDays}
        hasData={!!experiment && experiment.completed_runs > 0}
      />

      <div className="flex-1 overflow-y-auto p-6">
        {experiment && experiment.completed_runs > 0 ? (
          <div className="space-y-6">
            {/* Summary Stats */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <SummaryCard
                label="Cash"
                summary={experiment.summary.cash}
                formatValue={(v) => `$${v.toLocaleString()}`}
              />
              <SummaryCard
                label="Revenue"
                summary={experiment.summary.revenue}
                formatValue={(v) => `$${v.toLocaleString()}`}
              />
              <SummaryCard
                label="Customers"
                summary={experiment.summary.active_customers}
                formatValue={(v) => v.toLocaleString()}
              />
              <SummaryCard
                label="Market Share"
                summary={experiment.summary.market_share}
                formatValue={(v) => `${(v * 100).toFixed(1)}%`}
              />
            </div>

            {/* Runs Table */}
            <div className="rounded-lg border border-slate-700 bg-slate-800">
              <div className="border-b border-slate-700 px-4 py-3">
                <h3 className="font-semibold text-slate-100">Run Results</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead>
                    <tr className="border-b border-slate-700 text-xs uppercase text-slate-500">
                      <th className="p-3">Run</th>
                      <th className="p-3">Seed</th>
                      <th className="p-3">Day</th>
                      <th className="p-3">Cash</th>
                      <th className="p-3">Revenue</th>
                      <th className="p-3">Profit</th>
                      <th className="p-3">Customers</th>
                      <th className="p-3">Market %</th>
                      <th className="p-3">Valuation</th>
                      <th className="p-3"></th>
                    </tr>
                  </thead>
                  <tbody>
                    {experiment.runs.map((run) => (
                      <tr
                        key={run.run_id}
                        className="border-b border-slate-800 hover:bg-slate-800/50"
                      >
                        <td className="p-3 text-slate-400">#{run.run_id}</td>
                        <td className="p-3 text-slate-400">{run.seed}</td>
                        <td className="p-3 text-slate-300">{run.final_day}</td>
                        <td className="p-3 text-slate-200">
                          ${run.metrics.cash?.toLocaleString() ?? "—"}
                        </td>
                        <td className="p-3 text-slate-200">
                          ${run.metrics.revenue?.toLocaleString() ?? "—"}
                        </td>
                        <td className="p-3 text-slate-200">
                          ${run.metrics.profit?.toLocaleString() ?? "—"}
                        </td>
                        <td className="p-3 text-slate-200">
                          {run.metrics.active_customers != null
                            ? (run.metrics.active_customers as number).toLocaleString()
                            : "—"}
                        </td>
                        <td className="p-3 text-slate-200">
                          {run.metrics.market_share != null
                            ? `${((run.metrics.market_share as number) * 100).toFixed(1)}%`
                            : "—"}
                        </td>
                        <td className="p-3 text-slate-200">
                          ${run.metrics.valuation?.toLocaleString() ?? "—"}
                        </td>
                        <td className="p-3">
                          {runs.find((r) => r.id === run.run_id)?.company_id && (
                            <div className="flex gap-1">
                              <button
                                onClick={() => onViewRun(run.run_id)}
                                className="rounded bg-violet-600 px-2 py-1 text-xs text-white hover:bg-violet-500"
                              >
                                Detail
                              </button>
                              <button
                                onClick={() =>
                                  onViewCompany(runs.find((r) => r.id === run.run_id)!.company_id!)
                                }
                                className="rounded bg-slate-700 px-2 py-1 text-xs text-slate-200 hover:bg-slate-600"
                              >
                                Inspect
                              </button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Charts */}
            <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
              <h3 className="mb-4 font-semibold text-slate-100">Comparison Charts</h3>
              <ExperimentCharts runs={experiment.runs} />
            </div>

            {/* Failed Runs */}
            {runs.some((r) => r.status === "FAILED") && (
              <div className="rounded-lg border border-red-900/50 bg-red-900/10 p-4">
                <h4 className="text-sm font-semibold text-red-400">Failed Runs</h4>
                <ul className="mt-2 space-y-1 text-xs text-red-300">
                  {runs
                    .filter((r) => r.status === "FAILED")
                    .map((r) => (
                      <li key={r.id}>
                        Run #{r.id} (seed {r.seed}): {r.error_message || "Unknown error"}
                      </li>
                    ))}
                </ul>
              </div>
            )}
          </div>
        ) : (
          <div className="py-12 text-center">
            <div className="text-lg text-slate-400">No experiment results yet</div>
            <p className="mt-2 text-sm text-slate-500">
              Run an experiment to compare multiple simulation runs.
            </p>
          </div>
        )}
      </div>
    </div>
  );
}

function SummaryCard({
  label,
  summary,
  formatValue,
}: {
  label: string;
  summary: MetricSummary | undefined;
  formatValue: (v: number) => string;
}) {
  if (!summary) return null;

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
      <div className="text-xs font-semibold uppercase text-slate-500">{label}</div>
      <div className="mt-2 space-y-1 text-sm">
        <div className="flex justify-between">
          <span className="text-slate-400">Best:</span>
          <span className="font-medium text-emerald-400">{formatValue(summary.best)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Avg:</span>
          <span className="text-slate-200">{formatValue(summary.average)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Median:</span>
          <span className="text-slate-200">{formatValue(summary.median)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-slate-400">Worst:</span>
          <span className="font-medium text-red-400">{formatValue(summary.worst)}</span>
        </div>
      </div>
    </div>
  );
}

function ExperimentHeader({
  onBack,
  onRun,
  onExportCSV,
  onExportJSON,
  running,
  numRuns,
  numDays,
  onNumRunsChange,
  onNumDaysChange,
  hasData,
}: {
  onBack: () => void;
  onRun: () => void;
  onExportCSV: () => void;
  onExportJSON: () => void;
  running: boolean;
  numRuns: number;
  numDays: number;
  onNumRunsChange: (n: number) => void;
  onNumDaysChange: (n: number) => void;
  hasData: boolean;
}) {
  return (
    <header className="border-b border-slate-800 bg-slate-900 px-6 py-3">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="rounded bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-600"
          >
            Back to Scenarios
          </button>
          <h1 className="text-lg font-bold">Experiment Results</h1>
        </div>
        <div className="flex items-center gap-3">
          {hasData && (
            <>
              <button
                onClick={onExportCSV}
                className="rounded bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-600"
              >
                Export CSV
              </button>
              <button
                onClick={onExportJSON}
                className="rounded bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-600"
              >
                Export JSON
              </button>
            </>
          )}
        </div>
      </div>
      <div className="mt-3 flex items-center gap-4">
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Runs:</span>
          <input
            type="number"
            min={1}
            max={20}
            value={numRuns}
            onChange={(e) => onNumRunsChange(Math.max(1, Math.min(20, Number(e.target.value))))}
            className="w-16 rounded bg-slate-800 px-2 py-1 text-xs text-slate-200"
          />
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-slate-400">Days:</span>
          <input
            type="number"
            min={1}
            max={500}
            value={numDays}
            onChange={(e) => onNumDaysChange(Math.max(1, Math.min(500, Number(e.target.value))))}
            className="w-16 rounded bg-slate-800 px-2 py-1 text-xs text-slate-200"
          />
        </div>
        <button
          onClick={onRun}
          disabled={running}
          className="rounded bg-indigo-600 px-4 py-1.5 text-xs font-semibold hover:bg-indigo-500 disabled:opacity-50"
        >
          {running ? "Running..." : "Run Experiment"}
        </button>
      </div>
    </header>
  );
}

function downloadFile(content: string, filename: string, mimeType: string) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
