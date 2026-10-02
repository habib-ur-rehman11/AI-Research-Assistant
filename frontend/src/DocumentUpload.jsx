import { useState, useRef } from "react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const API_KEY = import.meta.env.VITE_API_KEY || "dev-local-key";

export default function DocumentUpload({ documents, setDocuments }) {
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");
  const inputRef = useRef(null);

  async function handleFiles(files) {
    setError("");
    setUploading(true);

    for (const file of files) {
      if (!file.name.toLowerCase().endsWith(".pdf")) {
        setError(`Skipped "${file.name}" — only PDF files are supported.`);
        continue;
      }

      const formData = new FormData();
      formData.append("file", file);

      try {
        const res = await fetch(`${API_URL}/api/documents/upload`, {
          method: "POST",
          headers: { "x-api-key": API_KEY },
          body: formData,
        });

        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body.detail || `Upload failed (${res.status})`);
        }

        const result = await res.json();
        setDocuments((prev) => [...prev, result]);
      } catch (e) {
        setError(e.message);
      }
    }

    setUploading(false);
  }

  return (
    <div className="card">
      <div
        className="upload-zone"
        onClick={() => inputRef.current?.click()}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          handleFiles(Array.from(e.dataTransfer.files));
        }}
      >
        <input
          ref={inputRef}
          type="file"
          accept=".pdf"
          multiple
          onChange={(e) => handleFiles(Array.from(e.target.files))}
        />
        <p style={{ margin: 0, fontSize: 14 }}>
          {uploading ? "Uploading & indexing..." : "Click or drag PDFs here to add to the knowledge base"}
        </p>
      </div>

      {error && <div className="error-box">{error}</div>}

      {documents.length > 0 && (
        <div style={{ marginTop: 12 }}>
          {documents.map((doc) => (
            <span key={doc.document_id} className="doc-chip">
              {doc.document_name} · {doc.chunks_indexed} chunks
            </span>
          ))}
        </div>
      )}
    </div>
  );
}
