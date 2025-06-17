"""
Memory Cache (L1) Implementation

Ultra-fast in-memory cache with LRU eviction policy.
Designed for frequently accessed data that needs sub-millisecond response times.

Features:
- LRU (Least Recently Used) eviction policy
- Thread-safe operations
- TTL (Time-To-Live) support
- Memory usage monitoring
- Performance statistics
"""

import time
import threading
import sys
from collections import OrderedDict
from typing import Any, Optional, Dict, List
from .base_cache import BaseCache
from .cache_stats import CacheStats


class MemoryCache(BaseCache):
    """
    High-performance in-memory cache with LRU eviction.
    
    This is the L1 cache tier, designed for ultra-fast access to frequently
    used data such as UI state, user preferences, and current session data.
    
    Performance characteristics:
    - Get operations: 0.001-0.01ms
    - Set operations: 0.001-0.01ms
    - Memory efficient with configurable limits
    - Thread-safe for concurrent access
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: int = 300):
        """
        Initialize memory cache.
        
        Args:
            max_size: Maximum number of items to store
            default_ttl: Default time-to-live in seconds
        """
        super().__init__()
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # Thread-safe storage
        self._lock = threading.RLock()
        self._cache = OrderedDict()  # Maintains insertion order for LRU
        self._expiry = {}  # key -> expiration_timestamp
        self._stats = CacheStats()
        
        # Memory tracking
        self._memory_usage = 0
        
    def get(self, key: str) -> Optional[Any]:
        """
        Retrieve a value from the cache.
        
        Args:
            key: The cache key to retrieve
            
        Returns:
            The cached value if found and not expired, None otherwise
        """
        start_time = time.time()
        
        with self._lock:
            # Check if key exists
            if key not in self._cache:
                self._stats.record_miss(time.time() - start_time)
                return None
            
            # Check expiration
            if key in self._expiry and time.time() > self._expiry[key]:
                self._remove_expired_key(key)
                self._stats.record_miss(time.time() - start_time)
                return None
            
            # Move to end (most recently used)
            value = self._cache.pop(key)
            self._cache[key] = value
            
            self._stats.record_hit(time.time() - start_time)
            return value
    
    def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Store a value in the cache.
        
        Args:
            key: The cache key
            value: The value to cache
            ttl: Time-to-live in seconds (None for default)
            
        Returns:
            True if successfully stored, False otherwise
        """
        start_time = time.time()
        
        try:
            with self._lock:
                ttl = ttl or self.default_ttl
                
                # Remove oldest items if at capacity and key is new
                if len(self._cache) >= self.max_size and key not in self._cache:
                    self._evict_lru()
                
                # Calculate memory usage for new item
                item_size = self._estimate_size(value)
                
                # Remove old value if updating existing key
                if key in self._cache:
                    old_size = self._estimate_size(self._cache[key])
                    self._memory_usage -= old_size
                
                # Store value and set expiration
                self._cache[key] = value
                if ttl > 0:
                    self._expiry[key] = time.time() + ttl
                elif key in self._expiry:
                    # Remove expiry if ttl is 0 (no expiration)
                    del self._expiry[key]
                
                # Update memory usage
                self._memory_usage += item_size
                
                # Update statistics
                self._stats.record_set(time.time() - start_time)
                self._stats.update_memory_usage(self._memory_usage)
                self._stats.update_item_count(len(self._cache))
                
                return True
                
        except Exception as e:
            self._stats.record_error()
            return False
    
    def delete(self, key: str) -> bool:
        """
        Remove a key from the cache.
        
        Args:
            key: The cache key to remove
            
        Returns:
            True if key was found and removed, False otherwise
        """
        start_time = time.time()
        
        with self._lock:
            if key in self._cache:
                # Update memory usage
                item_size = self._estimate_size(self._cache[key])
                self._memory_usage -= item_size
                
                # Remove from cache and expiry
                del self._cache[key]
                if key in self._expiry:
                    del self._expiry[key]
                
                # Update statistics
                self._stats.record_delete(time.time() - start_time)
                self._stats.update_memory_usage(self._memory_usage)
                self._stats.update_item_count(len(self._cache))
                
                return True
            
            return False
    
    def clear(self) -> bool:
        """
        Clear all entries from the cache.
        
        Returns:
            True if cache was successfully cleared
        """
        try:
            with self._lock:
                self._cache.clear()
                self._expiry.clear()
                self._memory_usage = 0
                
                # Update statistics
                self._stats.update_memory_usage(0)
                self._stats.update_item_count(0)
                
                return True
        except Exception:
            return False
    
    def exists(self, key: str) -> bool:
        """
        Check if a key exists in the cache (and is not expired).
        
        Args:
            key: The cache key to check
            
        Returns:
            True if key exists and is not expired, False otherwise
        """
        with self._lock:
            if key not in self._cache:
                return False
            
            # Check expiration
            if key in self._expiry and time.time() > self._expiry[key]:
                self._remove_expired_key(key)
                return False
            
            return True
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary containing cache performance statistics
        """
        stats_dict = self._stats.get_stats_dict()
        stats_dict.update({
            'cache_type': 'memory',
            'max_size': self.max_size,
            'current_size': len(self._cache),
            'memory_usage_bytes': self._memory_usage,
            'memory_usage_mb': self._memory_usage / (1024 * 1024),
            'fill_percentage': (len(self._cache) / self.max_size) * 100,
            'expired_keys': len([k for k, exp in self._expiry.items() if time.time() > exp])
        })
        return stats_dict
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries from the cache.
        
        Returns:
            Number of expired entries removed
        """
        removed_count = 0
        current_time = time.time()
        
        with self._lock:
            # Find expired keys
            expired_keys = [
                key for key, expiry_time in self._expiry.items()
                if current_time > expiry_time
            ]
            
            # Remove expired keys
            for key in expired_keys:
                if self.delete(key):
                    removed_count += 1
        
        return removed_count
    
    def get_size(self) -> int:
        """Get the number of items in the cache"""
        return len(self._cache)
    
    def get_memory_usage(self) -> int:
        """Get approximate memory usage in bytes"""
        return self._memory_usage
    
    def get_keys(self) -> List[str]:
        """Get all keys in the cache"""
        with self._lock:
            return list(self._cache.keys())
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate all keys matching a pattern.
        
        Args:
            pattern: Pattern to match keys against (simple string matching)
            
        Returns:
            Number of keys invalidated
        """
        removed_count = 0
        
        with self._lock:
            # Find matching keys
            matching_keys = [key for key in self._cache.keys() if pattern in key]
            
            # Remove matching keys
            for key in matching_keys:
                if self.delete(key):
                    removed_count += 1
        
        return removed_count
    
    def _evict_lru(self):
        """Remove the least recently used item"""
        if self._cache:
            # Remove oldest item (first in OrderedDict)
            oldest_key = next(iter(self._cache))
            self.delete(oldest_key)
    
    def _remove_expired_key(self, key: str):
        """Remove an expired key from cache and expiry tracking"""
        if key in self._cache:
            item_size = self._estimate_size(self._cache[key])
            self._memory_usage -= item_size
            del self._cache[key]
        
        if key in self._expiry:
            del self._expiry[key]
        
        # Update statistics
        self._stats.update_memory_usage(self._memory_usage)
        self._stats.update_item_count(len(self._cache))
    
    def _estimate_size(self, obj: Any) -> int:
        """
        Estimate the memory size of an object in bytes.
        
        Args:
            obj: Object to estimate size for
            
        Returns:
            Estimated size in bytes
        """
        try:
            return sys.getsizeof(obj)
        except Exception:
            # Fallback estimation
            if isinstance(obj, str):
                return len(obj.encode('utf-8'))
            elif isinstance(obj, (int, float)):
                return 8
            elif isinstance(obj, bool):
                return 1
            elif isinstance(obj, (list, tuple)):
                return sum(self._estimate_size(item) for item in obj)
            elif isinstance(obj, dict):
                return sum(self._estimate_size(k) + self._estimate_size(v) for k, v in obj.items())
            else:
                return 64  # Default estimate for unknown objects
    
    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get detailed cache information for debugging.
        
        Returns:
            Dictionary with detailed cache state information
        """
        with self._lock:
            current_time = time.time()
            
            return {
                'total_items': len(self._cache),
                'max_capacity': self.max_size,
                'memory_usage_bytes': self._memory_usage,
                'expired_items': len([k for k, exp in self._expiry.items() if current_time > exp]),
                'items_with_ttl': len(self._expiry),
                'oldest_key': next(iter(self._cache)) if self._cache else None,
                'newest_key': next(reversed(self._cache)) if self._cache else None,
                'average_item_size': self._memory_usage / len(self._cache) if self._cache else 0
            } 