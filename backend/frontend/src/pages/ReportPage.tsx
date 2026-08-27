import { useEffect, useState } from "react";
import { useCase } from "../lib/CaseContext";
import { ApiError, getCaseReport, type CanonicalFact } from "../lib/api";

export function ReportPage() {
  const { caseId, setCaseId } = useCase();
  const [localCaseId, setLocalCaseId] = useState(caseId);
  const [facts, setFacts] = useState<CanonicalFact[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loadedCaseId, setLoadedCaseId] = useState<string | null>(null);

  async function load(id: string) {
    if (!id.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const result = await getCaseReport(id.trim());
      setFacts(result.facts);
      setLoadedCaseId(id.trim());
      setCaseId(id.trim());
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load report.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (caseId) load(caseId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    load(localCaseId);
  }

  return (
    <div>
      <div className="page-header">
        <h1>Case Report</h1>
        <p>
          The committed, evidence-linked register for a case — the current
          believed truth for every field, written only from approved
          findings.
        </p>
      </div>

      <form className="card" onSubmit={handleSubmit}>
        <div className="btn-row">
          <input
            type="text"
            placeholder="CASE-ACME-001"
            value={localCaseId}
            onChange={(event) => setLocalCaseId(event.target.value)}
          />
          <button className="btn" type="submit" disabled={loading}>
            {loading ? "Loading…" : "Load register"}
          </button>
        </div>
      </form>

      {error && <div className="error-banner" style={{ marginTop: "1rem" }}>{error}</div>}

      {loadedCaseId && !loading && (
        <div className="card" style={{ marginTop: "1.5rem" }}>
          <h2 style={{ marginBottom: "1rem" }}>{loadedCaseId}</h2>

          {facts.length === 0 ? (
            <div className="empty-state">
              No committed facts yet for this case — run a document and
              commit approved findings first.
            </div>
          ) : (
            <table className="register">
              <thead>
                <tr>
                  <th>Field</th>
                  <th>Value</th>
                  <th>Updated</th>
                </tr>
              </thead>
              <tbody>
                {[...facts]
                  .sort((a, b) => a.field.localeCompare(b.field))
                  .map((fact) => (
                    <tr key={fact.field}>
                      <td className="field-cell">{fact.field}</td>
                      <td className="value-cell">{fact.value}</td>
                      <td className="doc-meta">
                        {new Date(fact.updated_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          )}
        </div>
      )}
    </div>
  );
}
