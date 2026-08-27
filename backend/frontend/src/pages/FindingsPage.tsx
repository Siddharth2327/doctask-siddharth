import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useCase } from "../lib/CaseContext";
import { StatusStamp } from "../components/StatusStamp";
import {
  ApiError,
  decideFinding,
  finalizeRun,
  listFindings,
  type CommitResult,
  type Finding,
} from "../lib/api";

const TYPE_LABEL: Record<Finding["type"], string> = {
  conflict: "Conflict",
  extraction: "New value",
  rule_violation: "Rule violation",
};

function FindingCard({
  finding,
  onDecide,
}: {
  finding: Finding;
  onDecide: (
    findingId: string,
    decision: "approved" | "rejected",
    editedValue?: string,
  ) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [editedValue, setEditedValue] = useState(finding.proposed_value ?? "");
  const reviewable = finding.status === "pending";

  return (
    <div className="card finding-card" data-status={finding.status}>
      <div className="finding-head">
        <div>
          <div className="finding-field">
            {TYPE_LABEL[finding.type]}
            {finding.field ? ` · ${finding.field}` : ""}
            {" · "}
            {finding.severity} severity
          </div>

          {editing ? (
            <input
              type="text"
              value={editedValue}
              onChange={(event) => setEditedValue(event.target.value)}
              style={{ marginTop: "0.35rem" }}
            />
          ) : (
            finding.proposed_value !== null && (
              <div className="finding-value">{finding.proposed_value}</div>
            )
          )}
        </div>

        <StatusStamp status={finding.status} />
      </div>

      <p className="finding-rationale">{finding.rationale}</p>

      {finding.evidence_ids.length > 0 && (
        <div className="evidence-quote">
          {finding.evidence_ids.length} supporting evidence record
          {finding.evidence_ids.length === 1 ? "" : "s"}
        </div>
      )}

      {finding.reviewer && (
        <div className="usage-line">
          reviewed by {finding.reviewer}
          {finding.review_comment ? ` — "${finding.review_comment}"` : ""}
        </div>
      )}

      {reviewable && (
        <div className="btn-row" style={{ marginTop: "0.75rem" }}>
          {editing ? (
            <>
              <button
                className="btn btn--approve"
                onClick={() => onDecide(finding.id, "approved", editedValue)}
              >
                Approve edited value
              </button>
              <button className="btn btn--ghost" onClick={() => setEditing(false)}>
                Cancel edit
              </button>
            </>
          ) : (
            <>
              <button
                className="btn btn--approve"
                onClick={() => onDecide(finding.id, "approved")}
              >
                Approve
              </button>
              <button
                className="btn btn--reject"
                onClick={() => onDecide(finding.id, "rejected")}
              >
                Reject
              </button>
              {finding.proposed_value !== null && (
                <button className="btn btn--ghost" onClick={() => setEditing(true)}>
                  Edit value
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}

export function FindingsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { caseId } = useCase();

  const runId = searchParams.get("runId") ?? "";
  const [lookupRunId, setLookupRunId] = useState(runId);

  const [findings, setFindings] = useState<Finding[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reviewer, setReviewer] = useState("reviewer@example.com");
  const [commitResult, setCommitResult] = useState<CommitResult | null>(null);
  const [finalizing, setFinalizing] = useState(false);

  async function refresh(targetRunId: string) {
    if (!targetRunId) return;

    setLoading(true);
    setError(null);

    try {
      const result = await listFindings({ runId: targetRunId });
      setFindings(result.findings);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load findings.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (runId) refresh(runId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [runId]);

  function handleLookup(event: React.FormEvent) {
    event.preventDefault();
    if (!lookupRunId.trim()) return;
    setSearchParams({ runId: lookupRunId.trim() });
  }

  async function handleDecide(
    findingId: string,
    decision: "approved" | "rejected",
    editedValue?: string,
  ) {
    setError(null);

    try {
      await decideFinding({
        findingId,
        decision,
        reviewer: reviewer.trim() || "reviewer@example.com",
        editedValue,
      });
      await refresh(runId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not record decision.");
    }
  }

  async function handleFinalize() {
    setFinalizing(true);
    setError(null);

    try {
      const result = await finalizeRun(runId);
      setCommitResult(result);
      await refresh(runId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not commit run.");
    } finally {
      setFinalizing(false);
    }
  }

  const pendingCount = findings.filter((f) => f.status === "pending").length;

  return (
    <div>
      <div className="page-header">
        <h1>Findings Review</h1>
        <p>
          Approve, reject, or edit each finding individually. Only approved
          findings are ever committed to the case's canonical register —
          rejections are recorded but never overwrite what's already there.
          {caseId && ` Active case: ${caseId}.`}
        </p>
      </div>

      {!runId && (
        <form className="card" onSubmit={handleLookup}>
          <div className="btn-row">
            <input
              type="text"
              placeholder="run id"
              value={lookupRunId}
              onChange={(event) => setLookupRunId(event.target.value)}
            />
            <button className="btn" type="submit">
              Load findings
            </button>
          </div>
        </form>
      )}

      {error && <div className="error-banner">{error}</div>}

      {runId && (
        <>
          <div className="field" style={{ maxWidth: "20rem" }}>
            <label htmlFor="reviewer">Reviewing as</label>
            <input
              id="reviewer"
              type="text"
              value={reviewer}
              onChange={(event) => setReviewer(event.target.value)}
            />
          </div>

          {loading ? (
            <p>Loading…</p>
          ) : findings.length === 0 ? (
            <div className="empty-state">No findings for this run.</div>
          ) : (
            findings.map((finding) => (
              <FindingCard key={finding.id} finding={finding} onDecide={handleDecide} />
            ))
          )}

          {findings.length > 0 && (
            <div className="card" style={{ marginTop: "1.5rem" }}>
              <div className="btn-row">
                <button
                  className="btn"
                  onClick={handleFinalize}
                  disabled={finalizing || pendingCount === findings.length}
                >
                  {finalizing ? "Committing…" : "Commit approved findings"}
                </button>
                {pendingCount > 0 && (
                  <span className="usage-line">
                    {pendingCount} finding{pendingCount === 1 ? "" : "s"} still
                    pending review
                  </span>
                )}
              </div>

              {commitResult && (
                <div className="usage-line" style={{ marginTop: "0.75rem" }}>
                  committed {commitResult.committed.length} · skipped (rejected){" "}
                  {commitResult.skipped_rejected.length} · already committed{" "}
                  {commitResult.already_committed.length}
                </div>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
}
