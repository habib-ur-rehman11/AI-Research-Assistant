from services.embeddings import get_openai_client
from config import settings
from agents.state import ResearchState

WRITER_PROMPT = """You are a research writer. Using ONLY the verified findings below, write a \
clear, well-structured markdown report answering the user's original question.

Rules:
- Cite sources inline like [Source: {{document_name}}, p.{{page_number}}] after claims that use them.
- If a sub-question was flagged as low-confidence or unsupported, explicitly note the gap in the report \
rather than guessing.
- Do not invent facts not present in the findings.
- Use headings for each major sub-topic.

Original question: {query}

Verified findings:
{findings_block}
"""


def _format_findings_block(findings: list[dict]) -> str:
    blocks = []
    for f in findings:
        status = "⚠ LOW CONFIDENCE / FLAGGED" if f["flagged"] else f"confidence={f['confidence']:.2f}"
        chunk_lines = "\n".join(
            f'  - "{c["text"][:300]}" [Source: {c["document_name"]}, p.{c["page_number"]}]'
            for c in f["chunks"][:3]
        )
        blocks.append(
            f"Sub-question: {f['sub_question']} ({status})\n"
            f"Critic note: {f['note']}\n"
            f"{chunk_lines}"
        )
    return "\n\n".join(blocks)


def _collect_sources(findings: list[dict]) -> list[dict]:
    seen = set()
    sources = []
    for f in findings:
        for c in f["chunks"]:
            key = (c["document_name"], c["page_number"])
            if key not in seen:
                seen.add(key)
                sources.append({"document_name": c["document_name"], "page_number": c["page_number"]})
    return sources


async def writer_node(state: ResearchState) -> dict:
    """Non-streaming version — used by the REST endpoint."""
    client = get_openai_client()
    prompt = WRITER_PROMPT.format(
        query=state["query"],
        findings_block=_format_findings_block(state["findings"]),
    )

    response = await client.chat.completions.create(
        model=settings.chat_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
    )

    report = response.choices[0].message.content
    return {"report": report, "sources": _collect_sources(state["findings"])}


async def stream_writer(state: ResearchState):
    """Streaming generator — used by the WebSocket/SSE endpoints. Yields text chunks."""
    client = get_openai_client()
    prompt = WRITER_PROMPT.format(
        query=state["query"],
        findings_block=_format_findings_block(state["findings"]),
    )

    stream = await client.chat.completions.create(
        model=settings.chat_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
