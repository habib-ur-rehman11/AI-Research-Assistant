import json
import asyncio
from services.embeddings import get_openai_client
from config import settings
from agents.state import ResearchState

CRITIC_PROMPT = """You are a fact-checking critic. Given a sub-question and retrieved passages, \
judge whether the passages contain enough information to answer the sub-question.

Sub-question: {sub_question}

Retrieved passages:
{passages}

Respond ONLY with JSON: {{"confidence": <0.0-1.0>, "flagged": <true/false>, "note": "<one sentence>"}}
flagged=true means the passages do NOT adequately support an answer (e.g. missing, contradictory, off-topic)."""


async def _critique_one(finding: dict) -> dict:
    if not finding["chunks"]:
        return {**finding, "confidence": 0.0, "flagged": True, "note": "No relevant chunks retrieved."}

    passages = "\n---\n".join(c["text"][:500] for c in finding["chunks"][:3])
    client = get_openai_client()

    response = await client.chat.completions.create(
        model=settings.chat_model,
        messages=[{
            "role": "user",
            "content": CRITIC_PROMPT.format(
                sub_question=finding["sub_question"],
                passages=passages,
            ),
        }],
        temperature=0,
    )
    raw = response.choices[0].message.content.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").replace("json", "", 1).strip()

    try:
        verdict = json.loads(raw)
    except Exception:
        verdict = {"confidence": 0.5, "flagged": False, "note": "Critic parse failure; defaulting to neutral."}

    return {
        **finding,
        "confidence": float(verdict.get("confidence", 0.5)),
        "flagged": bool(verdict.get("flagged", False)),
        "note": verdict.get("note", ""),
    }


async def critic_node(state: ResearchState) -> dict:
    critiqued = await asyncio.gather(*[_critique_one(f) for f in state["findings"]])
    return {"findings": critiqued}
