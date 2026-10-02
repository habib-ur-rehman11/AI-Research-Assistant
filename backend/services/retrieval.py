from services.vectorstore import get_weaviate_client, COLLECTION_NAME
from services.embeddings import embed_query
import weaviate.classes as wvc


async def hybrid_search(query: str, top_k: int = 5, alpha: float = 0.5) -> list[dict]:
    """
    alpha=0 -> pure keyword (BM25), alpha=1 -> pure vector search.
    0.5 blends both, which is the sane default for most queries.
    """
    client = get_weaviate_client()
    collection = client.collections.get(COLLECTION_NAME)

    query_vector = await embed_query(query)

    response = collection.query.hybrid(
        query=query,
        vector=query_vector,
        alpha=alpha,
        limit=top_k,
        return_metadata=wvc.query.MetadataQuery(score=True),
    )

    results = []
    for obj in response.objects:
        results.append({
            "text": obj.properties.get("text", ""),
            "document_name": obj.properties.get("document_name", ""),
            "page_number": obj.properties.get("page_number"),
            "score": obj.metadata.score if obj.metadata else None,
        })
    return results
