from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    openai_api_key: str = ""
    weaviate_url: str = "http://localhost:8080"
    weaviate_api_key: str = ""
    redis_url: str = "redis://localhost:6379/0"
    api_auth_key: str = "dev-local-key"

    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"

    chunk_size: int = 800
    chunk_overlap: int = 150
    cache_ttl_seconds: int = 3600

    class Config:
        env_file = ".env"


settings = Settings()
