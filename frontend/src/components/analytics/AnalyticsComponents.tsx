import { ReactNode } from "react";

interface KpiCardProps {
  label: string;
  value: string | number;
  subtitle?: string;
  color?: string;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
}

export function KpiCard({ label, value, subtitle, color = "text-slate-100", trend, trendValue }: KpiCardProps) {
  const trendColor = trend === "up" ? "text-emerald-400" : trend === "down" ? "text-red-400" : "text-slate-400";
  const trendIcon = trend === "up" ? "+" : trend === "down" ? "-" : "";

  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/50 p-4">
      <div className="text-[10px] font-semibold uppercase text-slate-500">{label}</div>
      <div className={`mt-1 text-2xl font-bold ${color}`}>{value}</div>
      {subtitle && <div className="mt-1 text-xs text-slate-400">{subtitle}</div>}
      {trendValue && (
        <div className={`mt-1 text-xs ${trendColor}`}>
          {trendIcon}{trendValue}
        </div>
      )}
    </div>
  );
}

interface AnalyticsSectionProps {
  title: string;
  children: ReactNode;
  description?: string;
}

export function AnalyticsSection({ title, children, description }: AnalyticsSectionProps) {
  return (
    <section className="mb-8">
      <div className="mb-4">
        <h2 className="text-sm font-semibold text-slate-200">{title}</h2>
        {description && <p className="mt-1 text-xs text-slate-500">{description}</p>}
      </div>
      {children}
    </section>
  );
}

interface ChartContainerProps {
  title: string;
  children: ReactNode;
  loading?: boolean;
  error?: string | null;
  empty?: boolean;
  emptyMessage?: string;
  onRetry?: () => void;
  height?: number;
}

export function ChartContainer({
  title,
  children,
  loading,
  error,
  empty,
  emptyMessage = "No data available",
  onRetry,
  height = 200,
}: ChartContainerProps) {
  return (
    <div className="rounded-lg border border-slate-700 bg-slate-800/30 p-4">
      <h3 className="mb-3 text-xs font-semibold uppercase text-slate-500">{title}</h3>
      <div style={{ height }} className="flex items-center justify-center">
        {loading ? (
          <div className="text-sm text-slate-500">Loading...</div>
        ) : error ? (
          <div className="flex flex-col items-center gap-2">
            <div className="text-sm text-rose-400">{error}</div>
            {onRetry && (
              <button
                onClick={onRetry}
                className="rounded bg-slate-700 px-3 py-1 text-xs text-slate-200 hover:bg-slate-600"
              >
                Retry
              </button>
            )}
          </div>
        ) : empty ? (
          <div className="text-sm text-slate-500">{emptyMessage}</div>
        ) : (
          children
        )}
      </div>
    </div>
  );
}

interface EmptyStateProps {
  message: string;
  description?: string;
}

export function EmptyState({ message, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="text-sm text-slate-400">{message}</div>
      {description && <div className="mt-1 text-xs text-slate-500">{description}</div>}
    </div>
  );
}

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="text-sm text-rose-400">{message}</div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 rounded bg-slate-700 px-4 py-2 text-sm text-slate-200 hover:bg-slate-600"
        >
          Retry
        </button>
      )}
    </div>
  );
}

interface LoadingStateProps {
  message?: string;
}

export function LoadingState({ message = "Loading analytics..." }: LoadingStateProps) {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="text-sm text-slate-500">{message}</div>
    </div>
  );
}
