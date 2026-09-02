import { useState, lazy, Suspense } from "react";
import { CreateCompany } from "./pages/CreateCompany";
import { Simulation } from "./pages/Simulation";
import { CompanyList } from "./pages/CompanyList";
import { ErrorBoundary } from "./components/ErrorBoundary";

const AnalyticsPage = lazy(() => import("./pages/Analytics").then(m => ({ default: m.AnalyticsPage })));
const TimelinePage = lazy(() => import("./pages/Timeline").then(m => ({ default: m.TimelinePage })));
const ScenariosPage = lazy(() => import("./pages/Scenarios").then(m => ({ default: m.ScenariosPage })));
const ExperimentPage = lazy(() => import("./pages/Experiment").then(m => ({ default: m.ExperimentPage })));
const ScenarioEditorPage = lazy(() => import("./pages/ScenarioEditorPage").then(m => ({ default: m.ScenarioEditorPage })));
const RunDetailPage = lazy(() => import("./pages/RunDetail").then(m => ({ default: m.RunDetailPage })));

function LoadingFallback() {
  return (
    <div className="flex min-h-[400px] items-center justify-center">
      <div className="text-sm text-slate-400">Loading...</div>
    </div>
  );
}

type Page =
  | { type: "list" }
  | { type: "create" }
  | { type: "simulation"; companyId: number }
  | { type: "analytics"; companyId: number }
  | { type: "timeline"; companyId: number }
  | { type: "scenarios" }
  | { type: "scenario_editor"; scenarioId?: number }
  | { type: "experiment"; scenarioId: number }
  | { type: "run_detail"; runId: number };

export default function App() {
  const [page, setPage] = useState<Page>({ type: "list" });

  return (
    <ErrorBoundary>
      <div className="min-h-screen">
        <header className="border-b border-slate-800 px-6 py-4">
          <div className="flex items-center justify-between">
            <h1
              className="text-lg font-bold text-slate-100 cursor-pointer"
              onClick={() => setPage({ type: "list" })}
            >
              Agent Company Simulator
            </h1>
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage({ type: "scenarios" })}
                className={`rounded px-3 py-1.5 text-xs font-medium ${
                  page.type === "scenarios" ||
                  page.type === "experiment" ||
                  page.type === "scenario_editor" ||
                  page.type === "run_detail"
                    ? "bg-indigo-600 text-white"
                    : "bg-slate-700 text-slate-200 hover:bg-slate-600"
                }`}
              >
                Scenarios
              </button>
              {(page.type === "simulation" ||
                page.type === "analytics" ||
                page.type === "timeline" ||
                page.type === "experiment" ||
                page.type === "scenario_editor" ||
                page.type === "run_detail") && (
                <button
                  onClick={() => setPage({ type: "list" })}
                  className="rounded bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-600"
                >
                  Back to Companies
                </button>
              )}
            </div>
          </div>
        </header>

        {page.type === "list" && (
          <CompanyList
            onSelect={(id) => setPage({ type: "simulation", companyId: id })}
            onCreateNew={() => setPage({ type: "create" })}
            onOpenScenarios={() => setPage({ type: "scenarios" })}
          />
        )}
        {page.type === "create" && (
          <CreateCompany
            onCreated={(id) => setPage({ type: "simulation", companyId: id })}
            onCancel={() => setPage({ type: "list" })}
          />
        )}
        {page.type === "simulation" && (
          <Simulation
            companyId={page.companyId}
            onOpenAnalytics={(id) => setPage({ type: "analytics", companyId: id })}
            onOpenTimeline={(id) => setPage({ type: "timeline", companyId: id })}
          />
        )}
        {page.type === "analytics" && (
          <Suspense fallback={<LoadingFallback />}>
            <AnalyticsPage
              companyId={page.companyId}
              onBack={() => setPage({ type: "simulation", companyId: page.companyId })}
              onOpenTimeline={() => setPage({ type: "timeline", companyId: page.companyId })}
            />
          </Suspense>
        )}
        {page.type === "timeline" && (
          <Suspense fallback={<LoadingFallback />}>
            <TimelinePage
              companyId={page.companyId}
              onBack={() => setPage({ type: "simulation", companyId: page.companyId })}
            />
          </Suspense>
        )}
        {page.type === "scenarios" && (
          <Suspense fallback={<LoadingFallback />}>
            <ScenariosPage
              onBack={() => setPage({ type: "list" })}
              onViewScenario={(id) => setPage({ type: "experiment", scenarioId: id })}
              onRunExperiment={(id) => setPage({ type: "experiment", scenarioId: id })}
              onCreateScenario={() => setPage({ type: "scenario_editor" })}
              onEditScenario={(id) => setPage({ type: "scenario_editor", scenarioId: id })}
            />
          </Suspense>
        )}
        {page.type === "scenario_editor" && (
          <Suspense fallback={<LoadingFallback />}>
            <ScenarioEditorPage
              scenarioId={page.scenarioId}
              onSave={() => setPage({ type: "scenarios" })}
              onCancel={() => setPage({ type: "scenarios" })}
            />
          </Suspense>
        )}
        {page.type === "experiment" && (
          <Suspense fallback={<LoadingFallback />}>
            <ExperimentPage
              scenarioId={page.scenarioId}
              onBack={() => setPage({ type: "scenarios" })}
              onViewRun={(runId) => setPage({ type: "run_detail", runId })}
              onViewCompany={(companyId) => setPage({ type: "simulation", companyId })}
            />
          </Suspense>
        )}
        {page.type === "run_detail" && (
          <Suspense fallback={<LoadingFallback />}>
            <RunDetailPage
              runId={page.runId}
              onBack={() => setPage({ type: "scenarios" })}
              onOpenAnalytics={(companyId) => setPage({ type: "analytics", companyId })}
              onOpenTimeline={(companyId) => setPage({ type: "timeline", companyId })}
            />
          </Suspense>
        )}
      </div>
    </ErrorBoundary>
  );
}
