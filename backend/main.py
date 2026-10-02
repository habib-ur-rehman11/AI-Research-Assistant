from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import research, documents
from services.vectorstore import close_weaviate_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    close_weaviate_client()


app = FastAPI(title="Multi-Agent RAG Research Copilot", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(research.router, prefix="/api", tags=["research"])
app.include_router(documents.router, prefix="/api", tags=["documents"])


@app.get("/health")
async def health():
    return {"status": "ok"}
