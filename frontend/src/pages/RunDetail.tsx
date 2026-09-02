import { useCallback, useEffect, useState } from "react";
import { api } from "../api/api";
import { Scenario, SimulationRun } from "../types/types";
import { ErrorState, LoadingState } from "../components/analytics/AnalyticsComponents";

interface RunDetailPageProps {
  runId: number;
  onBack: () => void;
  onOpenAnalytics: (companyId: number) => void;
  onOpenTimeline: (companyId: number) => void;
}

export function RunDetailPage({
  runId,
  onBack,
  onOpenAnalytics,
  onOpenTimeline,
}: RunDetailPageProps) {
  const [run, setRun] = useState<SimulationRun | null>(null);
  const [scenario, setScenario] = useState<Scenario | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const data: SimulationRun = await api.getSimulationRun(runId);
      setRun(data);

      const scenarioResponse = await api.getScenario(data.scenario_id);
      setScenario(scenarioResponse);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (loading) {
    return (
      <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
        <RunDetailHeader onBack={onBack} title="Run Detail" />
        <LoadingState message="Loading run details..." />
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
        <RunDetailHeader onBack={onBack} title="Run Detail" />
        <ErrorState message={error ?? "Run not found"} onRetry={refresh} />
      </div>
    );
  }

  const metrics = run.final_metrics ?? {};
  const config = run.configuration_snapshot as Record<string, unknown>;
  const isCompleted = run.status === "COMPLETED";
  const isFailed = run.status === "FAILED";

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
      <RunDetailHeader
        onBack={onBack}
        title={`Run #${run.id}`}
        subtitle={scenario?.name}
      />

      <div className="flex-1 overflow-y-auto p-6">
        <div className="mx-auto max-w-4xl space-y-6">
          {/* Status Banner */}
          {isFailed && (
            <div className="rounded border border-red-800 bg-red-950 p-4">
              <h3 className="font-semibold text-red-400">Run Failed</h3>
              {run.error_message && (
                <p className="mt-1 text-sm text-red-300">{run.error_message}</p>
              )}
            </div>
          )}

          {/* Run Overview */}
          <section className="rounded-lg border border-slate-700 bg-slate-800 p-4">
            <h2 className="mb-4 text-sm font-semibold uppercase text-slate-400">
              Run Overview
            </h2>
            <div className="grid gap-4 text-sm md:grid-cols-3">
              <InfoItem label="Run ID" value={`#${run.id}`} />
              <InfoItem label="Status" value={run.status} highlight={isCompleted ? "success" : isFailed ? "error" : "neutral"} />
              <InfoItem label="Seed" value={run.seed.toString()} />
              <InfoItem label="Scenario" value={scenario?.name ?? `ID ${run.scenario_id}`} />
              <InfoItem label="Simulation Days" value={run.simulation_days.toString()} />
              <InfoItem label="Final Day" value={metrics.current_day?.toString() ?? "—"} />
              <InfoItem label="Started" value={run.started_at ?? "—"} />
              <InfoItem label="Completed" value={run.completed_at ?? "—"} />
              <InfoItem label="Company ID" value={run.company_id?.toString() ?? "—"} />
            </div>
          </section>

          {/* Final Metrics */}
          {isCompleted && metrics && (
            <section className="rounded-lg border border-slate-700 bg-slate-800 p-4">
              <h2 className="mb-4 text-sm font-semibold uppercase text-slate-400">
                Final Metrics
              </h2>
              <div className="grid gap-4 md:grid-cols-4">
                <MetricCard
                  label="Cash"
                  value={formatCurrency(metrics.cash)}
                  color="emerald"
                />
                <MetricCard
                  label="Revenue"
                  value={formatCurrency(metrics.revenue)}
                  color="blue"
                />
                <MetricCard
                  label="Expenses"
                  value={formatCurrency(metrics.expenses)}
                  color="amber"
                />
                <MetricCard
                  label="Profit"
                  value={formatCurrency(metrics.profit)}
                  color={(metrics.profit as number) >= 0 ? "emerald" : "red"}
                />
                <MetricCard
                  label="Active Customers"
                  value={metrics.active_customers?.toLocaleString() ?? "—"}
                  color="purple"
                />
                <MetricCard
                  label="Market Share"
                  value={metrics.market_share != null
                    ? `${((metrics.market_share as number) * 100).toFixed(1)}%`
                    : "—"
                  }
                  color="cyan"
                />
                <MetricCard
                  label="Valuation"
                  value={formatCurrency(metrics.valuation)}
                  color="indigo"
                />
                <MetricCard
                  label="Product Readiness"
                  value={metrics.product_readiness != null
                    ? (metrics.product_readiness as number).toFixed(2)
                    : "—"
                  }
                  color="pink"
                />
              </div>
            </section>
          )}

          {/* Configuration Snapshot */}
          {config && (
            <section className="rounded-lg border border-slate-700 bg-slate-800 p-4">
              <h2 className="mb-2 text-sm font-semibold uppercase text-slate-400">
                Configuration Snapshot
              </h2>
              <p className="mb-4 text-xs text-slate-500">
                This is the configuration used when the run was created. Editing the scenario will not change this snapshot.
              </p>
              <div className="grid gap-3 text-sm md:grid-cols-3">
                <InfoItem label="Company Name" value={config.name?.toString() ?? "—"} />
                <InfoItem label="Mission" value={config.mission?.toString() ?? "—"} />
                <InfoItem label="Initial Cash" value={formatCurrency(config.cash)} />
                <InfoItem label="Market Demand" value={config.market_demand?.toString() ?? "—"} />
                <InfoItem label="Competition" value={config.market_competition?.toString() ?? "—"} />
                <InfoItem label="Target Segment" value={config.target_segment?.toString() ?? "—"} />
                <InfoItem label="Price" value={formatCurrency(config.price)} />
                <InfoItem label="Product Readiness" value={config.product_readiness?.toString() ?? "—"} />
                <InfoItem label="Technical Debt" value={config.technical_debt?.toString() ?? "—"} />
              </div>
            </section>
          )}

          {/* Actions */}
          {run.company_id && isCompleted && (
            <section className="flex gap-3">
              <button
                onClick={() => onOpenAnalytics(run.company_id!)}
                className="rounded bg-indigo-600 px-4 py-2 text-sm font-semibold hover:bg-indigo-500"
              >
                Open Analytics
              </button>
              <button
                onClick={() => onOpenTimeline(run.company_id!)}
                className="rounded bg-violet-600 px-4 py-2 text-sm font-semibold hover:bg-violet-500"
              >
                Open Timeline
              </button>
              <button
                onClick={() => onOpenTimeline(run.company_id!)}
                className="rounded bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-600"
              >
                View Decisions
              </button>
            </section>
          )}
        </div>
      </div>
    </div>
  );
}

function RunDetailHeader({
  onBack,
  title,
  subtitle,
}: {
  onBack: () => void;
  title: string;
  subtitle?: string;
}) {
  return (
    <header className="flex items-center justify-between border-b border-slate-800 bg-slate-900 px-6 py-3">
      <div className="flex items-center gap-4">
        <button
          onClick={onBack}
          className="rounded bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-600"
        >
          Back to Experiment
        </button>
        <div>
          <h1 className="text-lg font-bold">{title}</h1>
          {subtitle && <p className="text-sm text-slate-400">{subtitle}</p>}
        </div>
      </div>
    </header>
  );
}

function InfoItem({
  label,
  value,
  highlight,
}: {
  label: string;
  value: string;
  highlight?: "success" | "error" | "neutral";
}) {
  const highlightClass =
    highlight === "success"
      ? "text-emerald-400"
      : highlight === "error"
        ? "text-red-400"
        : "text-slate-200";

  return (
    <div>
      <div className="text-xs text-slate-500">{label}</div>
      <div className={`font-medium ${highlightClass}`}>{value}</div>
    </div>
  );
}

function MetricCard({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color: string;
}) {
  const colorMap: Record<string, string> = {
    emerald: "border-emerald-800 bg-emerald-950/30",
    blue: "border-blue-800 bg-blue-950/30",
    amber: "border-amber-800 bg-amber-950/30",
    red: "border-red-800 bg-red-950/30",
    purple: "border-purple-800 bg-purple-950/30",
    cyan: "border-cyan-800 bg-cyan-950/30",
    indigo: "border-indigo-800 bg-indigo-950/30",
    pink: "border-pink-800 bg-pink-950/30",
  };

  return (
    <div className={`rounded border p-3 ${colorMap[color] ?? "border-slate-700 bg-slate-900/30"}`}>
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-lg font-semibold text-slate-100">{value}</div>
    </div>
  );
}

function formatCurrency(value: unknown): string {
  if (value == null) return "—";
  const num = typeof value === "number" ? value : Number(value);
  if (isNaN(num)) return "—";
  return `$${num.toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}
