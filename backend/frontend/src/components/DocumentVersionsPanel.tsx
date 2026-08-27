import { useEffect, useState } from "react";
import {
  ApiError,
  listVersions,
  uploadNewVersion,
  type DocumentVersion,
} from "../lib/api";

export function DocumentVersionsPanel({ documentId }: { documentId: string }) {
  const [versions, setVersions] = useState<DocumentVersion[] | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [file, setFile] = useState<File | null>(null);
  const [source, setSource] = useState("upload");
  const [uploading, setUploading] = useState(false);
  const [confirmation, setConfirmation] = useState<string | null>(null);

  async function refresh() {
    setLoading(true);
    setError(null);

    try {
      const result = await listVersions(documentId);
      // Newest first is the more useful default for "did my upload land".
      setVersions([...result.versions].sort((a, b) => b.version_number - a.version_number));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load versions.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [documentId]);

  async function handleUpload(event: React.FormEvent) {
    event.preventDefault();

    if (!file) return;

    setUploading(true);
    setError(null);
    setConfirmation(null);

    try {
      const result = await uploadNewVersion({ documentId, file, source });
      setFile(null);

      if (result.is_duplicate) {
        setConfirmation(
          `This file's content matches an existing version — no new version was created. Reused version ${result.version.version_number}.`,
        );
      } else {
        setConfirmation(
          `New version ${result.version.version_number} created (${result.version.filename}).`,
        );
      }

      await refresh();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Could not upload new version.",
      );
    } finally {
      setUploading(false);
    }
  }

  return (
    <div style={{ padding: "0 0 1rem", borderBottom: "1px solid var(--rule)" }}>
      {error && <div className="error-banner">{error}</div>}
      {confirmation && (
        <div className="usage-line" style={{ marginBottom: "0.75rem" }}>
          {confirmation}
        </div>
      )}

      {loading || versions === null ? (
        <p className="doc-meta">Loading versions…</p>
      ) : versions.length === 0 ? (
        <div className="empty-state">No versions found.</div>
      ) : (
        <table className="register" style={{ marginBottom: "1rem" }}>
          <thead>
            <tr>
              <th>Version</th>
              <th>Filename</th>
              <th>Content type</th>
              <th>Source</th>
              <th>Uploaded</th>
              <th>Version ID</th>
              <th>Parent version</th>
            </tr>
          </thead>
          <tbody>
            {versions.map((version) => (
              <tr key={version.id}>
                <td className="field-cell">v{version.version_number}</td>
                <td>{version.filename}</td>
                <td className="doc-meta">{version.content_type}</td>
                <td className="doc-meta">{version.source}</td>
                <td className="doc-meta">
                  {new Date(version.created_at).toLocaleString()}
                </td>
                <td className="doc-meta mono" title={version.id}>
                  {version.id.slice(0, 8)}…
                </td>
                <td className="doc-meta mono">
                  {version.parent_version_id
                    ? `${version.parent_version_id.slice(0, 8)}…`
                    : "— (first version)"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <form onSubmit={handleUpload}>
        <div className="btn-row" style={{ flexWrap: "wrap" }}>
          <input
            type="file"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
          <input
            type="text"
            value={source}
            onChange={(event) => setSource(event.target.value)}
            placeholder="source"
            style={{ maxWidth: "10rem" }}
          />
          <button className="btn" type="submit" disabled={uploading || !file}>
            {uploading ? "Uploading…" : "Upload new version"}
          </button>
        </div>
      </form>
    </div>
  );
}