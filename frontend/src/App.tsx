import { useState } from "react";
import { CreateCompany } from "./pages/CreateCompany";
import { Simulation } from "./pages/Simulation";

export default function App() {
  const [companyId, setCompanyId] = useState<number | null>(null);

  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800 px-6 py-4">
        <h1 className="text-lg font-bold text-slate-100">
          Agent Company Simulator
        </h1>
      </header>
      {companyId === null ? (
        <CreateCompany onCreated={setCompanyId} />
      ) : (
        <Simulation companyId={companyId} />
      )}
    </div>
  );
}
