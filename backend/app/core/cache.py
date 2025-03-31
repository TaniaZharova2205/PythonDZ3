import redis
from app.core.config import REDIS_URL

redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

def get_url_from_cache(short_code: str) -> str:
    key = f"link:{short_code}"
    value = redis_client.get(key)
    return value if value else None

def set_url_to_cache(short_code: str, url: str, ttl: int = 3600):
    key = f"link:{short_code}"
    redis_client.setex(key, ttl, url)

def delete_url_cache(short_code: str):
    key = f"link:{short_code}"
    redis_client.delete(key)