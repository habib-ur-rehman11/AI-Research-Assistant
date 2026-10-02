from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, field_validator

from services.auth import verify_api_key
from services.cache import check_cache, write_cache
from agents.supervisor import run_research_pipeline, stream_research_pipeline

router = APIRouter()


class ResearchRequest(BaseModel):
    query: str
    max_sources: int = 10

    @field_validator("query")
    @classmethod
    def query_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Query cannot be empty")
        if len(v) > 2000:
            raise ValueError("Query exceeds 2000 character limit")
        return v

    @field_validator("max_sources")
    @classmethod
    def sources_in_range(cls, v: int) -> int:
        if not (1 <= v <= 50):
            raise ValueError("max_sources must be between 1 and 50")
        return v


class ResearchResponse(BaseModel):
    report: str
    sources: list[dict]
    latency_ms: int
    cached: bool


@router.post("/research", response_model=ResearchResponse)
async def research(req: ResearchRequest, api_key: str = Depends(verify_api_key)):
    cached = await check_cache(req.query)
    if cached:
        return ResearchResponse(**cached, cached=True)

    try:
        result = await run_research_pipeline(req.query, req.max_sources)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Research pipeline failed: {e}")

    await write_cache(req.query, result)
    return ResearchResponse(**result, cached=False)


@router.websocket("/research/stream")
async def research_stream(websocket: WebSocket):
    await websocket.accept()

    # Simple auth: client sends {"api_key": "...", "query": "..."} as first message
    try:
        data = await websocket.receive_json()
    except WebSocketDisconnect:
        return

    from config import settings
    if data.get("api_key") != settings.api_auth_key:
        await websocket.send_json({"type": "error", "message": "Invalid API key"})
        await websocket.close(code=4401)
        return

    query = (data.get("query") or "").strip()
    if not query:
        await websocket.send_json({"type": "error", "message": "Query cannot be empty"})
        await websocket.close(code=4400)
        return

    try:
        async for event in stream_research_pipeline(query):
            await websocket.send_json(event)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
