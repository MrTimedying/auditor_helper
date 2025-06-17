"""
Multi-Tier Cache System for Auditor Helper

This package provides a high-performance, multi-tier caching system that replaces
Redis with a more suitable client-side caching solution.

Cache Hierarchy:
- L1 (Memory): Ultra-fast in-memory cache for frequently accessed data
- L2 (SQLite): Persistent structured cache for medium-frequency data  

Features:
- Intelligent cache routing based on data type and access patterns
- Thread-safe operations
- Performance monitoring and statistics
- Zero external dependencies
"""

from .base_cache import BaseCache
from .cache_stats import CacheStats, CacheTierMetrics
from .memory_cache import MemoryCache
from .sqlite_cache import SQLiteCache

__all__ = [
    'BaseCache',
    'CacheStats',
    'CacheTierMetrics', 
    'MemoryCache',
    'SQLiteCache'
]

__version__ = '1.0.0' 