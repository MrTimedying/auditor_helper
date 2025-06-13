"""
Performance Monitor for Resize Operations

This module provides comprehensive performance monitoring capabilities
for tracking resize operation performance in the TaskGrid component.
"""

import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable
from PySide6 import QtCore


@dataclass
class PerformanceMetric:
    """Individual performance metric data point"""
    timestamp: float
    operation: str
    duration_ms: float
    additional_data: Dict = field(default_factory=dict)


@dataclass
class PerformanceSession:
    """Performance monitoring session data"""
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    metrics: List[PerformanceMetric] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)


class PerformanceMonitor(QtCore.QObject):
    """
    Comprehensive performance monitoring for resize operations.
    
    Tracks timing, frequency, and performance characteristics of various
    operations during window resize events.
    """
    
    # Signals for real-time monitoring
    metricRecorded = QtCore.Signal(PerformanceMetric)
    sessionStarted = QtCore.Signal(str)  # session_id
    sessionEnded = QtCore.Signal(str, dict)  # session_id, summary
    
    def __init__(self, max_sessions: int = 100, max_metrics_per_session: int = 1000):
        super().__init__()
        self.max_sessions = max_sessions
        self.max_metrics_per_session = max_metrics_per_session
        
        # Thread-safe storage
        self._lock = threading.RLock()
        self._sessions: Dict[str, PerformanceSession] = {}
        self._active_session: Optional[str] = None
        self._session_counter = 0
        
        # Performance tracking
        self._operation_timers: Dict[str, float] = {}
        self._operation_counts: defaultdict = defaultdict(int)
        self._recent_metrics: deque = deque(maxlen=1000)
        
        # Configuration
        self._enabled = True
        self._debug_mode = False
        
    def set_enabled(self, enabled: bool):
        """Enable or disable performance monitoring"""
        with self._lock:
            self._enabled = enabled
            if self._debug_mode:
                print(f"PerformanceMonitor: {'Enabled' if enabled else 'Disabled'}")
    
    def set_debug_mode(self, debug: bool):
        """Enable or disable debug output"""
        with self._lock:
            self._debug_mode = debug
    
    def start_session(self, session_type: str = "resize", metadata: Dict = None) -> str:
        """
        Start a new performance monitoring session.
        
        Args:
            session_type: Type of session (e.g., 'resize', 'paint', 'layout')
            metadata: Additional metadata for the session
            
        Returns:
            Session ID string
        """
        if not self._enabled:
            return ""
            
        with self._lock:
            self._session_counter += 1
            session_id = f"{session_type}_{self._session_counter}_{int(time.time())}"
            
            session = PerformanceSession(
                session_id=session_id,
                start_time=time.time(),
                metadata=metadata or {}
            )
            
            self._sessions[session_id] = session
            self._active_session = session_id
            
            # Cleanup old sessions if needed
            if len(self._sessions) > self.max_sessions:
                oldest_session = min(self._sessions.keys(), 
                                   key=lambda k: self._sessions[k].start_time)
                del self._sessions[oldest_session]
            
            if self._debug_mode:
                print(f"PerformanceMonitor: Started session {session_id}")
                
            self.sessionStarted.emit(session_id)
            return session_id
    
    def end_session(self, session_id: Optional[str] = None) -> Dict:
        """
        End a performance monitoring session and return summary.
        
        Args:
            session_id: Session to end (defaults to active session)
            
        Returns:
            Dictionary containing session summary
        """
        if not self._enabled:
            return {}
            
        with self._lock:
            if session_id is None:
                session_id = self._active_session
                
            if not session_id or session_id not in self._sessions:
                return {}
                
            session = self._sessions[session_id]
            session.end_time = time.time()
            
            # Generate summary
            summary = self._generate_session_summary(session)
            
            if session_id == self._active_session:
                self._active_session = None
                
            if self._debug_mode:
                print(f"PerformanceMonitor: Ended session {session_id}")
                print(f"Summary: {summary}")
                
            self.sessionEnded.emit(session_id, summary)
            return summary
    
    def start_operation(self, operation_name: str) -> str:
        """
        Start timing an operation.
        
        Args:
            operation_name: Name of the operation to time
            
        Returns:
            Operation timer ID
        """
        if not self._enabled:
            return ""
            
        timer_id = f"{operation_name}_{time.time()}"
        with self._lock:
            self._operation_timers[timer_id] = time.time()
            
        return timer_id
    
    def end_operation(self, timer_id: str, additional_data: Dict = None) -> Optional[PerformanceMetric]:
        """
        End timing an operation and record the metric.
        
        Args:
            timer_id: Timer ID returned from start_operation
            additional_data: Additional data to store with the metric
            
        Returns:
            PerformanceMetric object if successful, None otherwise
        """
        if not self._enabled or not timer_id:
            return None
            
        with self._lock:
            if timer_id not in self._operation_timers:
                return None
                
            start_time = self._operation_timers.pop(timer_id)
            end_time = time.time()
            duration_ms = (end_time - start_time) * 1000
            
            # Extract operation name from timer_id
            operation_name = timer_id.rsplit('_', 1)[0]
            
            metric = PerformanceMetric(
                timestamp=end_time,
                operation=operation_name,
                duration_ms=duration_ms,
                additional_data=additional_data or {}
            )
            
            # Record metric
            self._record_metric(metric)
            return metric
    
    def record_instant_metric(self, operation: str, value: float, additional_data: Dict = None):
        """
        Record an instant metric (not duration-based).
        
        Args:
            operation: Operation name
            value: Metric value
            additional_data: Additional data to store
        """
        if not self._enabled:
            return
            
        metric = PerformanceMetric(
            timestamp=time.time(),
            operation=operation,
            duration_ms=value,
            additional_data=additional_data or {}
        )
        
        self._record_metric(metric)
    
    def _record_metric(self, metric: PerformanceMetric):
        """Internal method to record a metric"""
        with self._lock:
            # Add to active session if exists
            if self._active_session and self._active_session in self._sessions:
                session = self._sessions[self._active_session]
                session.metrics.append(metric)
                
                # Limit metrics per session
                if len(session.metrics) > self.max_metrics_per_session:
                    session.metrics = session.metrics[-self.max_metrics_per_session:]
            
            # Add to recent metrics for quick access
            self._recent_metrics.append(metric)
            
            # Update operation counts
            self._operation_counts[metric.operation] += 1
            
            if self._debug_mode:
                print(f"PerformanceMonitor: {metric.operation} took {metric.duration_ms:.2f}ms")
                
            self.metricRecorded.emit(metric)
    
    def _generate_session_summary(self, session: PerformanceSession) -> Dict:
        """Generate a summary of session performance"""
        if not session.metrics:
            return {
                'session_id': session.session_id,
                'duration_seconds': session.end_time - session.start_time if session.end_time else 0,
                'total_operations': 0,
                'operations': {}
            }
        
        # Group metrics by operation
        operations = defaultdict(list)
        for metric in session.metrics:
            operations[metric.operation].append(metric.duration_ms)
        
        # Calculate statistics for each operation
        operation_stats = {}
        for op_name, durations in operations.items():
            operation_stats[op_name] = {
                'count': len(durations),
                'total_ms': sum(durations),
                'avg_ms': sum(durations) / len(durations),
                'min_ms': min(durations),
                'max_ms': max(durations),
                'frequency_hz': len(durations) / (session.end_time - session.start_time) if session.end_time else 0
            }
        
        return {
            'session_id': session.session_id,
            'duration_seconds': session.end_time - session.start_time if session.end_time else 0,
            'total_operations': len(session.metrics),
            'operations': operation_stats,
            'metadata': session.metadata
        }
    
    def get_session_summary(self, session_id: str) -> Dict:
        """Get summary for a specific session"""
        with self._lock:
            if session_id not in self._sessions:
                return {}
            return self._generate_session_summary(self._sessions[session_id])
    
    def get_recent_metrics(self, operation: str = None, limit: int = 100) -> List[PerformanceMetric]:
        """Get recent metrics, optionally filtered by operation"""
        with self._lock:
            metrics = list(self._recent_metrics)
            
            if operation:
                metrics = [m for m in metrics if m.operation == operation]
                
            return metrics[-limit:]
    
    def get_operation_statistics(self) -> Dict:
        """Get overall operation statistics"""
        with self._lock:
            return dict(self._operation_counts)
    
    def clear_data(self):
        """Clear all stored performance data"""
        with self._lock:
            self._sessions.clear()
            self._active_session = None
            self._operation_timers.clear()
            self._operation_counts.clear()
            self._recent_metrics.clear()
            self._session_counter = 0
            
        if self._debug_mode:
            print("PerformanceMonitor: All data cleared")


# Convenience context manager for timing operations
class TimedOperation:
    """Context manager for timing operations with PerformanceMonitor"""
    
    def __init__(self, monitor: PerformanceMonitor, operation_name: str, additional_data: Dict = None):
        self.monitor = monitor
        self.operation_name = operation_name
        self.additional_data = additional_data
        self.timer_id = None
    
    def __enter__(self):
        self.timer_id = self.monitor.start_operation(self.operation_name)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.timer_id:
            self.monitor.end_operation(self.timer_id, self.additional_data)


# Global performance monitor instance
_global_monitor = None

def get_global_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor

def set_global_monitor(monitor: PerformanceMonitor):
    """Set the global performance monitor instance"""
    global _global_monitor
    _global_monitor = monitor 