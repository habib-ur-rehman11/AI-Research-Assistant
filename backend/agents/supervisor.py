import time
from langgraph.graph import StateGraph, END
from agents.state import ResearchState
from agents.planner import planner_node
from agents.retriever import retriever_node
from agents.critic import critic_node
from agents.writer import writer_node, stream_writer


def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("planner", planner_node)
    graph.add_node("retriever", retriever_node)
    graph.add_node("critic", critic_node)
    graph.add_node("writer", writer_node)

    graph.set_entry_point("planner")
    graph.add_edge("planner", "retriever")
    graph.add_edge("retriever", "critic")
    graph.add_edge("critic", "writer")
    graph.add_edge("writer", END)

    return graph.compile()


_compiled_graph = None


def get_graph():
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_graph()
    return _compiled_graph


async def run_research_pipeline(query: str, max_sources: int = 10) -> dict:
    """Full non-streaming run — used by the REST endpoint."""
    start = time.perf_counter()
    graph = get_graph()

    initial_state: ResearchState = {
        "query": query,
        "sub_questions": [],
        "findings": [],
        "report": "",
        "sources": [],
    }

    final_state = await graph.ainvoke(initial_state)
    latency_ms = int((time.perf_counter() - start) * 1000)

    return {
        "report": final_state["report"],
        "sources": final_state["sources"][:max_sources],
        "latency_ms": latency_ms,
    }


async def stream_research_pipeline(query: str):
    """
    Runs planner -> retriever -> critic synchronously (fast, ~1-2s combined),
    then streams the writer's tokens as they're generated.
    Yields dicts: {"type": "status"|"token"|"sources"|"done", ...}
    """
    state: ResearchState = {
        "query": query,
        "sub_questions": [],
        "findings": [],
        "report": "",
        "sources": [],
    }

    yield {"type": "status", "stage": "planning"}
    state.update(await planner_node(state))

    yield {"type": "status", "stage": "retrieving"}
    state.update(await retriever_node(state))

    yield {"type": "status", "stage": "validating"}
    state.update(await critic_node(state))

    yield {"type": "status", "stage": "writing"}
    async for token in stream_writer(state):
        yield {"type": "token", "content": token}

    from agents.writer import _collect_sources
    sources = _collect_sources(state["findings"])
    yield {"type": "sources", "sources": sources}
    yield {"type": "done"}
