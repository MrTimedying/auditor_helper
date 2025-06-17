"""
Cache Statistics and Performance Monitoring

Provides comprehensive statistics tracking for cache performance monitoring,
including hit rates, response times, memory usage, and efficiency metrics.
"""

import time
import threading
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from collections import deque


@dataclass
class CacheTierMetrics:
    """Metrics for a single cache tier"""
    hits: int = 0
    misses: int = 0
    sets: int = 0
    deletes: int = 0
    errors: int = 0
    total_response_time: float = 0.0
    response_times: deque = field(default_factory=lambda: deque(maxlen=1000))
    memory_usage: int = 0
    item_count: int = 0
    created_at: float = field(default_factory=time.time)
    
    @property
    def total_operations(self) -> int:
        """Total number of operations"""
        return self.hits + self.misses + self.sets + self.deletes
    
    @property
    def hit_rate(self) -> float:
        """Cache hit rate as percentage"""
        total_reads = self.hits + self.misses
        return (self.hits / total_reads * 100) if total_reads > 0 else 0.0
    
    @property
    def average_response_time(self) -> float:
        """Average response time in milliseconds"""
        return (self.total_response_time / self.total_operations * 1000) if self.total_operations > 0 else 0.0
    
    @property
    def p95_response_time(self) -> float:
        """95th percentile response time in milliseconds"""
        if not self.response_times:
            return 0.0
        sorted_times = sorted(self.response_times)
        index = int(len(sorted_times) * 0.95)
        return sorted_times[index] * 1000 if index < len(sorted_times) else 0.0
    
    @property
    def efficiency_score(self) -> float:
        """Cache efficiency score (0-100)"""
        if self.total_operations == 0:
            return 0.0
        
        # Weighted score based on hit rate and response time
        hit_rate_score = self.hit_rate
        response_time_score = max(0, 100 - self.average_response_time)  # Lower is better
        
        return (hit_rate_score * 0.7 + response_time_score * 0.3)


class CacheStats:
    """
    Thread-safe cache statistics collector.
    
    Tracks performance metrics for cache operations including:
    - Hit/miss rates
    - Response times
    - Memory usage
    - Error rates
    - Efficiency scores
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._metrics = CacheTierMetrics()
        self._start_time = time.time()
        
    def record_hit(self, response_time: float = 0.0):
        """Record a cache hit"""
        with self._lock:
            self._metrics.hits += 1
            self._metrics.total_response_time += response_time
            if response_time > 0:
                self._metrics.response_times.append(response_time)
    
    def record_miss(self, response_time: float = 0.0):
        """Record a cache miss"""
        with self._lock:
            self._metrics.misses += 1
            self._metrics.total_response_time += response_time
            if response_time > 0:
                self._metrics.response_times.append(response_time)
    
    def record_set(self, response_time: float = 0.0):
        """Record a cache set operation"""
        with self._lock:
            self._metrics.sets += 1
            self._metrics.total_response_time += response_time
            if response_time > 0:
                self._metrics.response_times.append(response_time)
    
    def record_delete(self, response_time: float = 0.0):
        """Record a cache delete operation"""
        with self._lock:
            self._metrics.deletes += 1
            self._metrics.total_response_time += response_time
            if response_time > 0:
                self._metrics.response_times.append(response_time)
    
    def record_error(self):
        """Record a cache error"""
        with self._lock:
            self._metrics.errors += 1
    
    def update_memory_usage(self, memory_bytes: int):
        """Update memory usage statistics"""
        with self._lock:
            self._metrics.memory_usage = memory_bytes
    
    def update_item_count(self, count: int):
        """Update item count statistics"""
        with self._lock:
            self._metrics.item_count = count
    
    def get_metrics(self) -> CacheTierMetrics:
        """Get a copy of current metrics"""
        with self._lock:
            # Return a copy to avoid race conditions
            metrics_copy = CacheTierMetrics()
            metrics_copy.hits = self._metrics.hits
            metrics_copy.misses = self._metrics.misses
            metrics_copy.sets = self._metrics.sets
            metrics_copy.deletes = self._metrics.deletes
            metrics_copy.errors = self._metrics.errors
            metrics_copy.total_response_time = self._metrics.total_response_time
            metrics_copy.response_times = deque(self._metrics.response_times)
            metrics_copy.memory_usage = self._metrics.memory_usage
            metrics_copy.item_count = self._metrics.item_count
            metrics_copy.created_at = self._metrics.created_at
            return metrics_copy
    
    def get_stats_dict(self) -> Dict[str, Any]:
        """Get statistics as a dictionary"""
        metrics = self.get_metrics()
        uptime = time.time() - self._start_time
        
        return {
            'uptime_seconds': uptime,
            'total_operations': metrics.total_operations,
            'hits': metrics.hits,
            'misses': metrics.misses,
            'sets': metrics.sets,
            'deletes': metrics.deletes,
            'errors': metrics.errors,
            'hit_rate_percent': metrics.hit_rate,
            'average_response_time_ms': metrics.average_response_time,
            'p95_response_time_ms': metrics.p95_response_time,
            'memory_usage_bytes': metrics.memory_usage,
            'memory_usage_mb': metrics.memory_usage / (1024 * 1024),
            'item_count': metrics.item_count,
            'efficiency_score': metrics.efficiency_score,
            'operations_per_second': metrics.total_operations / uptime if uptime > 0 else 0
        }
    
    def reset(self):
        """Reset all statistics"""
        with self._lock:
            self._metrics = CacheTierMetrics()
            self._start_time = time.time()
    
    def get_performance_grade(self) -> str:
        """Get a letter grade for cache performance"""
        efficiency = self.get_metrics().efficiency_score
        
        if efficiency >= 90:
            return "A+"
        elif efficiency >= 80:
            return "A"
        elif efficiency >= 70:
            return "B"
        elif efficiency >= 60:
            return "C"
        elif efficiency >= 50:
            return "D"
        else:
            return "F"


class MultiTierCacheStats:
    """
    Statistics collector for multi-tier cache system.
    
    Tracks performance across all cache tiers and provides
    aggregate statistics and insights.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._tier_stats = {
            'l1': CacheStats(),
            'l2': CacheStats(), 
            'l3': CacheStats()
        }
        self._start_time = time.time()
        self._cache_promotions = 0
        self._cache_demotions = 0
    
    def get_tier_stats(self, tier: str) -> CacheStats:
        """Get statistics for a specific tier"""
        return self._tier_stats.get(tier)
    
    def record_promotion(self):
        """Record a cache promotion (data moved to faster tier)"""
        with self._lock:
            self._cache_promotions += 1
    
    def record_demotion(self):
        """Record a cache demotion (data moved to slower tier)"""
        with self._lock:
            self._cache_demotions += 1
    
    def get_aggregate_stats(self) -> Dict[str, Any]:
        """Get aggregate statistics across all tiers"""
        with self._lock:
            aggregate = {
                'uptime_seconds': time.time() - self._start_time,
                'cache_promotions': self._cache_promotions,
                'cache_demotions': self._cache_demotions,
                'tiers': {}
            }
            
            total_operations = 0
            total_hits = 0
            total_memory = 0
            
            for tier_name, stats in self._tier_stats.items():
                tier_dict = stats.get_stats_dict()
                aggregate['tiers'][tier_name] = tier_dict
                
                total_operations += tier_dict['total_operations']
                total_hits += tier_dict['hits']
                total_memory += tier_dict['memory_usage_bytes']
            
            # Calculate aggregate metrics
            aggregate['total_operations'] = total_operations
            aggregate['total_hits'] = total_hits
            aggregate['overall_hit_rate'] = (total_hits / total_operations * 100) if total_operations > 0 else 0
            aggregate['total_memory_usage_mb'] = total_memory / (1024 * 1024)
            
            return aggregate
    
    def get_performance_report(self) -> str:
        """Generate a human-readable performance report"""
        stats = self.get_aggregate_stats()
        
        report = []
        report.append("=== Multi-Tier Cache Performance Report ===")
        report.append(f"Uptime: {stats['uptime_seconds']:.1f} seconds")
        report.append(f"Overall Hit Rate: {stats['overall_hit_rate']:.1f}%")
        report.append(f"Total Memory Usage: {stats['total_memory_usage_mb']:.1f} MB")
        report.append(f"Cache Promotions: {stats['cache_promotions']}")
        report.append(f"Cache Demotions: {stats['cache_demotions']}")
        report.append("")
        
        for tier_name, tier_stats in stats['tiers'].items():
            report.append(f"--- {tier_name.upper()} Cache ---")
            report.append(f"  Hit Rate: {tier_stats['hit_rate_percent']:.1f}%")
            report.append(f"  Operations: {tier_stats['total_operations']}")
            report.append(f"  Avg Response: {tier_stats['average_response_time_ms']:.2f}ms")
            report.append(f"  Memory: {tier_stats['memory_usage_mb']:.1f}MB")
            report.append(f"  Grade: {tier_stats.get('performance_grade', 'N/A')}")
            report.append("")
        
        return "\n".join(report) 