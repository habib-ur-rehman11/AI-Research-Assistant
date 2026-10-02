import uuid
from services.pdf_parser import extract_text_from_pdf, chunk_text
from services.embeddings import embed_texts
from services.vectorstore import get_weaviate_client, ensure_schema, COLLECTION_NAME


async def ingest_pdf(filepath: str, document_name: str) -> dict:
    ensure_schema()

    pages = extract_text_from_pdf(filepath)
    if not pages:
        raise ValueError("No extractable text found in PDF")

    chunks = chunk_text(pages)
    if not chunks:
        raise ValueError("Chunking produced no content")

    texts = [c["text"] for c in chunks]
    embeddings = await embed_texts(texts)

    document_id = str(uuid.uuid4())
    client = get_weaviate_client()
    collection = client.collections.get(COLLECTION_NAME)

    with collection.batch.dynamic() as batch:
        for chunk, vector in zip(chunks, embeddings):
            batch.add_object(
                properties={
                    "text": chunk["text"],
                    "document_id": document_id,
                    "document_name": document_name,
                    "page_number": chunk["page_number"],
                },
                vector=vector,
            )

    return {
        "document_id": document_id,
        "document_name": document_name,
        "chunks_indexed": len(chunks),
        "pages_processed": len(pages),
    }
