import re
from pypdf import PdfReader
from config import settings


def extract_text_from_pdf(filepath: str) -> list[dict]:
    """Returns a list of {page_number, text} dicts."""
    reader = PdfReader(filepath)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        text = re.sub(r"\s+", " ", text).strip()
        if text:
            pages.append({"page_number": i + 1, "text": text})
    return pages


def chunk_text(
    pages: list[dict],
    chunk_size: int = None,
    overlap: int = None,
) -> list[dict]:
    """Sliding-window chunking that preserves page numbers for citations."""
    chunk_size = chunk_size or settings.chunk_size
    overlap = overlap or settings.chunk_overlap

    chunks = []
    for page in pages:
        text = page["text"]
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append({
                    "text": chunk.strip(),
                    "page_number": page["page_number"],
                })
            start += chunk_size - overlap
    return chunks
