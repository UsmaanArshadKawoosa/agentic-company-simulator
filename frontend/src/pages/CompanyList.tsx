import { useState, useEffect, useCallback } from "react";
import { api } from "../api/api";
import { Company } from "../types/types";

export function CompanyList({
  onSelect,
  onCreateNew,
}: {
  onSelect: (id: number) => void;
  onCreateNew: () => void;
}) {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadCompanies = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.listCompanies();
      setCompanies(data);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadCompanies();
  }, [loadCompanies]);

  const statusColor = (status: string) => {
    switch (status) {
      case "RUNNING":
        return "bg-emerald-900 text-emerald-300";
      case "PAUSED":
        return "bg-yellow-900 text-yellow-300";
      case "FAILED":
        return "bg-red-900 text-red-300";
      case "COMPLETED":
        return "bg-blue-900 text-blue-300";
      default:
        return "bg-slate-800 text-slate-300";
    }
  };

  return (
    <div className="mx-auto mt-12 max-w-4xl px-6">
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-100">Companies</h1>
        <button
          onClick={onCreateNew}
          className="rounded bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
        >
          Create Company
        </button>
      </div>

      {error && (
        <div className="mb-4 rounded border border-red-800 bg-red-950 p-3 text-sm text-red-300">
          {error}
        </div>
      )}

      {loading ? (
        <div className="py-12 text-center text-slate-400">Loading companies...</div>
      ) : companies.length === 0 ? (
        <div className="rounded-xl border border-slate-700 bg-slate-800 p-12 text-center">
          <p className="mb-4 text-slate-400">No companies yet. Create your first company to get started.</p>
          <button
            onClick={onCreateNew}
            className="rounded bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500"
          >
            Create Company
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {companies.map((company) => (
            <button
              key={company.id}
              onClick={() => onSelect(company.id)}
              className="w-full rounded-xl border border-slate-700 bg-slate-800 p-4 text-left transition hover:border-indigo-600 hover:bg-slate-750"
            >
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-slate-100">{company.name}</h3>
                  <p className="mt-1 text-sm text-slate-400 line-clamp-1">{company.mission}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`rounded px-2 py-1 text-xs font-medium ${statusColor(company.status)}`}>
                    {company.status}
                  </span>
                  <span className="text-xs text-slate-500">Day {company.current_day}</span>
                </div>
              </div>
              <div className="mt-3 flex gap-4 text-xs text-slate-500">
                <span>Cash: ${company.cash.toLocaleString()}</span>
                <span>Revenue: ${company.revenue.toLocaleString()}</span>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
