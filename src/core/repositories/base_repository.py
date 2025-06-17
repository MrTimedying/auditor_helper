from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union
from contextlib import contextmanager
import logging

# Import the Redis-enabled DataService
from ..services.data_service import DataService

class BaseRepository(ABC):
    """Base repository interface for data access with Redis caching support"""
    
    def __init__(self, data_service: DataService = None):
        # Use the Redis-enabled DataService singleton
        self._data_service = data_service or DataService.get_instance()
        self._logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def create(self, **kwargs) -> int:
        """Create new entity, return ID"""
        pass
    
    @abstractmethod
    def get_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """Get entity by ID"""
        pass
    
    @abstractmethod
    def update(self, entity_id: int, **kwargs) -> bool:
        """Update entity, return success status"""
        pass
    
    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """Delete entity, return success status"""
        pass
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        try:
            with self._data_service.transaction():
                yield
        except Exception as e:
            self._logger.error(f"Transaction failed: {e}")
            raise
    
    def _execute_query(self, query: str, params: tuple = (), use_cache: bool = True, cache_ttl: int = None) -> List[Dict[str, Any]]:
        """Execute SELECT query with Redis caching support"""
        try:
            return self._data_service.execute_query(query, params, use_cache=use_cache, cache_ttl=cache_ttl)
        except Exception as e:
            self._logger.error(f"Query failed: {query}, params: {params}, error: {e}")
            raise
    
    def _execute_command(self, command: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE command and return affected rows or last row ID"""
        try:
            return self._data_service.execute_command(command, params)
        except Exception as e:
            self._logger.error(f"Command failed: {command}, params: {params}, error: {e}")
            raise
    
    def clear_cache(self):
        """Clear repository-specific cache"""
        if hasattr(self._data_service, 'cache_manager'):
            self._data_service.cache_manager.invalidate_cache_pattern("query")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if hasattr(self._data_service, 'cache_manager'):
            return self._data_service.cache_manager.get_cache_stats()
        return {"redis_available": False} 