import { useState } from "react";
import { api } from "../api/api";

export function CreateCompany({
  onCreated,
}: {
  onCreated: (id: number) => void;
}) {
  const [name, setName] = useState("");
  const [mission, setMission] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const company = await api.createCompany(name, mission);
      onCreated(company.id);
    } catch (err) {
      setError(String(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="mx-auto mt-20 max-w-md rounded-xl border border-slate-700 bg-slate-800 p-6">
      <h1 className="mb-4 text-xl font-bold text-slate-100">
        Create a Company
      </h1>
      <form onSubmit={submit} className="space-y-4">
        <div>
          <label className="block text-sm text-slate-300">Name</label>
          <input
            className="mt-1 w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-slate-100"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
        </div>
        <div>
          <label className="block text-sm text-slate-300">Mission</label>
          <textarea
            className="mt-1 w-full rounded border border-slate-600 bg-slate-900 px-3 py-2 text-slate-100"
            value={mission}
            onChange={(e) => setMission(e.target.value)}
          />
        </div>
        {error && <p className="text-sm text-rose-400">{error}</p>}
        <button
          type="submit"
          disabled={submitting}
          className="w-full rounded bg-indigo-600 px-4 py-2 font-semibold text-white hover:bg-indigo-500 disabled:opacity-50"
        >
          {submitting ? "Creating..." : "Create Company"}
        </button>
      </form>
    </div>
  );
}
