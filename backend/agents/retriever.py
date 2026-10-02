import asyncio
from services.retrieval import hybrid_search
from agents.state import ResearchState


async def _retrieve_one(sub_question: str) -> dict:
    chunks = await hybrid_search(sub_question, top_k=5)
    return {
        "sub_question": sub_question,
        "chunks": chunks,
        "confidence": 0.0,   # filled in by Critic
        "flagged": False,
        "note": "",
    }


async def retriever_node(state: ResearchState) -> dict:
    sub_questions = state["sub_questions"]
    findings = await asyncio.gather(*[_retrieve_one(q) for q in sub_questions])
    return {"findings": list(findings)}
