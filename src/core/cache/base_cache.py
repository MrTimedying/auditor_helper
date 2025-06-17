"""
Base Cache Interface

Defines the abstract interface that all cache implementations must follow.
This ensures consistency across different cache tiers and enables easy testing
and swapping of cache implementations.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional, Dict, List
import time
import threading


class BaseCache(ABC):
    """
    Abstract base class for all cache implementations.
    
    Provides the standard interface that all cache tiers (Memory, SQLite, File)
    must implement to ensure consistency and interoperability.
    """
    
    def __init__(self):
        self._stats_lock = threading.RLock()
        self._created_at = time.time()
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Args:
            key: The cache key to retrieve
            
        Returns:
            The cached value if found and not expired, None otherwise
        """
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Store a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds (None for no expiration)
            
        Returns:
            True if successfully stored, False otherwise
        """
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Remove a key from the cache.
        
        Args:
            key: The cache key to remove
            
        Returns:
            True if key was found and removed, False otherwise
        """
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """
        Clear all entries from the cache.
        
        Returns:
            True if cache was successfully cleared, False otherwise
        """
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache (and is not expired).
        
        Args:
            key: The cache key to check
            
        Returns:
            True if key exists and is not expired, False otherwise
        """
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache performance statistics
        """
        pass
    
    @abstractmethod
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from the cache.
        
        Returns:
            Number of expired entries removed
        """
        pass
    
    def get_size(self) -> int:
        """
        Get the number of items in the cache.
        Default implementation returns 0 - subclasses should override.
        
        Returns:
            Number of items currently in the cache
        """
        return 0
    
    def get_memory_usage(self) -> int:
        """
        Get approximate memory usage in bytes.
        Default implementation returns 0 - subclasses should override.
        
        Returns:
            Approximate memory usage in bytes
        """
        return 0
    
    def get_uptime(self) -> float:
        """
        Get cache uptime in seconds.
        
        Returns:
            Number of seconds since cache was created
        """
        return time.time() - self._created_at
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.
        Default implementation does nothing - subclasses can override.
        
        Args:
            pattern: Pattern to match keys against
            
        Returns:
            Number of keys invalidated
        """
        return 0
    
    def get_keys(self) -> List[str]:
        """
        Get all keys in the cache.
        Default implementation returns empty list - subclasses should override.
        
        Returns:
            List of all cache keys
        """
        return []
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup if needed"""
        pass 