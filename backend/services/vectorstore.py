import weaviate
from weaviate.classes.init import Auth
import weaviate.classes as wvc
from config import settings

_client: weaviate.WeaviateClient | None = None

COLLECTION_NAME = "DocumentChunk"


def get_weaviate_client() -> weaviate.WeaviateClient:
    global _client
    if _client is None or not _client.is_connected():
        if settings.weaviate_api_key:
            # Weaviate Cloud (WCD) — used when running without Docker
            _client = weaviate.connect_to_weaviate_cloud(
                cluster_url=settings.weaviate_url,
                auth_credentials=Auth.api_key(settings.weaviate_api_key),
            )
        else:
            # Local instance via Docker — no auth
            host = settings.weaviate_url.replace("http://", "").replace("https://", "")
            host_only, port = host.split(":") if ":" in host else (host, "8080")
            _client = weaviate.connect_to_local(host=host_only, port=int(port))
    return _client


def ensure_schema() -> None:
    client = get_weaviate_client()
    if client.collections.exists(COLLECTION_NAME):
        return

    client.collections.create(
        name=COLLECTION_NAME,
        vectorizer_config=wvc.config.Configure.Vectorizer.none(),
        properties=[
            wvc.config.Property(name="text", data_type=wvc.config.DataType.TEXT),
            wvc.config.Property(name="document_id", data_type=wvc.config.DataType.TEXT),
            wvc.config.Property(name="document_name", data_type=wvc.config.DataType.TEXT),
            wvc.config.Property(name="page_number", data_type=wvc.config.DataType.INT),
        ],
    )


def close_weaviate_client() -> None:
    global _client
    if _client is not None:
        _client.close()
        _client = None
