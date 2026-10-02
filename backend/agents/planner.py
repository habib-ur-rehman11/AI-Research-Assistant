import json
from services.embeddings import get_openai_client
from config import settings
from agents.state import ResearchState

PLANNER_PROMPT = """You are a research planner. Break the user's question into 2-4 focused \
sub-questions that, together, would let someone answer the original question thoroughly \
using a document search system. Avoid redundant sub-questions.

Respond ONLY with a JSON array of strings, nothing else. Example:
["What is X?", "How does X compare to Y?"]

User question: {query}"""


async def planner_node(state: ResearchState) -> dict:
    client = get_openai_client()
    response = await client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "user", "content": PLANNER_PROMPT.format(query=state["query"])}
        ],
        temperature=0.2,
    )
    raw = response.choices[0].message.content.strip()

    # Model may wrap in code fences despite instructions — strip defensively
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    try:
        sub_questions = json.loads(raw)
        if not isinstance(sub_questions, list):
            raise ValueError
    except Exception:
        sub_questions = [state["query"]]  # fallback: treat original query as the only sub-question

    return {"sub_questions": sub_questions[:4]}
