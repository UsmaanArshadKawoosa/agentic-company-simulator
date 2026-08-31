import { useState } from "react";
import { CreateCompany } from "./pages/CreateCompany";
import { Simulation } from "./pages/Simulation";
import { CompanyList } from "./pages/CompanyList";

type Page =
  | { type: "list" }
  | { type: "create" }
  | { type: "simulation"; companyId: number };

export default function App() {
  const [page, setPage] = useState<Page>({ type: "list" });

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800 px-6 py-4">
        <div className="flex items-center justify-between">
          <h1
            className="text-lg font-bold text-slate-100 cursor-pointer"
            onClick={() => setPage({ type: "list" })}
          >
            Agent Company Simulator
          </h1>
          {page.type === "simulation" && (
            <button
              onClick={() => setPage({ type: "list" })}
              className="rounded bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-600"
            >
              Back to Companies
            </button>
          )}
        </div>
      </header>

      {page.type === "list" && (
        <CompanyList
          onSelect={(id) => setPage({ type: "simulation", companyId: id })}
          onCreateNew={() => setPage({ type: "create" })}
        />
      )}
      {page.type === "create" && (
        <CreateCompany
          onCreated={(id) => setPage({ type: "simulation", companyId: id })}
          onCancel={() => setPage({ type: "list" })}
        />
      )}
      {page.type === "simulation" && (
        <Simulation companyId={page.companyId} />
      )}
    </div>
  );
}
