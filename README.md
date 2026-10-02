# Multi-Agent RAG Research Copilot

Upload PDFs, ask a question, and watch four specialist agents — Planner, Retriever, Critic, and Writer —
collaborate in real time to produce a cited research report.

## Architecture

```
User query → Planner (breaks into sub-questions)
           → Retriever (parallel hybrid search over Weaviate)
           → Critic (validates each finding, flags gaps)
           → Writer (streams a cited markdown report)
```

- **Orchestration**: LangGraph state machine
- **Vector DB**: Weaviate (hybrid BM25 + dense search)
- **Cache**: Redis (hashed-query response cache)
- **LLM**: OpenAI (gpt-4o-mini by default — change in `backend/config.py`)
- **Backend**: FastAPI, WebSocket streaming
- **Frontend**: React + Vite

## Run it

1. Copy the env template and add your OpenAI key:
   ```bash
   cp .env.example .env
   # edit .env and paste your OPENAI_API_KEY
   ```

2. Start everything:
   ```bash
   docker compose up --build
   ```

3. Open the app:
   - Frontend: http://localhost:5173
   - Backend API docs: http://localhost:8000/docs
   - Weaviate console: http://localhost:8080

4. Upload a PDF in the UI, then ask a question about it.

## Project layout

```
backend/
  agents/          # planner, retriever, critic, writer, supervisor (LangGraph)
  routers/         # FastAPI endpoints (research, documents)
  services/        # auth, cache, embeddings, vectorstore, retrieval, pdf parsing
  main.py
frontend/
  src/
    App.jsx        # query UI + WebSocket streaming
    DocumentUpload.jsx
docker-compose.yml
```

## API quick reference

**Upload a document**
```bash
curl -X POST http://localhost:8000/api/documents/upload \
  -H "x-api-key: dev-local-key" \
  -F "file=@/path/to/doc.pdf"
```

**Ask a question (REST, non-streaming)**
```bash
curl -X POST http://localhost:8000/api/research \
  -H "x-api-key: dev-local-key" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the main findings?"}'
```

**Ask a question (WebSocket, streaming)** — see `frontend/src/App.jsx` for a working client.

## Notes on what's stubbed vs production-real

This runs fully end-to-end with real OpenAI calls, real Weaviate hybrid search, and real Redis caching —
nothing is mocked. For a CV-ready production version, the next additions worth making are:

- **Observability**: OpenTelemetry traces + Prometheus metrics + Grafana dashboard (mentioned in the original
  roadmap, not wired up here to keep this runnable without an observability stack).
- **Evals**: RAGAS faithfulness/relevancy scoring on a held-out query set.
- **Auth**: swap the static `API_AUTH_KEY` for real per-user API keys / OAuth.
- **Persistent doc list**: the uploaded-documents list currently lives in frontend React state and resets on
  page reload — Weaviate itself retains the data permanently. A `GET /api/documents` endpoint would let the
  UI rehydrate that list from Weaviate on load.
