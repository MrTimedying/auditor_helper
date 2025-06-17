"""
Clean Data Service Layer with Multi-Tier Caching
No Redis dependencies - uses Memory + SQLite cache tiers only
"""

import sqlite3
import threading
import json
import hashlib
from pathlib import Path
from contextlib import contextmanager
from typing import Dict, Any, List, Optional, Union, Tuple

from ..db.db_schema import DB_FILE
from ..optimization.multi_tier_cache import MultiTierCache


class DataServiceError(Exception):
    """Exception raised by DataService operations"""
    pass


class CacheManager:
    """Multi-tier cache manager with Memory + SQLite caching (no Redis)"""
    
    def __init__(self):
        self._logger = None  # Simplified - no logging for now
        self.cache = MultiTierCache()
    
    def get_cached_query(self, query: str, params: tuple = (), ttl: int = None) -> Optional[List[Dict[str, Any]]]:
        """Get cached query result"""
        cache_key = self._generate_cache_key("query", query, params)
        cached_data = self.cache.get(cache_key)
        
        if cached_data:
            try:
                return json.loads(cached_data) if isinstance(cached_data, str) else cached_data
            except:
                return None
        return None
    
    def set_cached_query(self, query: str, params: tuple, result: List[Dict[str, Any]], ttl: int = None):
        """Cache query result"""
        cache_key = self._generate_cache_key("query", query, params)
        try:
            cached_data = json.dumps(result, default=str)
            self.cache.set(cache_key, cached_data, ex=ttl)
        except:
            pass  # Ignore cache errors
    
    def _generate_cache_key(self, prefix: str, query: str, params: tuple) -> str:
        """Generate consistent cache key"""
        key_data = f"{query}:{params}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"auditor_helper:{prefix}:{key_hash}"
    
    def clear_all_cache(self):
        """Clear all cache"""
        self.cache.flushdb()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache.get_stats()


class DataService:
    """
    Clean data access service with multi-tier caching
    No Redis dependencies - uses Memory + SQLite cache only
    """
    
    _instance: Optional['DataService'] = None
    _lock = threading.Lock()
    
    def __new__(cls, db_path: str = None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self, db_path: str = None):
        if hasattr(self, '_initialized'):
            return
            
        # Use the configured database path if none provided
        if db_path is None:
            db_path = DB_FILE
        self.db_path = Path(db_path)
        self._connection_pool = {}  # Thread-local connections
        self._transaction_depth = {}  # Track transaction depth per thread
        
        # Initialize cache manager (no Redis)
        self.cache_manager = CacheManager()
        
        self._initialized = True
        
        # Ensure database exists and is properly initialized
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database file exists and is accessible"""
        try:
            if not self.db_path.exists():
                # Import and run migrations to create database
                from ..db.db_schema import run_all_migrations
                run_all_migrations()
            
            # Test connection
            with self._get_connection() as conn:
                conn.execute("SELECT 1").fetchone()
                
        except Exception as e:
            raise DataServiceError(f"Database initialization failed: {e}")
    
    def _get_thread_id(self) -> int:
        """Get current thread ID"""
        return threading.get_ident()
    
    @contextmanager
    def _get_connection(self):
        """Get thread-safe database connection"""
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
            raise DataServiceError(f"Database connection failed: {e}")
        finally:
            if conn and thread_id not in self._connection_pool:
                conn.close()
    
    def execute_query(self, query: str, params: Union[Tuple, Dict] = None, 
                     use_cache: bool = True, cache_ttl: int = None) -> List[Dict[str, Any]]:
        """
        Execute SELECT query with multi-tier caching support.
        """
        params = params or ()
        
        # Convert dict params to tuple for caching
        if isinstance(params, dict):
            cache_params = tuple(sorted(params.items()))
        else:
            cache_params = tuple(params)
        
        # Try cache first
        if use_cache:
            cached_result = self.cache_manager.get_cached_query(query, cache_params, cache_ttl)
            if cached_result is not None:
                return cached_result
        
        # Execute query
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(query, params)
                results = [dict(row) for row in cursor.fetchall()]
                
                # Cache the result
                if use_cache:
                    self.cache_manager.set_cached_query(query, cache_params, results, cache_ttl)
                
                return results
                
        except sqlite3.Error as e:
            raise DataServiceError(f"Query failed: {e}")
    
    def execute_command(self, command: str, params: Union[Tuple, Dict] = None) -> int:
        """
        Execute INSERT/UPDATE/DELETE command with automatic cache invalidation.
        """
        params = params or ()
        
        try:
            with self._get_connection() as conn:
                cursor = conn.execute(command, params)
                
                # Auto-commit if not in transaction
                thread_id = self._get_thread_id()
                if thread_id not in self._connection_pool:
                    conn.commit()
                
                result = cursor.lastrowid if cursor.lastrowid else cursor.rowcount
                
                # Clear cache on data changes
                self.cache_manager.clear_all_cache()
                
                return result
                
        except sqlite3.Error as e:
            raise DataServiceError(f"Command failed: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        cache_stats = self.cache_manager.get_cache_stats()
        
        return {
            "cache_stats": {
                "multi_tier_active": True,
                "memory_cache_active": True,
                "sqlite_cache_active": True,
                **cache_stats
            },
            "database_path": str(self.db_path),
            "connection_pool_size": len(self._connection_pool)
        }
    
    def invalidate_analytics_cache(self):
        """Invalidate analytics-related cache entries"""
        # For now, clear all cache - could be more specific in the future
        self.cache_manager.clear_all_cache()
    
    @classmethod
    def get_instance(cls, db_path: str = None, redis_config: Any = None) -> 'DataService':
        """Get singleton instance (redis_config ignored for compatibility)"""
        return cls(db_path)
    
    @classmethod
    def reset_instance(cls):
        """Reset singleton instance"""
        cls._instance = None
