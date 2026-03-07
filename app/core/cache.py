from typing import Any, Optional, Dict
from datetime import datetime, timedelta
import hashlib
import json
import threading
from app.core.logging import logger


class TTLCache:
    """Thread-safe TTL-based cache"""
    
    def __init__(self, default_ttl_seconds: int = 300):
        self.default_ttl = default_ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
    
    def _generate_key(self, key_data: Any) -> str:
        """Generate cache key from data"""
        if isinstance(key_data, str):
            return hashlib.md5(key_data.encode()).hexdigest()
        else:
            serialized = json.dumps(key_data, sort_keys=True)
            return hashlib.md5(serialized.encode()).hexdigest()
    
    def _is_expired(self, entry: Dict[str, Any]) -> bool:
        """Check if cache entry is expired"""
        expiry = entry.get("expiry")
        if expiry is None:
            return True
        return datetime.utcnow() > expiry
    
    def get(self, key: Any) -> Optional[Any]:
        """Get value from cache"""
        cache_key = self._generate_key(key)
        
        with self._lock:
            entry = self._cache.get(cache_key)
            
            if entry is None:
                logger.debug_structured("Cache miss", key=str(key)[:50])
                return None
            
            if self._is_expired(entry):
                del self._cache[cache_key]
                logger.debug_structured("Cache expired", key=str(key)[:50])
                return None
            
            logger.debug_structured("Cache hit", key=str(key)[:50])
            return entry.get("value")
    
    def set(self, key: Any, value: Any, ttl_seconds: Optional[int] = None):
        """Set value in cache with TTL"""
        cache_key = self._generate_key(key)
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expiry = datetime.utcnow() + timedelta(seconds=ttl)
        
        with self._lock:
            self._cache[cache_key] = {
                "value": value,
                "expiry": expiry,
                "created_at": datetime.utcnow()
            }
        
        logger.debug_structured(
            "Cache set",
            key=str(key)[:50],
            ttl_seconds=ttl
        )
    
    def delete(self, key: Any):
        """Delete value from cache"""
        cache_key = self._generate_key(key)
        
        with self._lock:
            if cache_key in self._cache:
                del self._cache[cache_key]
                logger.debug_structured("Cache deleted", key=str(key)[:50])
    
    def clear(self):
        """Clear all cache entries"""
        with self._lock:
            count = len(self._cache)
            self._cache.clear()
            logger.info_structured("Cache cleared", entries_removed=count)
    
    def cleanup_expired(self):
        """Remove expired entries"""
        with self._lock:
            expired_keys = [
                key for key, entry in self._cache.items()
                if self._is_expired(entry)
            ]
            
            for key in expired_keys:
                del self._cache[key]
            
            if expired_keys:
                logger.info_structured(
                    "Cache cleanup",
                    expired_entries=len(expired_keys)
                )
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        with self._lock:
            return {
                "total_entries": len(self._cache),
                "default_ttl_seconds": self.default_ttl
            }


# Global cache instances
query_cache = TTLCache(default_ttl_seconds=300)
embedding_cache = TTLCache(default_ttl_seconds=600)
metrics_cache = TTLCache(default_ttl_seconds=60)
