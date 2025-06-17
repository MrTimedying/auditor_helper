"""
Startup Performance Monitor

Tracks and analyzes application startup performance to measure the effectiveness
of optimization efforts and provide insights for further improvements.

Features:
- Startup time measurement and tracking
- Component-level timing analysis
- Performance regression detection
- Optimization impact reporting
"""

import time
import threading
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class StartupPhase:
    """Represents a phase in the startup process"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    description: str = ""
    critical: bool = False
    
    def finish(self):
        """Mark this phase as finished"""
        if self.end_time is None:
            self.end_time = time.time()
            self.duration = self.end_time - self.start_time
    
    @property
    def is_finished(self) -> bool:
        """Check if this phase is finished"""
        return self.end_time is not None


@dataclass
class StartupSession:
    """Represents a complete startup session"""
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    total_duration: Optional[float] = None
    phases: List[StartupPhase] = field(default_factory=list)
    lazy_imports_used: bool = False
    cache_system_used: bool = False
    optimization_version: str = "1.0.0"
    
    def finish(self):
        """Mark this session as finished"""
        if self.end_time is None:
            self.end_time = time.time()
            self.total_duration = self.end_time - self.start_time
    
    @property
    def is_finished(self) -> bool:
        """Check if this session is finished"""
        return self.end_time is not None


class StartupPerformanceMonitor:
    """
    Monitors and analyzes application startup performance.
    
    Provides detailed timing information for different startup phases
    and tracks the impact of optimization efforts over time.
    """
    
    def __init__(self, data_file: str = "startup_performance.json"):
        self.data_file = Path(data_file)
        self.current_session: Optional[StartupSession] = None
        self.current_phase: Optional[StartupPhase] = None
        self._lock = threading.RLock()
        self.logger = logging.getLogger(__name__)
        
        # Performance thresholds (in seconds)
        self.thresholds = {
            'excellent': 2.0,
            'good': 3.0,
            'acceptable': 5.0,
            'slow': 8.0
        }
        
        # Load historical data
        self.historical_sessions = self._load_historical_data()
    
    def start_session(self, session_id: str = None) -> str:
        """
        Start a new startup performance monitoring session.
        
        Args:
            session_id: Optional custom session ID
            
        Returns:
            The session ID for this monitoring session
        """
        with self._lock:
            if session_id is None:
                session_id = f"startup_{int(time.time())}"
            
            self.current_session = StartupSession(
                session_id=session_id,
                start_time=time.time()
            )
            
            self.logger.info(f"🚀 Started startup performance monitoring session: {session_id}")
            return session_id
    
    def start_phase(self, phase_name: str, description: str = "", critical: bool = False):
        """
        Start timing a specific startup phase.
        
        Args:
            phase_name: Name of the startup phase
            description: Optional description of what this phase does
            critical: Whether this is a critical phase for startup time
        """
        with self._lock:
            if self.current_session is None:
                self.logger.warning("No active session - starting default session")
                self.start_session()
            
            # Finish previous phase if active
            if self.current_phase and not self.current_phase.is_finished:
                self.current_phase.finish()
            
            # Start new phase
            self.current_phase = StartupPhase(
                name=phase_name,
                start_time=time.time(),
                description=description,
                critical=critical
            )
            
            self.current_session.phases.append(self.current_phase)
            self.logger.debug(f"⏱️  Started phase: {phase_name}")
    
    def finish_phase(self, phase_name: str = None):
        """
        Finish timing the current or specified startup phase.
        
        Args:
            phase_name: Optional name to verify we're finishing the right phase
        """
        with self._lock:
            if self.current_phase is None:
                self.logger.warning(f"No active phase to finish: {phase_name}")
                return
            
            if phase_name and self.current_phase.name != phase_name:
                self.logger.warning(f"Phase name mismatch: expected {phase_name}, got {self.current_phase.name}")
            
            self.current_phase.finish()
            duration_ms = self.current_phase.duration * 1000
            
            self.logger.info(f"✅ Finished phase '{self.current_phase.name}': {duration_ms:.1f}ms")
            self.current_phase = None
    
    def finish_session(self):
        """Finish the current startup monitoring session"""
        with self._lock:
            if self.current_session is None:
                self.logger.warning("No active session to finish")
                return
            
            # Finish any active phase
            if self.current_phase and not self.current_phase.is_finished:
                self.current_phase.finish()
            
            # Finish session
            self.current_session.finish()
            
            # Log summary
            self._log_session_summary()
            
            # Save to historical data
            self.historical_sessions.append(self.current_session)
            self._save_historical_data()
            
            self.current_session = None
    
    def set_optimization_flags(self, lazy_imports: bool = False, cache_system: bool = False):
        """
        Set flags indicating which optimizations are active.
        
        Args:
            lazy_imports: Whether lazy imports are being used
            cache_system: Whether the new cache system is being used
        """
        with self._lock:
            if self.current_session:
                self.current_session.lazy_imports_used = lazy_imports
                self.current_session.cache_system_used = cache_system
    
    def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report.
        
        Returns:
            Dictionary containing performance analysis and recommendations
        """
        with self._lock:
            if not self.historical_sessions:
                return {'error': 'No historical data available'}
            
            # Calculate statistics
            recent_sessions = self.historical_sessions[-10:]  # Last 10 sessions
            all_durations = [s.total_duration for s in self.historical_sessions if s.total_duration]
            recent_durations = [s.total_duration for s in recent_sessions if s.total_duration]
            
            # Performance trends
            optimized_sessions = [s for s in recent_sessions if s.lazy_imports_used or s.cache_system_used]
            unoptimized_sessions = [s for s in recent_sessions if not (s.lazy_imports_used or s.cache_system_used)]
            
            report = {
                'summary': {
                    'total_sessions': len(self.historical_sessions),
                    'recent_sessions': len(recent_sessions),
                    'optimized_sessions': len(optimized_sessions),
                    'current_performance_grade': self._get_performance_grade(recent_durations[-1] if recent_durations else 0)
                },
                'timing_analysis': {
                    'all_time_average': sum(all_durations) / len(all_durations) if all_durations else 0,
                    'recent_average': sum(recent_durations) / len(recent_durations) if recent_durations else 0,
                    'best_time': min(all_durations) if all_durations else 0,
                    'worst_time': max(all_durations) if all_durations else 0,
                    'latest_time': recent_durations[-1] if recent_durations else 0
                },
                'optimization_impact': self._analyze_optimization_impact(optimized_sessions, unoptimized_sessions),
                'recommendations': self._generate_recommendations(recent_sessions)
            }
            
            return report
    
    def _log_session_summary(self):
        """Log a summary of the completed session"""
        if not self.current_session or not self.current_session.is_finished:
            return
        
        session = self.current_session
        duration_s = session.total_duration
        grade = self._get_performance_grade(duration_s)
        
        self.logger.info(f"🎯 Startup completed in {duration_s:.2f}s (Grade: {grade})")
        
        # Log critical phases
        critical_phases = [p for p in session.phases if p.critical and p.duration]
        if critical_phases:
            self.logger.info("Critical phases:")
            for phase in critical_phases:
                self.logger.info(f"  • {phase.name}: {phase.duration*1000:.1f}ms")
        
        # Log optimization status
        optimizations = []
        if session.lazy_imports_used:
            optimizations.append("Lazy Imports")
        if session.cache_system_used:
            optimizations.append("Multi-Tier Cache")
        
        if optimizations:
            self.logger.info(f"Active optimizations: {', '.join(optimizations)}")
    
    def _get_performance_grade(self, duration: float) -> str:
        """Get a letter grade for startup performance"""
        if duration <= self.thresholds['excellent']:
            return "A+"
        elif duration <= self.thresholds['good']:
            return "A"
        elif duration <= self.thresholds['acceptable']:
            return "B"
        elif duration <= self.thresholds['slow']:
            return "C"
        else:
            return "D"
    
    def _analyze_optimization_impact(self, optimized: List[StartupSession], unoptimized: List[StartupSession]) -> Dict[str, Any]:
        """Analyze the impact of optimizations"""
        if not optimized or not unoptimized:
            return {'insufficient_data': True}
        
        opt_durations = [s.total_duration for s in optimized if s.total_duration]
        unopt_durations = [s.total_duration for s in unoptimized if s.total_duration]
        
        if not opt_durations or not unopt_durations:
            return {'insufficient_data': True}
        
        opt_avg = sum(opt_durations) / len(opt_durations)
        unopt_avg = sum(unopt_durations) / len(unopt_durations)
        improvement = unopt_avg - opt_avg
        improvement_percent = (improvement / unopt_avg) * 100 if unopt_avg > 0 else 0
        
        return {
            'optimized_average': opt_avg,
            'unoptimized_average': unopt_avg,
            'improvement_seconds': improvement,
            'improvement_percent': improvement_percent,
            'significant_improvement': improvement_percent > 20
        }
    
    def _generate_recommendations(self, sessions: List[StartupSession]) -> List[str]:
        """Generate performance improvement recommendations"""
        recommendations = []
        
        if not sessions:
            return ["Insufficient data for recommendations"]
        
        latest_session = sessions[-1]
        avg_duration = sum(s.total_duration for s in sessions if s.total_duration) / len(sessions)
        
        # Performance-based recommendations
        if avg_duration > self.thresholds['slow']:
            recommendations.append("Startup time is significantly slow - consider implementing lazy imports")
        elif avg_duration > self.thresholds['acceptable']:
            recommendations.append("Startup time could be improved - review critical phases")
        
        # Optimization-specific recommendations
        if not latest_session.lazy_imports_used:
            recommendations.append("Enable lazy imports for heavy scientific libraries")
        
        if not latest_session.cache_system_used:
            recommendations.append("Multi-tier cache system active - performance optimized")
        
        return recommendations if recommendations else ["Performance is optimal - no recommendations"]
    
    def _load_historical_data(self) -> List[StartupSession]:
        """Load historical performance data"""
        try:
            if self.data_file.exists():
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    sessions = []
                    for session_data in data:
                        session = StartupSession(**session_data)
                        # Reconstruct phases
                        session.phases = [StartupPhase(**phase_data) for phase_data in session_data.get('phases', [])]
                        sessions.append(session)
                    return sessions
        except Exception as e:
            self.logger.warning(f"Failed to load historical data: {e}")
        
        return []
    
    def _save_historical_data(self):
        """Save historical performance data"""
        try:
            # Convert sessions to serializable format
            data = []
            for session in self.historical_sessions:
                session_dict = {
                    'session_id': session.session_id,
                    'start_time': session.start_time,
                    'end_time': session.end_time,
                    'total_duration': session.total_duration,
                    'lazy_imports_used': session.lazy_imports_used,
                    'cache_system_used': session.cache_system_used,
                    'optimization_version': session.optimization_version,
                    'phases': [
                        {
                            'name': phase.name,
                            'start_time': phase.start_time,
                            'end_time': phase.end_time,
                            'duration': phase.duration,
                            'description': phase.description,
                            'critical': phase.critical
                        }
                        for phase in session.phases
                    ]
                }
                data.append(session_dict)
            
            # Ensure directory exists
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to save historical data: {e}")


# Global startup monitor instance
_startup_monitor = StartupPerformanceMonitor()


def get_startup_monitor() -> StartupPerformanceMonitor:
    """Get the global startup performance monitor instance"""
    return _startup_monitor


def monitor_startup_phase(phase_name: str, description: str = "", critical: bool = False):
    """
    Decorator to monitor a startup phase.
    
    Args:
        phase_name: Name of the startup phase
        description: Optional description
        critical: Whether this is a critical phase
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            monitor = get_startup_monitor()
            monitor.start_phase(phase_name, description, critical)
            try:
                result = func(*args, **kwargs)
                monitor.finish_phase(phase_name)
                return result
            except Exception as e:
                monitor.finish_phase(phase_name)
                raise
        return wrapper
    return decorator 