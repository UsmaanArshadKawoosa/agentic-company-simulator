import { useState } from "react";
import { api } from "../api/api";
import { Scenario, ScenarioConfiguration } from "../types/types";

interface ScenarioEditorProps {
  scenario?: Scenario;
  onSave: (scenario: Scenario) => void;
  onCancel: () => void;
}

const DEFAULT_CONFIG: ScenarioConfiguration = {
  name: "New Company",
  mission: "Build a great product",
  cash: 100000,
  seed: null,
  market_demand: 0.5,
  market_competition: 0.3,
  product_readiness: 0.0,
  technical_debt: 0.0,
  target_segment: "SMB",
  price: 100,
};

const VALID_SEGMENTS = ["SMB", "Mid-Market", "Enterprise", "Consumer"];

interface FormErrors {
  name?: string;
  cash?: string;
  market_demand?: string;
  market_competition?: string;
  product_readiness?: string;
  technical_debt?: string;
  price?: string;
  target_segment?: string;
}

export function ScenarioEditor({ scenario, onSave, onCancel }: ScenarioEditorProps) {
  const isBuiltin = scenario?.is_builtin === true;
  const isEditing = !!scenario;

  const [name, setName] = useState(scenario?.name ?? "");
  const [description, setDescription] = useState(scenario?.description ?? "");
  const [category, setCategory] = useState(scenario?.category ?? "custom");
  const [config, setConfig] = useState<ScenarioConfiguration>(
    (scenario?.configuration as ScenarioConfiguration) ?? DEFAULT_CONFIG
  );
  const [errors, setErrors] = useState<FormErrors>({});
  const [submitting, setSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!name.trim()) {
      newErrors.name = "Name is required";
    } else if (name.length > 255) {
      newErrors.name = "Name must be 255 characters or less";
    }

    if (config.cash < 0) {
      newErrors.cash = "Cash cannot be negative";
    } else if (config.cash > 10_000_000) {
      newErrors.cash = "Cash cannot exceed $10,000,000";
    }

    if (config.market_demand < 0 || config.market_demand > 1) {
      newErrors.market_demand = "Must be between 0 and 1";
    }

    if (config.market_competition < 0 || config.market_competition > 1) {
      newErrors.market_competition = "Must be between 0 and 1";
    }

    if (config.product_readiness < 0 || config.product_readiness > 1) {
      newErrors.product_readiness = "Must be between 0 and 1";
    }

    if (config.technical_debt < 0 || config.technical_debt > 1) {
      newErrors.technical_debt = "Must be between 0 and 1";
    }

    if (config.price < 0) {
      newErrors.price = "Price cannot be negative";
    } else if (config.price > 100_000) {
      newErrors.price = "Price cannot exceed $100,000";
    }

    if (!VALID_SEGMENTS.includes(config.target_segment)) {
      newErrors.target_segment = `Must be one of: ${VALID_SEGMENTS.join(", ")}`;
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setSubmitting(true);
    setApiError(null);

    try {
      const payload = {
        name: name.trim(),
        description: description.trim(),
        category,
        configuration: config,
      };

      let result: Scenario;
      if (isEditing && scenario) {
        result = await api.updateScenario(scenario.id, payload);
      } else {
        result = await api.createScenario(payload);
      }
      onSave(result);
    } catch (err) {
      setApiError(String(err));
    } finally {
      setSubmitting(false);
    }
  };

  const updateConfig = (field: keyof ScenarioConfiguration, value: number | string | null) => {
    setConfig((prev) => ({ ...prev, [field]: value }));
  };

  const inputClass = "mt-1 w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-sm text-slate-100";
  const labelClass = "block text-sm font-medium text-slate-300";
  const errorClass = "mt-1 text-xs text-rose-400";

  return (
    <div className="flex h-screen flex-col bg-slate-950 text-slate-100">
      <header className="flex items-center justify-between border-b border-slate-800 bg-slate-900 px-6 py-3">
        <h1 className="text-lg font-bold">{isEditing ? "Edit Scenario" : "Create Scenario"}</h1>
        <div className="flex items-center gap-3">
          {isBuiltin && (
            <span className="rounded bg-amber-900 px-2 py-1 text-xs text-amber-300">
              Built-in (read-only)
            </span>
          )}
          <button
            onClick={onCancel}
            className="rounded bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-200 hover:bg-slate-600"
          >
            Cancel
          </button>
        </div>
      </header>

      <div className="flex-1 overflow-y-auto p-6">
        <form onSubmit={handleSubmit} className="mx-auto max-w-2xl space-y-6">
          {apiError && (
            <div className="rounded border border-red-800 bg-red-950 p-3 text-sm text-red-300">
              {apiError}
            </div>
          )}

          {/* Basic Information */}
          <section className="rounded-lg border border-slate-700 bg-slate-800 p-4">
            <h2 className="mb-4 text-sm font-semibold uppercase text-slate-400">
              Basic Information
            </h2>
            <div className="space-y-4">
              <div>
                <label htmlFor="scenario-name" className={labelClass}>
                  Name *
                </label>
                <input
                  id="scenario-name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  disabled={isBuiltin}
                  className={inputClass}
                  placeholder="My Scenario"
                />
                {errors.name && <p className={errorClass}>{errors.name}</p>}
              </div>

              <div>
                <label htmlFor="scenario-desc" className={labelClass}>
                  Description
                </label>
                <textarea
                  id="scenario-desc"
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  disabled={isBuiltin}
                  rows={2}
                  className={inputClass}
                  placeholder="Describe this scenario..."
                />
              </div>

              <div>
                <label htmlFor="scenario-category" className={labelClass}>
                  Category
                </label>
                <select
                  id="scenario-category"
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  disabled={isBuiltin}
                  className={inputClass}
                >
                  <option value="custom">Custom</option>
                  <option value="startup">Startup</option>
                  <option value="growth">Growth</option>
                  <option value="financial">Financial</option>
                  <option value="market">Market</option>
                  <option value="workforce">Workforce</option>
                  <option value="product">Product</option>
                </select>
              </div>
            </div>
          </section>

          {/* Company / Mission */}
          <section className="rounded-lg border border-slate-700 bg-slate-800 p-4">
            <h2 className="mb-4 text-sm font-semibold uppercase text-slate-400">
              Company
            </h2>
            <div className="space-y-4">
              <div>
                <label htmlFor="config-mission" className={labelClass}>
                  Mission
                </label>
                <input
                  id="config-mission"
                  type="text"
                  value={config.mission}
                  onChange={(e) => updateConfig("mission", e.target.value)}
                  disabled={isBuiltin}
                  className={inputClass}
                  placeholder="Company mission..."
                />
              </div>
              <div>
                <label htmlFor="config-name" className={labelClass}>
                  Company Name Prefix
                </label>
                <input
                  id="config-name"
                  type="text"
                  value={config.name}
                  onChange={(e) => updateConfig("name", e.target.value)}
                  disabled={isBuiltin}
                  className={inputClass}
                  placeholder="Company name..."
                />
              </div>
            </div>
          </section>

          {/* Financial Conditions */}
          <section className="rounded-lg border border-slate-700 bg-slate-800 p-4">
            <h2 className="mb-4 text-sm font-semibold uppercase text-slate-400">
              Financial Conditions
            </h2>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label htmlFor="config-cash" className={labelClass}>
                  Initial Cash ($)
                </label>
                <input
                  id="config-cash"
                  type="number"
                  min={0}
                  max={10_000_000}
                  step={1000}
                  value={config.cash}
                  onChange={(e) => updateConfig("cash", Number(e.target.value))}
                  disabled={isBuiltin}
                  className={inputClass}
                />
                {errors.cash && <p className={errorClass}>{errors.cash}</p>}
              </div>
            </div>
          </section>

          {/* Market Conditions */}
          <section className="rounded-lg border border-slate-700 bg-slate-800 p-4">
            <h2 className="mb-4 text-sm font-semibold uppercase text-slate-400">
              Market Conditions
            </h2>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label htmlFor="config-demand" className={labelClass}>
                  Market Demand (0-1)
                </label>
                <input
                  id="config-demand"
                  type="number"
                  min={0}
                  max={1}
                  step={0.05}
                  value={config.market_demand}
                  onChange={(e) => updateConfig("market_demand", Number(e.target.value))}
                  disabled={isBuiltin}
                  className={inputClass}
                />
                {errors.market_demand && <p className={errorClass}>{errors.market_demand}</p>}
              </div>
              <div>
                <label htmlFor="config-competition" className={labelClass}>
                  Market Competition (0-1)
                </label>
                <input
                  id="config-competition"
                  type="number"
                  min={0}
                  max={1}
                  step={0.05}
                  value={config.market_competition}
                  onChange={(e) => updateConfig("market_competition", Number(e.target.value))}
                  disabled={isBuiltin}
                  className={inputClass}
                />
                {errors.market_competition && (
                  <p className={errorClass}>{errors.market_competition}</p>
                )}
              </div>
              <div>
                <label htmlFor="config-segment" className={labelClass}>
                  Target Segment
                </label>
                <select
                  id="config-segment"
                  value={config.target_segment}
                  onChange={(e) => updateConfig("target_segment", e.target.value)}
                  disabled={isBuiltin}
                  className={inputClass}
                >
                  {VALID_SEGMENTS.map((seg) => (
                    <option key={seg} value={seg}>
                      {seg}
                    </option>
                  ))}
                </select>
                {errors.target_segment && <p className={errorClass}>{errors.target_segment}</p>}
              </div>
              <div>
                <label htmlFor="config-price" className={labelClass}>
                  Price ($)
                </label>
                <input
                  id="config-price"
                  type="number"
                  min={0}
                  max={100_000}
                  step={1}
                  value={config.price}
                  onChange={(e) => updateConfig("price", Number(e.target.value))}
                  disabled={isBuiltin}
                  className={inputClass}
                />
                {errors.price && <p className={errorClass}>{errors.price}</p>}
              </div>
            </div>
          </section>

          {/* Product Conditions */}
          <section className="rounded-lg border border-slate-700 bg-slate-800 p-4">
            <h2 className="mb-4 text-sm font-semibold uppercase text-slate-400">
              Product Conditions
            </h2>
            <div className="grid gap-4 md:grid-cols-2">
              <div>
                <label htmlFor="config-readiness" className={labelClass}>
                  Product Readiness (0-1)
                </label>
                <input
                  id="config-readiness"
                  type="number"
                  min={0}
                  max={1}
                  step={0.05}
                  value={config.product_readiness}
                  onChange={(e) => updateConfig("product_readiness", Number(e.target.value))}
                  disabled={isBuiltin}
                  className={inputClass}
                />
                {errors.product_readiness && (
                  <p className={errorClass}>{errors.product_readiness}</p>
                )}
              </div>
              <div>
                <label htmlFor="config-debt" className={labelClass}>
                  Technical Debt (0-1)
                </label>
                <input
                  id="config-debt"
                  type="number"
                  min={0}
                  max={1}
                  step={0.05}
                  value={config.technical_debt}
                  onChange={(e) => updateConfig("technical_debt", Number(e.target.value))}
                  disabled={isBuiltin}
                  className={inputClass}
                />
                {errors.technical_debt && <p className={errorClass}>{errors.technical_debt}</p>}
              </div>
            </div>
          </section>

          {/* Configuration Preview */}
          <section className="rounded-lg border border-slate-700 bg-slate-800 p-4">
            <h2 className="mb-4 text-sm font-semibold uppercase text-slate-400">
              Starting Conditions Preview
            </h2>
            <div className="grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
              <PreviewItem label="Cash" value={`$${config.cash.toLocaleString()}`} />
              <PreviewItem label="Market Demand" value={config.market_demand.toFixed(2)} />
              <PreviewItem label="Competition" value={config.market_competition.toFixed(2)} />
              <PreviewItem label="Readiness" value={config.product_readiness.toFixed(2)} />
              <PreviewItem label="Tech Debt" value={config.technical_debt.toFixed(2)} />
              <PreviewItem label="Segment" value={config.target_segment} />
              <PreviewItem label="Price" value={`$${config.price.toLocaleString()}`} />
            </div>
          </section>

          {/* Actions */}
          {!isBuiltin && (
            <div className="flex justify-end gap-3">
              <button
                type="button"
                onClick={onCancel}
                className="rounded bg-slate-700 px-4 py-2 text-sm font-medium text-slate-200 hover:bg-slate-600"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="rounded bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
              >
                {submitting ? "Saving..." : isEditing ? "Save Changes" : "Create Scenario"}
              </button>
            </div>
          )}
        </form>
      </div>
    </div>
  );
}

function PreviewItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded bg-slate-900/50 p-2">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="font-medium text-slate-200">{value}</div>
    </div>
  );
}
