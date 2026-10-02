import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import DocumentUpload from "./DocumentUpload.jsx";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const WS_URL = API_URL.replace(/^http/, "ws");
const API_KEY = import.meta.env.VITE_API_KEY || "dev-local-key";

const STAGE_LABELS = {
  planning: "Breaking down your question...",
  retrieving: "Searching documents...",
  validating: "Validating findings...",
  writing: "Writing report...",
};

export default function App() {
  const [documents, setDocuments] = useState([]);
  const [query, setQuery] = useState("");
  const [report, setReport] = useState("");
  const [sources, setSources] = useState([]);
  const [stage, setStage] = useState(null);
  const [error, setError] = useState("");
  const [running, setRunning] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    fetch(`${API_URL}/api/documents`, { headers: { "x-api-key": API_KEY } })
      .then((res) => (res.ok ? res.json() : []))
      .then(setDocuments)
      .catch(() => {});
  }, []);

  function runQuery() {
    if (!query.trim() || running) return;

    setReport("");
    setSources([]);
    setError("");
    setRunning(true);
    setStage("planning");

    const ws = new WebSocket(`${WS_URL}/api/research/stream`);
    wsRef.current = ws;

    ws.onopen = () => {
      ws.send(JSON.stringify({ api_key: API_KEY, query }));
    };

    ws.onmessage = (event) => {
      const msg = JSON.parse(event.data);

      if (msg.type === "status") {
        setStage(msg.stage);
      } else if (msg.type === "token") {
        setReport((prev) => prev + msg.content);
      } else if (msg.type === "sources") {
        setSources(msg.sources);
      } else if (msg.type === "error") {
        setError(msg.message);
        setRunning(false);
      } else if (msg.type === "done") {
        setStage(null);
        setRunning(false);
        ws.close();
      }
    };

    ws.onerror = () => {
      setError("Connection error — is the backend running?");
      setRunning(false);
    };
  }

  return (
    <div className="app">
      <div className="header">
        <h1>Multi-Agent RAG Research Copilot</h1>
        <p>Upload PDFs, then ask a question. A planner, retriever, critic, and writer agent collaborate on the answer.</p>
      </div>

      <DocumentUpload documents={documents} setDocuments={setDocuments} />

      <div className="card">
        <div className="query-row">
          <textarea
            rows={2}
            placeholder={documents.length === 0 ? "Upload a PDF first, then ask a question..." : "Ask a question about your documents..."}
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                runQuery();
              }
            }}
          />
          <button onClick={runQuery} disabled={running || !query.trim()}>
            {running ? "Researching..." : "Ask"}
          </button>
        </div>

        {stage && (
          <div className="status-bar">
            <span className="status-dot" />
            {STAGE_LABELS[stage] || stage}
          </div>
        )}

        {error && <div className="error-box">{error}</div>}

        {report && (
          <div style={{ marginTop: 16 }}>
            <div className="report">
              <ReactMarkdown>{report}</ReactMarkdown>
            </div>

            {sources.length > 0 && (
              <div className="sources">
                <h4>Sources</h4>
                {sources.map((s, i) => (
                  <div key={i} className="source-item">
                    {s.document_name} — page {s.page_number}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
