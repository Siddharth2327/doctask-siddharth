import { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { useCase } from "../lib/CaseContext";
import {
  ApiError,
  getRun,
  listVersions,
  startRun,
  type DocumentVersion,
  type RunStatus,
} from "../lib/api";

export function RunsPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { caseId, setCaseId } = useCase();

  const documentId = searchParams.get("documentId") ?? "";
  const preselectedVersionId = searchParams.get("documentVersionId") ?? "";

  const [versions, setVersions] = useState<DocumentVersion[]>([]);
  const [versionId, setVersionId] = useState(preselectedVersionId);
  const [localCaseId, setLocalCaseId] = useState(caseId);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [run, setRun] = useState<RunStatus | null>(null);
  const [lookupRunId, setLookupRunId] = useState("");

  useEffect(() => {
    if (!documentId) return;

    listVersions(documentId)
      .then((result) => {
        setVersions(result.versions);
        if (!versionId && result.versions.length > 0) {
          setVersionId(result.versions[result.versions.length - 1].id);
        }
      })
      .catch(() => setError("Could not load versions for this document."));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId]);

  async function handleStart(event: React.FormEvent) {
    event.preventDefault();

    if (!documentId || !versionId || !localCaseId.trim()) return;

    setStarting(true);
    setError(null);

    try {
      const result = await startRun({
        documentId,
        documentVersionId: versionId,
        caseId: localCaseId.trim(),
      });
      setCaseId(localCaseId.trim());

      const status = await getRun(result.run_id);
      setRun(status);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not start run.");
    } finally {
      setStarting(false);
    }
  }

  async function handleLookup(event: React.FormEvent) {
    event.preventDefault();
    if (!lookupRunId.trim()) return;

    setError(null);

    try {
      const status = await getRun(lookupRunId.trim());
      setRun(status);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Run not found.");
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Runs</h1>
        <p>
          Running a document processes it end to end: evidence-backed
          extraction, retrieval, conflict detection against the case's
          committed register, and deterministic rule validation — producing
          findings ready for human review.
        </p>
      </div>

      {error && <div className="error-banner">{error}</div>}

      {documentId ? (
        <form className="card" onSubmit={handleStart}>
          <div className="field">
            <label htmlFor="version-select">Document version</label>
            <select
              id="version-select"
              value={versionId}
              onChange={(event) => setVersionId(event.target.value)}
            >
              {versions.map((version) => (
                <option key={version.id} value={version.id}>
                  v{version.version_number} — {version.filename}
                </option>
              ))}
            </select>
          </div>

          <div className="field">
            <label htmlFor="case-id-input">Case ID</label>
            <input
              id="case-id-input"
              type="text"
              placeholder="CASE-ACME-001"
              value={localCaseId}
              onChange={(event) => setLocalCaseId(event.target.value)}
            />
          </div>

          <button
            className="btn"
            type="submit"
            disabled={starting || !versionId || !localCaseId.trim()}
          >
            {starting ? "Running pipeline…" : "Run pipeline"}
          </button>
        </form>
      ) : (
        <div className="empty-state">
          Pick a document from the Documents page to start a run, or look one
          up by run ID below.
        </div>
      )}

      <h2 style={{ marginTop: "2.5rem" }}>Look up a run</h2>
      <form className="card" onSubmit={handleLookup}>
        <div className="btn-row">
          <input
            type="text"
            placeholder="run id"
            value={lookupRunId}
            onChange={(event) => setLookupRunId(event.target.value)}
          />
          <button className="btn btn--ghost" type="submit">
            Look up
          </button>
        </div>
      </form>

      {run && (
        <div className="card" style={{ marginTop: "1.5rem" }}>
          <div className="finding-field">Run {run.run_id}</div>
          <div className="finding-value">Status: {run.status}</div>
          <div className="usage-line">
            case {run.case_id} · {run.input_tokens} in / {run.output_tokens} out
            tokens · est. ${run.estimated_cost.toFixed(4)}
          </div>
          <div className="btn-row" style={{ marginTop: "1rem" }}>
            <button
              className="btn"
              onClick={() => navigate(`/findings?runId=${run.run_id}`)}
            >
              Review findings →
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
