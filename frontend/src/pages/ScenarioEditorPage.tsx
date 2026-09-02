import { useCallback, useEffect, useState } from "react";
import { api } from "../api/api";
import { Scenario } from "../types/types";
import { ScenarioEditor } from "./ScenarioEditor";
import { ErrorState, LoadingState } from "../components/analytics/AnalyticsComponents";

interface ScenarioEditorPageProps {
  scenarioId?: number;
  onSave: () => void;
  onCancel: () => void;
}

export function ScenarioEditorPage({ scenarioId, onSave, onCancel }: ScenarioEditorPageProps) {
  const [scenario, setScenario] = useState<Scenario | undefined>(undefined);
  const [loading, setLoading] = useState(!!scenarioId);
  const [error, setError] = useState<string | null>(null);

  const loadScenario = useCallback(async () => {
    if (!scenarioId) {
      setLoading(false);
      return;
    }
    setError(null);
    try {
      const data = await api.getScenario(scenarioId);
      setScenario(data);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }, [scenarioId]);

  useEffect(() => {
    loadScenario();
  }, [loadScenario]);

  if (loading) {
    return <LoadingState message="Loading scenario..." />;
  }

  if (error) {
    return <ErrorState message={error} onRetry={loadScenario} />;
  }

  return (
    <ScenarioEditor
      scenario={scenario}
      onSave={() => onSave()}
      onCancel={onCancel}
    />
  );
}
