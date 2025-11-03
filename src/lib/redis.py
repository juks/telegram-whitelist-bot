"""
Redis client class for storing and retrieving data
"""
import redis
import json
from typing import Any, Optional


class Redis:
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0, password: str = None):
        """
        Initialize Redis connection
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            password: Redis password (optional)
        """
        self.host = host
        self.port = port
        self.db = db
        self.password = password
        self.client = None
        self._connect()
    
    def _connect(self):
        """Establish connection to Redis server"""
        try:
            self.client = redis.Redis(
                host=self.host,
                port=self.port,
                db=self.db,
                password=self.password,
                decode_responses=True
            )
            # Test connection
            self.client.ping()
        except redis.ConnectionError as e:
            raise Exception(f"Failed to connect to Redis at {self.host}:{self.port}: {e}")
    
    def get(self, key: str) -> Optional[str]:
        """
        Get value from Redis by key
        
        Args:
            key: Redis key
            
        Returns:
            Value as string or None if key doesn't exist
        """
        try:
            return self.client.get(key)
        except redis.RedisError as e:
            raise Exception(f"Failed to get value from Redis: {e}")
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """
        Set value in Redis by key
        
        Args:
            key: Redis key
            value: Value to store (will be converted to string)
            expire: Optional expiration time in seconds
            
        Returns:
            True if successful
        """
        try:
            # Convert value to string
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            else:
                value = str(value)
            
            if expire:
                return self.client.setex(key, expire, value)
            else:
                return self.client.set(key, value)
        except redis.RedisError as e:
            raise Exception(f"Failed to set value in Redis: {e}")
    
    def delete(self, key: str) -> bool:
        """
        Delete key from Redis
        
        Args:
            key: Redis key to delete
            
        Returns:
            True if key was deleted, False if key didn't exist
        """
        try:
            return bool(self.client.delete(key))
        except redis.RedisError as e:
            raise Exception(f"Failed to delete key from Redis: {e}")
    
    def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis
        
        Args:
            key: Redis key to check
            
        Returns:
            True if key exists, False otherwise
        """
        try:
            return bool(self.client.exists(key))
        except redis.RedisError as e:
            raise Exception(f"Failed to check key existence in Redis: {e}")
    
    def get_dict(self, key: str) -> Optional[dict]:
        """
        Get dictionary value from Redis by key
        
        Args:
            key: Redis key
            
        Returns:
            Dictionary or None if key doesn't exist or value is not valid JSON
        """
        value = self.get(key)
        if value is None:
            return None
        
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
    
    def set_dict(self, key: str, value: dict, expire: Optional[int] = None) -> bool:
        """
        Set dictionary value in Redis by key
        
        Args:
            key: Redis key
            value: Dictionary to store
            expire: Optional expiration time in seconds
            
        Returns:
            True if successful
        """
        return self.set(key, value, expire)
    
    def close(self):
        """Close Redis connection"""
        if self.client:
            self.client.close()
