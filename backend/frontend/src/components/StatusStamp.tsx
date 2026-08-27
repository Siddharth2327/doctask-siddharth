import type { FindingStatus } from "../lib/api";

const LABELS: Record<FindingStatus, string> = {
  pending: "pending review",
  approved: "approved",
  rejected: "rejected",
  committed: "committed",
};

export function StatusStamp({ status }: { status: FindingStatus }) {
  return (
    <span className={`stamp stamp--${status}`} aria-label={`status: ${status}`}>
      {LABELS[status]}
    </span>
  );
}
