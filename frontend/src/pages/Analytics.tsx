import { useCallback, useEffect, useState } from "react";
import { api } from "../api/api";
import { HistoryResponse, Company, FinancialMetrics, ValuationData, WorkforceSummary, MarketData, CompetitorData, SalesOpportunity, Objective, Risk, Incident } from "../types/types";
import { KpiCard, AnalyticsSection, ChartContainer, LoadingState, ErrorState } from "../components/analytics/AnalyticsComponents";
import { TimeSeriesChart, SimpleBarChart, DonutChart } from "../components/analytics/Charts";

interface AnalyticsPageProps {
  companyId: number;
  onBack: () => void;
  onOpenTimeline?: () => void;
}

export function AnalyticsPage({ companyId, onBack, onOpenTimeline }: AnalyticsPageProps) {
  const [company, setCompany] = useState<Company | null>(null);
  const [history, setHistory] = useState<HistoryResponse | null>(null);
  const [financials, setFinancials] = useState<FinancialMetrics | null>(null);
  const [valuation, setValuation] = useState<ValuationData | null>(null);
  const [workforce, setWorkforce] = useState<WorkforceSummary | null>(null);
  const [market, setMarket] = useState<MarketData | null>(null);
  const [competitors, setCompetitors] = useState<CompetitorData[]>([]);
  const [sales, setSales] = useState<SalesOpportunity[]>([]);
  const [objectives, setObjectives] = useState<Objective[]>([]);
  const [risks, setRisks] = useState<Risk[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [historyLimit, setHistoryLimit] = useState(25);

  const refresh = useCallback(async () => {
    setError(null);
    try {
      const results = await Promise.allSettled([
        api.getCompany(companyId),
        api.getHistory(companyId, historyLimit),
        api.getFinancials(companyId),
        api.getValuation(companyId),
        api.getWorkforce(companyId),
        api.getMarketData(companyId),
        api.getCompetitorsData(companyId),
        api.getSalesOpportunities(companyId),
        api.getObjectives(companyId),
        api.getRisks(companyId),
        api.getIncidents(companyId),
      ]);

      const [comp, hist, fin, val, wf, mkt, comps, salesData, objs, rks, incs] = results;

      if (comp.status === "fulfilled") setCompany(comp.value);
      if (hist.status === "fulfilled") setHistory(hist.value);
      if (fin.status === "fulfilled") setFinancials(fin.value);
      if (val.status === "fulfilled") setValuation(val.value);
      if (wf.status === "fulfilled") setWorkforce(wf.value);
      if (mkt.status === "fulfilled") setMarket(mkt.value);
      if (comps.status === "fulfilled") setCompetitors(comps.value);
      if (salesData.status === "fulfilled") setSales(salesData.value);
      if (objs.status === "fulfilled") setObjectives(objs.value);
      if (rks.status === "fulfilled") setRisks(rks.value);
      if (incs.status === "fulfilled") setIncidents(incs.value);

      const hasAnyData = results.some((r) => r.status === "fulfilled");
      if (!hasAnyData) {
        setError("Failed to load analytics data");
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [companyId, historyLimit]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (loading && !company) {
    return (
      <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
        <AnalyticsHeader company={null} onBack={onBack} onRefresh={refresh} onOpenTimeline={onOpenTimeline} />
        <LoadingState />
      </div>
    );
  }

  if (error && !company) {
    return (
      <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
        <AnalyticsHeader company={null} onBack={onBack} onRefresh={refresh} onOpenTimeline={onOpenTimeline} />
        <ErrorState message={error} onRetry={refresh} />
      </div>
    );
  }

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
      <AnalyticsHeader company={company} onBack={onBack} onRefresh={refresh} onOpenTimeline={onOpenTimeline} />

      <div className="flex-1 overflow-y-auto p-6">
        <TimeRangeSelector limit={historyLimit} onChange={setHistoryLimit} />

        <AnalyticsSection title="Executive Overview" description="Key company performance indicators">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <KpiCard label="Cash" value={`$${company?.cash.toLocaleString() ?? 0}`} color="text-emerald-400" />
            <KpiCard label="Revenue" value={`$${company?.revenue.toLocaleString() ?? 0}`} color="text-blue-400" />
            <KpiCard label="Expenses" value={`$${company?.expenses.toLocaleString() ?? 0}`} color="text-red-400" />
            <KpiCard label="Day" value={company?.current_day ?? 0} color="text-slate-100" />
          </div>
        </AnalyticsSection>

        <AnalyticsSection title="Financial Performance" description="Revenue, expenses, and cash over time">
          <div className="grid gap-4 lg:grid-cols-2">
            <ChartContainer
              title="Revenue vs Expenses"
              loading={loading}
              error={!history && error ? error : null}
              empty={history?.data_points === 0}
              emptyMessage="No historical data yet. Run the simulation."
              onRetry={refresh}
              height={220}
            >
              <TimeSeriesChart
                data={history?.series ?? []}
                type="area"
                dataKeys={[
                  { key: "revenue" as const, name: "Revenue", color: "#10b981" },
                  { key: "expenses" as const, name: "Expenses", color: "#ef4444" },
                ]}
                height={220}
              />
            </ChartContainer>

            <ChartContainer
              title="Cash Balance"
              loading={loading}
              error={!history && error ? error : null}
              empty={history?.data_points === 0}
              emptyMessage="No historical data yet."
              onRetry={refresh}
              height={220}
            >
              <TimeSeriesChart
                data={history?.series ?? []}
                type="area"
                dataKeys={[{ key: "cash" as const, name: "Cash", color: "#3b82f6" }]}
                height={220}
              />
            </ChartContainer>
          </div>

          {financials && (
            <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
              <KpiCard label="Daily Burn" value={`$${financials.daily_burn.toLocaleString()}`} color="text-red-400" />
              <KpiCard
                label="Runway"
                value={financials.runway_days ? `${financials.runway_days.toFixed(1)} days` : "∞"}
                color="text-blue-400"
              />
              <KpiCard
                label="Health Score"
                value={`${(financials.financial_health_score * 100).toFixed(0)}%`}
                color={financials.financial_health === "HEALTHY" ? "text-emerald-400" : "text-yellow-400"}
              />
              <KpiCard label="Risk Level" value={financials.financial_risk_level} color="text-orange-400" />
            </div>
          )}

          {valuation && (
            <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-3">
              <KpiCard label="Valuation" value={`$${valuation.valuation.toLocaleString()}`} color="text-emerald-400" />
              <KpiCard label="ARR" value={`$${valuation.annual_revenue.toLocaleString()}`} color="text-blue-400" />
              <KpiCard label="Growth Factor" value={`${valuation.growth_factor.toFixed(2)}x`} color="text-purple-400" />
            </div>
          )}
        </AnalyticsSection>

        <AnalyticsSection title="Market Intelligence" description="Market position and competitive landscape">
          <div className="grid gap-4 lg:grid-cols-2">
            <ChartContainer
              title="Market Segments"
              loading={loading}
              empty={!market || market.segments.length === 0}
              emptyMessage="No market data available."
              onRetry={refresh}
              height={200}
            >
              <DonutChart data={market?.segments.map((s) => ({ name: s.name, value: s.size })) ?? []} height={200} />
            </ChartContainer>

            <ChartContainer
              title="Competitor Market Share"
              loading={loading}
              empty={competitors.length === 0}
              emptyMessage="No competitor data available."
              onRetry={refresh}
              height={200}
            >
              <SimpleBarChart
                data={competitors.map((c) => ({ name: c.name, value: c.market_share * 100 }))}
                height={200}
              />
            </ChartContainer>
          </div>

          {market && (
            <div className="mt-4 grid grid-cols-2 gap-4 md:grid-cols-4">
              <KpiCard label="Target Segment" value={market.company.target_segment} color="text-slate-100" />
              <KpiCard label="Price" value={`$${market.company.price}`} color="text-blue-400" />
              <KpiCard
                label="Market Share"
                value={`${(market.company.market_share * 100).toFixed(1)}%`}
                color="text-purple-400"
              />
              <KpiCard
                label="Brand Strength"
                value={`${(market.company.brand_strength * 100).toFixed(0)}%`}
                color="text-amber-400"
              />
            </div>
          )}
        </AnalyticsSection>

        <AnalyticsSection title="Workforce" description="Team composition and metrics">
          {workforce ? (
            <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
              <KpiCard label="Headcount" value={workforce.overview.headcount} color="text-slate-100" />
              <KpiCard label="Active" value={workforce.overview.active_count} color="text-emerald-400" />
              <KpiCard label="Payroll" value={`$${workforce.overview.payroll.toLocaleString()}`} color="text-red-400" />
              <KpiCard
                label="Avg Morale"
                value={`${(workforce.overview.avg_morale * 100).toFixed(0)}%`}
                color="text-purple-400"
              />
            </div>
          ) : (
            <div className="text-sm text-slate-500">No workforce data available.</div>
          )}
        </AnalyticsSection>

        <AnalyticsSection title="Sales Pipeline" description="Opportunities and deal values">
          {sales.length > 0 ? (
            <div className="grid gap-4 lg:grid-cols-2">
              <ChartContainer title="Pipeline by Stage" height={180}>
                <SimpleBarChart
                  data={getSalesByStage(sales)}
                  height={180}
                />
              </ChartContainer>
              <ChartContainer title="Deal Values" height={180}>
                <SimpleBarChart
                  data={sales.slice(0, 8).map((s) => ({ name: s.name.substring(0, 15), value: s.value }))}
                  height={180}
                />
              </ChartContainer>
            </div>
          ) : (
            <div className="text-sm text-slate-500">No sales opportunities yet.</div>
          )}
        </AnalyticsSection>

        <AnalyticsSection title="Operational Health" description="Objectives, risks, and incidents">
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <KpiCard label="Active Objectives" value={objectives.filter((o) => o.status === "ACTIVE").length} color="text-blue-400" />
            <KpiCard label="Completed" value={objectives.filter((o) => o.status === "COMPLETED").length} color="text-emerald-400" />
            <KpiCard label="Active Risks" value={risks.filter((r) => r.status === "ACTIVE").length} color="text-yellow-400" />
            <KpiCard label="Open Incidents" value={incidents.filter((i) => i.status === "OPEN").length} color="text-red-400" />
          </div>
        </AnalyticsSection>
      </div>
    </div>
  );
}

function AnalyticsHeader({ company, onBack, onRefresh, onOpenTimeline }: { company: Company | null; onBack: () => void; onRefresh: () => void; onOpenTimeline?: () => void }) {
  return (
    <header className="flex items-center justify-between border-b border-slate-800 bg-slate-900 px-6 py-3">
      <div className="flex items-center gap-4">
        <button
          onClick={onBack}
          className="rounded bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-600"
        >
          Back to Command Center
        </button>
        {onOpenTimeline && (
          <button
            onClick={onOpenTimeline}
            className="rounded bg-violet-900 px-3 py-1.5 text-xs font-semibold hover:bg-violet-700"
          >
            View Timeline
          </button>
        )}
        <h1 className="text-lg font-bold">{company?.name ?? "Company"} — Analytics</h1>
      </div>
      <button
        onClick={onRefresh}
        className="rounded bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-600"
      >
        Refresh
      </button>
    </header>
  );
}

function TimeRangeSelector({ limit, onChange }: { limit: number; onChange: (limit: number) => void }) {
  return (
    <div className="mb-6 flex items-center gap-2">
      <span className="text-xs text-slate-400">History:</span>
      {[10, 25, 50].map((l) => (
        <button
          key={l}
          onClick={() => onChange(l)}
          className={`rounded px-2 py-1 text-xs ${
            limit === l ? "bg-indigo-600 text-white" : "bg-slate-800 text-slate-400 hover:bg-slate-700"
          }`}
        >
          Last {l}
        </button>
      ))}
    </div>
  );
}

function getSalesByStage(sales: SalesOpportunity[]): Array<{ name: string; value: number }> {
  const stages: Record<string, number> = {};
  for (const s of sales) {
    stages[s.stage] = (stages[s.stage] || 0) + 1;
  }
  return Object.entries(stages).map(([name, value]) => ({ name, value }));
}
