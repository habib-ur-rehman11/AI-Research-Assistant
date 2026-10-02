import json
import hashlib
import redis.asyncio as redis
from config import settings

_pool: redis.Redis | None = None


def get_redis() -> redis.Redis:
    global _pool
    if _pool is None:
        _pool = redis.from_url(settings.redis_url, decode_responses=True)
    return _pool


def _key_for(query: str) -> str:
    normalized = query.strip().lower()
    digest = hashlib.sha256(normalized.encode()).hexdigest()
    return f"research:cache:{digest}"


async def check_cache(query: str) -> dict | None:
    r = get_redis()
    raw = await r.get(_key_for(query))
    if raw:
        return json.loads(raw)
    return None


async def write_cache(query: str, result: dict, ttl: int | None = None) -> None:
    r = get_redis()
    await r.set(
        _key_for(query),
        json.dumps(result),
        ex=ttl or settings.cache_ttl_seconds,
    )
