import { useCallback, useEffect, useState } from "react";
import { api } from "../api/api";
import { Agent, Company, SimEvent, SimulationState } from "../types/types";

export function useSimulation(companyId: number) {
  const [company, setCompany] = useState<Company | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [events, setEvents] = useState<SimEvent[]>([]);
  const [sim, setSim] = useState<SimulationState | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    try {
      const [c, a, e, s] = await Promise.all([
        api.getCompany(companyId),
        api.getAgents(companyId),
        api.getEvents(companyId),
        api.getSimulation(companyId),
      ]);
      setCompany(c);
      setAgents(a);
      setEvents(e);
      setSim(s);
    } catch (err) {
      setError(String(err));
    }
  }, [companyId]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const start = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.startSimulation(companyId);
      setSim(r.state);
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [companyId, refresh]);

  const tick = useCallback(async () => {
    setLoading(true);
    try {
      const r = await api.tickSimulation(companyId);
      setSim(r.state);
      await refresh();
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [companyId, refresh]);

  return { company, agents, events, sim, loading, error, refresh, start, tick };
}
