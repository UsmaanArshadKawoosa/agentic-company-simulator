import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import { RunResult } from "../../types/types";

interface ExperimentChartsProps {
  runs: RunResult[];
}

interface ChartDataPoint {
  name: string;
  value: number;
  runId: number;
  status: string;
}

const COLORS = [
  "#6366f1", "#8b5cf6", "#a855f7", "#d946ef", "#ec4899",
  "#f43f5e", "#ef4444", "#f97316", "#eab308", "#22c55e",
];

function formatCurrency(value: number): string {
  if (Math.abs(value) >= 1_000_000) {
    return `$${(value / 1_000_000).toFixed(1)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `$${(value / 1_000).toFixed(0)}K`;
  }
  return `$${value.toFixed(0)}`;
}

function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function ExperimentCharts({ runs }: ExperimentChartsProps) {
  const completedRuns = runs.filter((r) => r.status === "COMPLETED");

  if (completedRuns.length === 0) {
    return (
      <div className="rounded-lg border border-slate-700 bg-slate-800 p-8 text-center text-sm text-slate-500">
        No completed runs to chart.
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <MetricChart
        title="Cash by Run"
        data={completedRuns.map((r) => ({
          name: `#${r.run_id}`,
          value: (r.metrics.cash as number) ?? 0,
          runId: r.run_id,
          status: r.status,
        }))}
        formatValue={formatCurrency}
      />
      <MetricChart
        title="Revenue by Run"
        data={completedRuns.map((r) => ({
          name: `#${r.run_id}`,
          value: (r.metrics.revenue as number) ?? 0,
          runId: r.run_id,
          status: r.status,
        }))}
        formatValue={formatCurrency}
      />
      <MetricChart
        title="Profit/Loss by Run"
        data={completedRuns.map((r) => ({
          name: `#${r.run_id}`,
          value: (r.metrics.profit as number) ?? 0,
          runId: r.run_id,
          status: r.status,
        }))}
        formatValue={formatCurrency}
        allowNegative
      />
      <MetricChart
        title="Active Customers by Run"
        data={completedRuns.map((r) => ({
          name: `#${r.run_id}`,
          value: (r.metrics.active_customers as number) ?? 0,
          runId: r.run_id,
          status: r.status,
        }))}
        formatValue={(v) => v.toLocaleString()}
      />
      <MetricChart
        title="Market Share by Run"
        data={completedRuns.map((r) => ({
          name: `#${r.run_id}`,
          value: ((r.metrics.market_share as number) ?? 0) * 100,
          runId: r.run_id,
          status: r.status,
        }))}
        formatValue={(v) => `${v.toFixed(1)}%`}
      />
      <MetricChart
        title="Valuation by Run"
        data={completedRuns.map((r) => ({
          name: `#${r.run_id}`,
          value: (r.metrics.valuation as number) ?? 0,
          runId: r.run_id,
          status: r.status,
        }))}
        formatValue={formatCurrency}
      />
    </div>
  );
}

function MetricChart({
  title,
  data,
  formatValue,
  allowNegative = false,
}: {
  title: string;
  data: ChartDataPoint[];
  formatValue: (v: number) => string;
  allowNegative?: boolean;
}) {
  const minValue = Math.min(...data.map((d) => d.value));
  const maxY = Math.max(...data.map((d) => d.value));
  const minY = allowNegative ? Math.min(0, minValue) : 0;

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800 p-4">
      <h3 className="mb-3 text-sm font-semibold text-slate-300">{title}</h3>
      <ResponsiveContainer width="100%" height={200}>
        <BarChart data={data} margin={{ top: 5, right: 20, left: 20, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
          <XAxis
            dataKey="name"
            tick={{ fill: "#94a3b8", fontSize: 12 }}
            axisLine={{ stroke: "#475569" }}
          />
          <YAxis
            domain={[minY, maxY * 1.1]}
            tick={{ fill: "#94a3b8", fontSize: 12 }}
            axisLine={{ stroke: "#475569" }}
            tickFormatter={(v) => formatValue(v)}
          />
          <Tooltip
            contentStyle={{
              backgroundColor: "#1e293b",
              border: "1px solid #475569",
              borderRadius: "8px",
              color: "#f1f5f9",
            }}
            formatter={(value) => [formatValue(Number(value)), title]}
            labelFormatter={(label) => `Run ${label}`}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.value < 0 ? "#ef4444" : COLORS[index % COLORS.length]}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
