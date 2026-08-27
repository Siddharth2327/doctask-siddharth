import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ApiError,
  listDocuments,
  uploadDocument,
  type DocumentSummary,
} from "../lib/api";
import { DocumentVersionsPanel } from "../components/DocumentVersionsPanel";

export function DocumentsPage() {
  const navigate = useNavigate();

  const [documents, setDocuments] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [name, setName] = useState("");
  const [source, setSource] = useState("upload");
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);

  const [expandedDocumentId, setExpandedDocumentId] = useState<string | null>(
    null,
  );

  async function refresh() {
    setLoading(true);
    setError(null);

    try {
      const result = await listDocuments();
      setDocuments(result.documents);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not load documents.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleUpload(event: React.FormEvent) {
    event.preventDefault();

    if (!file || !name.trim()) {
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const result = await uploadDocument({ file, name: name.trim(), source });
      setName("");
      setFile(null);
      await refresh();
      navigate(
        `/runs?documentId=${result.id}&documentVersionId=${result.version.id}`,
      );
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  return (
    <div>
      <div className="page-header">
        <h1>Documents</h1>
        <p>
          Upload a contract, invoice, or renewal notice. Supported formats:
          plain text, PDF (including scanned pages), Word (.docx), and
          scanned images (PNG/JPEG/TIFF) — every format is processed into
          evidence-backed, page-aware source references.
        </p>
      </div>

      <form className="card" onSubmit={handleUpload}>
        <div className="field">
          <label htmlFor="doc-name">Document name</label>
          <input
            id="doc-name"
            type="text"
            placeholder="Acme Master Services Agreement"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </div>

        <div className="field">
          <label htmlFor="doc-source">Source</label>
          <input
            id="doc-source"
            type="text"
            value={source}
            onChange={(event) => setSource(event.target.value)}
          />
        </div>

        <div className="field">
          <label htmlFor="doc-file">File</label>
          <input
            id="doc-file"
            type="file"
            onChange={(event) => setFile(event.target.files?.[0] ?? null)}
          />
        </div>

        <button className="btn" type="submit" disabled={uploading || !file || !name.trim()}>
          {uploading ? "Uploading…" : "Upload & continue to run"}
        </button>
      </form>

      {error && <div className="error-banner" style={{ marginTop: "1rem" }}>{error}</div>}

      <h2 style={{ marginTop: "2.5rem" }}>Uploaded documents</h2>

      {loading ? (
        <p>Loading…</p>
      ) : documents.length === 0 ? (
        <div className="empty-state">No documents uploaded yet.</div>
      ) : (
        <div className="card">
          {documents.map((document) => (
            <div key={document.id}>
              <div className="doc-row">
                <div>
                  <div className="doc-name">{document.name}</div>
                  <div className="doc-meta">
                    {document.source} · {new Date(document.created_at).toLocaleString()}
                  </div>
                </div>
                <div className="btn-row">
                  <button
                    className="btn btn--ghost"
                    onClick={() =>
                      setExpandedDocumentId(
                        expandedDocumentId === document.id ? null : document.id,
                      )
                    }
                  >
                    {expandedDocumentId === document.id
                      ? "Hide versions"
                      : "Versions / Upload new version"}
                  </button>
                  <button
                    className="btn btn--ghost"
                    onClick={() => navigate(`/runs?documentId=${document.id}`)}
                  >
                    Start run →
                  </button>
                </div>
              </div>

              {expandedDocumentId === document.id && (
                <DocumentVersionsPanel documentId={document.id} />
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}