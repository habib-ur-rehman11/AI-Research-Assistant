from typing import TypedDict


class Finding(TypedDict):
    sub_question: str
    chunks: list[dict]
    confidence: float
    flagged: bool
    note: str


class ResearchState(TypedDict):
    query: str
    sub_questions: list[str]
    findings: list[Finding]
    report: str
    sources: list[dict]
