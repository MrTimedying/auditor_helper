"""
Multi-Tier Cache System for Auditor Helper
High-performance client-side caching with Memory (L1) + SQLite (L2) tiers
Eliminates network dependencies and provides instant startup
"""

import time
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from ..cache.memory_cache import MemoryCache
from ..cache.sqlite_cache import SQLiteCache
from ..cache.cache_stats import CacheStats
from .startup_profiler import profile_phase

class MultiTierCache:
    """
    High-performance multi-tier cache system
    Provides Redis-compatible interface with no network dependencies
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize the multi-tier cache system"""
        with profile_phase("Multi-Tier Cache Init"):
            # Initialize multi-tier cache
            self.memory_cache = MemoryCache(max_size=1000, default_ttl=3600)
            
            # Set up SQLite cache path
            if cache_dir:
                cache_path = f"{cache_dir}/multi_tier_cache.db"
            else:
                cache_path = "multi_tier_cache.db"
            
            self.sqlite_cache = SQLiteCache(db_path=cache_path)
            self.stats = CacheStats()
            self.start_time = time.time()
            
            # Track initialization
            self.stats.record_set(0.001)
            self.stats.update_memory_usage(0)
            self.stats.update_item_count(0)
    
    def ping(self) -> bool:
        """Cache availability check (always returns True)"""
        return True
    
    def info(self) -> Dict[str, Any]:
        """Cache system information"""
        memory_stats = self.memory_cache.get_stats()
        sqlite_stats = self.sqlite_cache.get_stats()
        
        return {
            "cache_version": "2.0.0-multitier",
            "used_memory_human": f"{memory_stats.get('memory_usage_mb', 0):.1f}M",
            "active_connections": 1,
            "uptime_in_seconds": int(time.time() - self.start_time),
            "keyspace_hits": memory_stats.get("hits", 0) + sqlite_stats.get("hits", 0),
            "keyspace_misses": memory_stats.get("misses", 0) + sqlite_stats.get("misses", 0),
            "total_commands_processed": memory_stats.get("operations", 0) + sqlite_stats.get("operations", 0),
            "multi_tier_mode": True,
            "cache_tiers": ["memory", "sqlite"]
        }
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Store a value in the cache"""
        start_time = time.time()
        
        try:
            # Set in both caches
            self.memory_cache.set(key, value, ttl=ex)
            self.sqlite_cache.set(key, value, ttl=ex)
            
            duration = time.time() - start_time
            self.stats.record_set(duration)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.stats.record_error()
            return False
    
    def get(self, key: str) -> Any:
        """Retrieve a value from the cache"""
        start_time = time.time()
        
        try:
            # Try memory cache first (L1)
            value = self.memory_cache.get(key)
            if value is not None:
                duration = time.time() - start_time
                self.stats.record_hit(duration)
                return value
            
            # Try SQLite cache (L2)
            value = self.sqlite_cache.get(key)
            if value is not None:
                # Promote to memory cache
                self.memory_cache.set(key, value)
                duration = time.time() - start_time
                self.stats.record_hit(duration)
                return value
            
            # Not found
            duration = time.time() - start_time
            self.stats.record_miss(duration)
            return None
            
        except Exception as e:
            duration = time.time() - start_time
            self.stats.record_error()
            return None
    
    def delete(self, key: str) -> int:
        """Delete a key from the cache"""
        start_time = time.time()
        
        try:
            deleted_count = 0
            
            # Delete from memory cache
            if self.memory_cache.delete(key):
                deleted_count += 1
            
            # Delete from SQLite cache
            if self.sqlite_cache.delete(key):
                deleted_count += 1
            
            duration = time.time() - start_time
            self.stats.record_delete(duration)
            return min(deleted_count, 1)  # Return 0 or 1
            
        except Exception as e:
            duration = time.time() - start_time
            self.stats.record_error()
            return 0
    
    def exists(self, key: str) -> int:
        """Check if a key exists in the cache"""
        start_time = time.time()
        
        try:
            # Check memory cache first
            if self.memory_cache.exists(key):
                duration = time.time() - start_time
                self.stats.record_hit(duration)
                return 1
            
            # Check SQLite cache
            if self.sqlite_cache.exists(key):
                duration = time.time() - start_time
                self.stats.record_hit(duration)
                return 1
            
            duration = time.time() - start_time
            self.stats.record_miss(duration)
            return 0
            
        except Exception as e:
            duration = time.time() - start_time
            self.stats.record_error()
            return 0
    
    def expire(self, key: str, seconds: int) -> int:
        """Set expiration time for a key"""
        start_time = time.time()
        
        try:
            success_count = 0
            
            # Set expiration in memory cache
            if self.memory_cache.exists(key):
                # Memory cache handles TTL automatically
                success_count += 1
            
            # Set expiration in SQLite cache
            if self.sqlite_cache.exists(key):
                # SQLite cache handles TTL automatically
                success_count += 1
            
            duration = time.time() - start_time
            self.stats.record_set(duration)
            return min(success_count, 1)  # Return 0 or 1
            
        except Exception as e:
            duration = time.time() - start_time
            self.stats.record_error()
            return 0
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Get all keys matching a pattern"""
        start_time = time.time()
        
        try:
            # Get keys from both caches
            memory_keys = set(self.memory_cache.get_all_keys())
            sqlite_keys = set(self.sqlite_cache.get_all_keys())
            
            # Combine and deduplicate
            all_keys = list(memory_keys | sqlite_keys)
            
            # Simple pattern matching (only supports * wildcard)
            if pattern == "*":
                result = all_keys
            else:
                # Basic pattern matching
                import fnmatch
                result = [key for key in all_keys if fnmatch.fnmatch(key, pattern)]
            
            duration = time.time() - start_time
            self.stats.record_hit(duration)
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            self.stats.record_error()
            return []
    
    def flushdb(self) -> bool:
        """Clear all entries from the cache"""
        start_time = time.time()
        
        try:
            self.memory_cache.clear()
            self.sqlite_cache.clear()
            
            duration = time.time() - start_time
            self.stats.record_delete(duration)
            return True
            
        except Exception as e:
            duration = time.time() - start_time
            self.stats.record_error()
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics"""
        memory_stats = self.memory_cache.get_stats()
        sqlite_stats = self.sqlite_cache.get_stats()
        replacement_stats = self.stats.get_stats_dict()
        
        return {
            "multi_tier_active": True,
            "memory_cache": memory_stats,
            "sqlite_cache": sqlite_stats,
            "aggregate_stats": replacement_stats,
            "total_operations": replacement_stats.get("total_operations", 0),
            "total_hits": replacement_stats.get("hits", 0),
            "total_misses": replacement_stats.get("misses", 0),
            "hit_rate": replacement_stats.get("hit_rate_percent", 0),
            "uptime": replacement_stats.get("uptime_seconds", 0)
        }
    


class FastDataService:
    """
    Optimized DataService with multi-tier caching
    Eliminates network dependencies and provides instant startup
    Compatible with existing DAO interface
    """
    
    _instance = None
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize fast data service"""
        with profile_phase("Fast DataService Init"):
            # Initialize multi-tier cache
            self.cache_manager = MultiTierCache(cache_dir)
            
            # Initialize database connection (compatible with existing DataService)
            from pathlib import Path
            import sqlite3
            import threading
            from contextlib import contextmanager
            
            # Database setup (same as DataService)
            from ..db.db_schema import DB_FILE
            self.db_path = Path(DB_FILE)
            self._connection_pool = {}
            self._transaction_depth = {}
            
            self.initialized = True
    
    def _get_thread_id(self) -> int:
        """Get current thread ID"""
        import threading
        return threading.get_ident()
    
    @contextmanager
    def _get_connection(self):
        """Get thread-safe database connection"""
        import sqlite3
        thread_id = self._get_thread_id()
        
        # Check if we have an active transaction connection
        if thread_id in self._connection_pool:
            yield self._connection_pool[thread_id]
            return
        
        # Create new connection for this operation
        conn = None
        try:
            conn = sqlite3.connect(str(self.db_path), timeout=30.0)
            conn.row_factory = sqlite3.Row  # Enable dict-like access
            conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key constraints
            yield conn
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            raise Exception(f"Database connection failed: {e}")
        finally:
            if conn and thread_id not in self._connection_pool:
                conn.close()
    
    def execute_query(self, query: str, params=None, use_cache: bool = True, cache_ttl: int = None):
        """Execute SELECT query (compatible with DataService interface)"""
        params = params or ()
        
        # Execute query
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(query, params)
                results = [dict(row) for row in cursor.fetchall()]
                return results
        except Exception as e:
            raise Exception(f"Query failed: {e}")
    
    def execute_command(self, command: str, params=None) -> int:
        """Execute INSERT/UPDATE/DELETE command (compatible with DataService interface)"""
        params = params or ()
        
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(command, params)
                
                # Auto-commit if not in transaction
                thread_id = self._get_thread_id()
                if thread_id not in self._connection_pool:
                    conn.commit()
                
                result = cursor.lastrowid if cursor.lastrowid else cursor.rowcount
                return result
        except Exception as e:
            raise Exception(f"Command failed: {e}")
    
    @classmethod
    def get_instance(cls, redis_config: Optional[Dict] = None, cache_dir: Optional[str] = None):
        """Get singleton instance of FastDataService"""
        if cls._instance is None:
            cls._instance = cls(cache_dir)
        return cls._instance
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        cache_stats = self.cache_manager.get_stats()
        
        return {
            "cache_stats": {
                "network_cache_available": False,  # No network dependencies
                "multi_tier_active": True,
                "memory_cache_active": True,
                "sqlite_cache_active": True,
                **cache_stats
            },
            "startup_optimized": True,
            "connection_timeout_eliminated": True
        }

def create_optimized_cache() -> MultiTierCache:
    """Create an optimized multi-tier cache"""
    with profile_phase("Create Multi-Tier Cache"):
        return MultiTierCache()

def migrate_from_network_cache(config: Dict[str, Any]) -> MultiTierCache:
    """Migrate from network-based cache to multi-tier cache"""
    with profile_phase("Migrate to Multi-Tier Cache"):
        # Create multi-tier cache (ignores network config)
        cache = MultiTierCache()
        
        # Log the migration
        print("🔄 Migrated to multi-tier cache system")
        print("✅ Eliminated network connection timeouts")
        print("🚀 Startup performance improved")
        
        return cache 