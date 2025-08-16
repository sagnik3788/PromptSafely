import redis
import os
from dotenv import load_dotenv

load_dotenv() 

class RedisClient:
    def __init__(self):
        self.host = os.getenv("REDIS_HOST","127.0.0.1")
        self.port = os.getenv("REDIS_PORT", "6379")
        self.db   = os.getenv("REDIS_DB", "0")
        
        #  pool it so that we dont need to create tcp connection again n again
        self.pool = redis.ConnectionPool(
            host = self.host,
            port = self.port,
            db   = self.db,
            decode_responses = True,
            max_connections = 5
        )
        
        self.client = redis.Redis(connection_pool= self.pool)
    
    def set(self, key: str, value: str, ttl: int | None = 3600):
        return self.client.set(name=key, value=value, ex=ttl)
    
    def get(self, key: str):
        return self.client.get(name=key)

    def delete(self, key: str):
        return self.client.delete(key)

    def exists(self, key: str):
        return self.client.exists(key)


