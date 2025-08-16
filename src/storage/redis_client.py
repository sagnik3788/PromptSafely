import redis
import os
from dotenv import load_dotenv

load_dotenv() 

class RedisClient:
    def __init__(self):
        """
        Initialize the RedisClient by reading configuration from environment variables and creating a Redis connection pool and client.
        
        Reads:
        - REDIS_HOST (defaults to "127.0.0.1")
        - REDIS_PORT
        - REDIS_DB
        
        Creates a redis.ConnectionPool with decode_responses=True and max_connections=5, then a redis.Redis client that uses this pool. The resulting client is available as self.client and the pool as self.pool.
        """
        self.host = os.getenv("REDIS_HOST","127.0.0.1")
        self.port = os.getenv("REDIS_PORT")
        self.db   = os.getenv("REDIS_DB")
        
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
        """
        Set a string value for a key in Redis with an optional TTL.
        
        Stores `value` at `key` using the underlying Redis client. If `ttl` is provided (seconds), the key will expire after that many seconds; if `ttl` is None, the key is stored without expiration.
        
        Parameters:
            key (str): Redis key.
            value (str): Value to store.
            ttl (int | None): Time-to-live in seconds; None means no expiration. Defaults to 3600.
        
        Returns:
            bool: True if the value was set, False otherwise (per the Redis client).
        """
        return self.client.set(name=key, value=value, ex=ttl)
    
    def get(self, key: str):
        """
        Return the value stored at `key` in Redis.
        
        Retrieves the value for the given Redis key. Because the client is configured with
        `decode_responses=True`, the returned value will be a Python string (or `None` if the key does not exist).
        
        Parameters:
            key (str): Redis key name to fetch.
        
        Returns:
            str | None: The stored value as a string, or `None` if the key is not present.
        """
        return self.client.get(name=key)

    def delete(self, key: str):
        """
        Delete a key from Redis.
        
        Parameters:
            key (str): The Redis key to remove.
        
        Returns:
            int: Number of keys removed (0 if the key did not exist).
        """
        return self.client.delete(key)

    def exists(self, key: str):
        """
        Check whether a key exists in Redis.
        
        Parameters:
            key (str): The Redis key to check.
        
        Returns:
            int: 1 if the key exists, 0 if it does not.
        """
        return self.client.exists(key)


