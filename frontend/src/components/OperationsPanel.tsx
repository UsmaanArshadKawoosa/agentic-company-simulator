import { useState, useEffect, useCallback } from "react";
import { api } from "../api/api";
import { Objective, Risk, Incident } from "../types/types";

interface OperationsPanelProps {
  companyId: number;
  visible?: boolean;
}

export function OperationsPanel({ companyId, visible = true }: OperationsPanelProps) {
  const [objectives, setObjectives] = useState<Objective[]>([]);
  const [risks, setRisks] = useState<Risk[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showCreateObjective, setShowCreateObjective] = useState(false);
  const [newObjectiveTitle, setNewObjectiveTitle] = useState("");
  const [newObjectiveDesc, setNewObjectiveDesc] = useState("");

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [objs, rsk, inc] = await Promise.all([
        api.getObjectives(companyId),
        api.getRisks(companyId),
        api.getIncidents(companyId),
      ]);
      setObjectives(objs);
      setRisks(rsk);
      setIncidents(inc);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [companyId]);

  useEffect(() => {
    if (!visible) return;
    loadData();
    const interval = setInterval(loadData, 5000);
    return () => clearInterval(interval);
  }, [loadData, visible]);

  const handleCreateObjective = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newObjectiveTitle.trim()) return;
    try {
      await api.createObjective(companyId, newObjectiveTitle, newObjectiveDesc);
      setNewObjectiveTitle("");
      setNewObjectiveDesc("");
      setShowCreateObjective(false);
      await loadData();
    } catch (err) {
      setError(String(err));
    }
  };

  const severityColor = (severity: string) => {
    switch (severity) {
      case "CRITICAL":
        return "text-red-400";
      case "HIGH":
        return "text-orange-400";
      case "MEDIUM":
        return "text-yellow-400";
      case "LOW":
        return "text-blue-400";
      default:
        return "text-slate-400";
    }
  };

  const statusColor = (status: string) => {
    switch (status) {
      case "ACHIEVED":
      case "RESOLVED":
      case "MITIGATED":
        return "text-emerald-400";
      case "ACTIVE":
      case "IN_PROGRESS":
        return "text-blue-400";
      case "FAILED":
        return "text-red-400";
      default:
        return "text-slate-400";
    }
  };

  return (
    <div className="space-y-4">
      {error && (
        <div className="rounded border border-red-800 bg-red-950 p-2 text-xs text-red-300">
          {error}
        </div>
      )}

      {/* Objectives */}
      <div className="rounded bg-slate-800/50 p-3">
        <div className="mb-2 flex items-center justify-between">
          <h3 className="text-[10px] font-semibold uppercase text-slate-500">Objectives</h3>
          <button
            onClick={() => setShowCreateObjective(!showCreateObjective)}
            className="text-[10px] text-indigo-400 hover:text-indigo-300"
          >
            {showCreateObjective ? "Cancel" : "+ Add"}
          </button>
        </div>

        {showCreateObjective && (
          <form onSubmit={handleCreateObjective} className="mb-2 space-y-2">
            <input
              className="w-full rounded border border-slate-600 bg-slate-900 px-2 py-1 text-xs text-slate-100"
              placeholder="Objective title"
              value={newObjectiveTitle}
              onChange={(e) => setNewObjectiveTitle(e.target.value)}
            />
            <input
              className="w-full rounded border border-slate-600 bg-slate-900 px-2 py-1 text-xs text-slate-100"
              placeholder="Description (optional)"
              value={newObjectiveDesc}
              onChange={(e) => setNewObjectiveDesc(e.target.value)}
            />
            <button
              type="submit"
              className="w-full rounded bg-indigo-600 px-2 py-1 text-xs font-medium text-white hover:bg-indigo-500"
            >
              Create Objective
            </button>
          </form>
        )}

        {loading ? (
          <div className="text-xs text-slate-500">Loading...</div>
        ) : objectives.length === 0 ? (
          <div className="text-xs text-slate-500">No objectives yet</div>
        ) : (
          <div className="space-y-2">
            {objectives.slice(0, 5).map((obj) => (
              <div key={obj.id} className="rounded bg-slate-900/50 p-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-medium text-slate-200 truncate max-w-[140px]">
                    {obj.title}
                  </span>
                  <span className={`text-[10px] ${statusColor(obj.status)}`}>
                    {obj.status}
                  </span>
                </div>
                <div className="mt-1 h-1 rounded-full bg-slate-700">
                  <div
                    className="h-full rounded-full bg-indigo-500"
                    style={{ width: `${obj.progress}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Risks */}
      <div className="rounded bg-slate-800/50 p-3">
        <h3 className="mb-2 text-[10px] font-semibold uppercase text-slate-500">Risks</h3>
        {risks.length === 0 ? (
          <div className="text-xs text-slate-500">No active risks</div>
        ) : (
          <div className="space-y-1">
            {risks.slice(0, 5).map((risk) => (
              <div key={risk.id} className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-300 truncate max-w-[120px]">
                  {risk.risk_type}
                </span>
                <span className={`text-[10px] ${severityColor(risk.severity)}`}>
                  {risk.severity}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Incidents */}
      <div className="rounded bg-slate-800/50 p-3">
        <h3 className="mb-2 text-[10px] font-semibold uppercase text-slate-500">Incidents</h3>
        {incidents.length === 0 ? (
          <div className="text-xs text-slate-500">No active incidents</div>
        ) : (
          <div className="space-y-1">
            {incidents.slice(0, 5).map((inc) => (
              <div key={inc.id} className="flex items-center justify-between text-xs">
                <span className="font-medium text-slate-300 truncate max-w-[120px]">
                  {inc.incident_type}
                </span>
                <span className={`text-[10px] ${severityColor(inc.severity)}`}>
                  {inc.severity}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
