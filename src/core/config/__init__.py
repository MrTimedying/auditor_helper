"""
Configuration package for the Auditor Helper application.
Provides configuration management for Redis and other services.
"""

from .redis_config import get_redis_config, is_redis_required

__all__ = ['get_redis_config', 'is_redis_required'] 