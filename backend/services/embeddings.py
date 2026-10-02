from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from config import settings

_client: AsyncOpenAI | None = None


def get_openai_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=8))
async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Batch-embeds a list of strings. OpenAI allows up to 2048 inputs per call."""
    client = get_openai_client()
    all_embeddings: list[list[float]] = []

    batch_size = 100
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = await client.embeddings.create(
            model=settings.embedding_model,
            input=batch,
        )
        all_embeddings.extend([d.embedding for d in response.data])

    return all_embeddings


async def embed_query(query: str) -> list[float]:
    result = await embed_texts([query])
    return result[0]
