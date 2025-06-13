"""
Adaptive Threshold Manager for Phase 3 Resize Optimization

This module implements intelligent threshold adaptation based on real-world performance data,
hardware capabilities, and optimization effectiveness analysis.
"""

import time
import json
import platform
import psutil
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import statistics
import logging

logger = logging.getLogger(__name__)

@dataclass
class HardwareProfile:
    """Hardware capability profile for threshold optimization"""
    cpu_cores: int
    cpu_frequency: float  # GHz
    memory_gb: float
    platform: str
    gpu_info: str
    performance_score: float  # Calculated performance score 0-100

@dataclass
class ContextProfile:
    """Context-specific performance profile"""
    task_count: int
    window_size: Tuple[int, int]
    monitor_count: int
    high_dpi: bool
    accessibility_enabled: bool

@dataclass
class OptimizationSession:
    """Record of an optimization session for learning"""
    timestamp: float
    context: ContextProfile
    thresholds_used: Dict[str, float]
    performance_metrics: Dict[str, float]
    effectiveness_score: float  # 0-100, how effective the optimization was
    user_satisfaction: Optional[float] = None  # If available from feedback

@dataclass
class ThresholdSet:
    """Set of optimization thresholds"""
    light_threshold: float = 25.0
    medium_threshold: float = 40.0
    heavy_threshold: float = 60.0
    static_threshold: float = 80.0
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'light': self.light_threshold,
            'medium': self.medium_threshold,
            'heavy': self.heavy_threshold,
            'static': self.static_threshold
        }

class AdaptiveThresholdManager:
    """
    Manages adaptive threshold optimization based on real-world performance data.
    
    This class analyzes optimization effectiveness and automatically adjusts
    thresholds to improve performance for specific hardware and usage contexts.
    """
    
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path("data/optimization")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Core data
        self.hardware_profile = self._detect_hardware_profile()
        self.session_history: List[OptimizationSession] = []
        self.context_thresholds: Dict[str, ThresholdSet] = {}
        
        # Default thresholds (Phase 2 proven values)
        self.default_thresholds = ThresholdSet()
        
        # Learning parameters
        self.min_sessions_for_adaptation = 5
        self.effectiveness_weight = 0.7
        self.performance_weight = 0.3
        self.adaptation_rate = 0.1  # How quickly to adapt (0.0-1.0)
        
        # Load existing data
        self._load_historical_data()
        
        logger.info(f"AdaptiveThresholdManager initialized for {self.hardware_profile.platform}")
        logger.info(f"Hardware score: {self.hardware_profile.performance_score:.1f}")
    
    def _detect_hardware_profile(self) -> HardwareProfile:
        """Detect and profile hardware capabilities"""
        try:
            # CPU information
            cpu_cores = psutil.cpu_count(logical=True)
            cpu_freq = psutil.cpu_freq()
            cpu_frequency = cpu_freq.max / 1000.0 if cpu_freq else 2.0  # Default 2GHz
            
            # Memory information
            memory = psutil.virtual_memory()
            memory_gb = memory.total / (1024**3)
            
            # Platform information
            platform_name = platform.system()
            
            # GPU information (basic detection)
            gpu_info = "Unknown"
            try:
                import subprocess
                if platform_name == "Windows":
                    result = subprocess.run(["wmic", "path", "win32_VideoController", "get", "name"], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        gpu_info = lines[1].strip() if len(lines) > 1 else "Unknown"
            except Exception:
                pass
            
            # Calculate performance score (0-100)
            performance_score = self._calculate_performance_score(
                cpu_cores, cpu_frequency, memory_gb, platform_name
            )
            
            return HardwareProfile(
                cpu_cores=cpu_cores,
                cpu_frequency=cpu_frequency,
                memory_gb=memory_gb,
                platform=platform_name,
                gpu_info=gpu_info,
                performance_score=performance_score
            )
            
        except Exception as e:
            logger.warning(f"Hardware detection failed: {e}")
            # Return conservative defaults
            return HardwareProfile(
                cpu_cores=4,
                cpu_frequency=2.0,
                memory_gb=8.0,
                platform=platform.system(),
                gpu_info="Unknown",
                performance_score=50.0
            )
    
    def _calculate_performance_score(self, cores: int, freq: float, memory: float, platform: str) -> float:
        """Calculate a performance score from hardware specs"""
        # Base score from CPU
        cpu_score = min(cores * 5, 40) + min(freq * 10, 30)  # Max 70 points
        
        # Memory score
        memory_score = min(memory * 2, 20)  # Max 20 points
        
        # Platform bonus/penalty
        platform_bonus = 10 if platform == "Windows" else 5  # Max 10 points
        
        total_score = cpu_score + memory_score + platform_bonus
        return min(total_score, 100.0)
    
    def _load_historical_data(self):
        """Load historical optimization data"""
        try:
            # Load session history
            history_file = self.data_dir / "session_history.json"
            if history_file.exists():
                with open(history_file, 'r') as f:
                    data = json.load(f)
                    self.session_history = [
                        OptimizationSession(**session) for session in data
                    ]
                logger.info(f"Loaded {len(self.session_history)} historical sessions")
            
            # Load context thresholds
            thresholds_file = self.data_dir / "context_thresholds.json"
            if thresholds_file.exists():
                with open(thresholds_file, 'r') as f:
                    data = json.load(f)
                    self.context_thresholds = {
                        context: ThresholdSet(**thresholds)
                        for context, thresholds in data.items()
                    }
                logger.info(f"Loaded thresholds for {len(self.context_thresholds)} contexts")
                
        except Exception as e:
            logger.warning(f"Failed to load historical data: {e}")
    
    def _save_data(self):
        """Save current data to disk"""
        try:
            # Save session history
            history_file = self.data_dir / "session_history.json"
            with open(history_file, 'w') as f:
                json.dump([asdict(session) for session in self.session_history], f, indent=2)
            
            # Save context thresholds
            thresholds_file = self.data_dir / "context_thresholds.json"
            with open(thresholds_file, 'w') as f:
                json.dump({
                    context: asdict(thresholds)
                    for context, thresholds in self.context_thresholds.items()
                }, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to save data: {e}")
    
    def _get_context_key(self, context: ContextProfile) -> str:
        """Generate a key for context-specific thresholds"""
        # Group similar contexts together
        task_group = "small" if context.task_count < 10 else "medium" if context.task_count < 50 else "large"
        size_group = "small" if context.window_size[0] < 800 else "medium" if context.window_size[0] < 1400 else "large"
        
        return f"{task_group}_{size_group}_{context.monitor_count}mon_{context.high_dpi}_{context.accessibility_enabled}"
    
    def get_optimal_thresholds(self, context: ContextProfile) -> ThresholdSet:
        """
        Get optimal thresholds for the given context.
        
        Returns adapted thresholds if enough data is available,
        otherwise returns hardware-adjusted defaults.
        """
        context_key = self._get_context_key(context)
        
        # Check if we have learned thresholds for this context
        if context_key in self.context_thresholds:
            learned_thresholds = self.context_thresholds[context_key]
            logger.debug(f"Using learned thresholds for context {context_key}")
            return learned_thresholds
        
        # Use hardware-adjusted defaults with context awareness
        adjusted_thresholds = self._get_hardware_adjusted_thresholds(context)
        logger.debug(f"Using hardware-adjusted defaults for context {context_key}")
        return adjusted_thresholds
    
    def _get_hardware_adjusted_thresholds(self, context: Optional[ContextProfile] = None) -> ThresholdSet:
        """Get thresholds adjusted for current hardware performance and context"""
        base = self.default_thresholds
        score = self.hardware_profile.performance_score
        
        # Base hardware adjustment
        if score >= 80:  # High-end hardware
            hw_multiplier = 1.3
        elif score >= 60:  # Mid-range hardware
            hw_multiplier = 1.1
        elif score >= 40:  # Low-mid range hardware
            hw_multiplier = 0.9
        else:  # Low-end hardware
            hw_multiplier = 0.7
        
        # Context-specific adjustments
        context_multiplier = 1.0
        if context:
            # Adjust based on task count
            if context.task_count > 100:
                context_multiplier *= 0.9  # Optimize earlier for many tasks
            elif context.task_count < 20:
                context_multiplier *= 1.1  # Can handle higher frequencies with few tasks
            
            # Adjust based on window size
            window_area = context.window_size[0] * context.window_size[1]
            if window_area > 1500000:  # Large window (>1500x1000)
                context_multiplier *= 0.95
            elif window_area < 600000:  # Small window (<800x750)
                context_multiplier *= 1.05
            
            # Adjust for multi-monitor
            if context.monitor_count > 1:
                context_multiplier *= 0.95
            
            # Adjust for high DPI
            if context.high_dpi:
                context_multiplier *= 0.9
            
            # Adjust for accessibility
            if context.accessibility_enabled:
                context_multiplier *= 0.85
        
        final_multiplier = hw_multiplier * context_multiplier
        
        return ThresholdSet(
            light_threshold=base.light_threshold * final_multiplier,
            medium_threshold=base.medium_threshold * final_multiplier,
            heavy_threshold=base.heavy_threshold * final_multiplier,
            static_threshold=base.static_threshold * final_multiplier
        )
    
    def record_optimization_session(self, 
                                  context: ContextProfile,
                                  thresholds_used: Dict[str, float],
                                  performance_metrics: Dict[str, float],
                                  effectiveness_score: float):
        """Record an optimization session for learning"""
        session = OptimizationSession(
            timestamp=time.time(),
            context=context,
            thresholds_used=thresholds_used,
            performance_metrics=performance_metrics,
            effectiveness_score=effectiveness_score
        )
        
        self.session_history.append(session)
        
        # Limit history size
        if len(self.session_history) > 1000:
            self.session_history = self.session_history[-800:]  # Keep most recent 800
        
        # Try to learn from this session
        self._update_thresholds_from_session(session)
        
        # Save data periodically
        if len(self.session_history) % 10 == 0:
            self._save_data()
        
        logger.debug(f"Recorded optimization session with effectiveness {effectiveness_score:.1f}")
    
    def _update_thresholds_from_session(self, session: OptimizationSession):
        """Update thresholds based on session effectiveness"""
        context_key = self._get_context_key(session.context)
        
        # Get sessions for this context
        context_sessions = [
            s for s in self.session_history 
            if self._get_context_key(s.context) == context_key
        ]
        
        if len(context_sessions) < self.min_sessions_for_adaptation:
            return  # Not enough data yet
        
        # Analyze recent sessions (last 20 or all if fewer)
        recent_sessions = context_sessions[-20:]
        
        # Calculate average effectiveness
        avg_effectiveness = statistics.mean(s.effectiveness_score for s in recent_sessions)
        
        # If effectiveness is low, try to adapt thresholds
        if avg_effectiveness < 70:  # Below 70% effectiveness
            current_thresholds = self.context_thresholds.get(
                context_key, self._get_hardware_adjusted_thresholds()
            )
            
            # Analyze what might improve effectiveness
            new_thresholds = self._optimize_thresholds(recent_sessions, current_thresholds)
            
            if new_thresholds:
                self.context_thresholds[context_key] = new_thresholds
                logger.info(f"Adapted thresholds for context {context_key} "
                           f"(effectiveness: {avg_effectiveness:.1f}%)")
    
    def _optimize_thresholds(self, sessions: List[OptimizationSession], 
                           current: ThresholdSet) -> Optional[ThresholdSet]:
        """Optimize thresholds based on session analysis"""
        try:
            # Analyze performance patterns
            high_freq_sessions = [s for s in sessions if s.performance_metrics.get('peak_frequency', 0) > 60]
            low_effectiveness = [s for s in sessions if s.effectiveness_score < 60]
            
            # If we have high frequency events with low effectiveness,
            # we might need to optimize earlier (lower thresholds)
            if len(high_freq_sessions) > len(sessions) * 0.3:  # 30% of sessions
                # Reduce thresholds to optimize earlier
                factor = 0.9
                return ThresholdSet(
                    light_threshold=current.light_threshold * factor,
                    medium_threshold=current.medium_threshold * factor,
                    heavy_threshold=current.heavy_threshold * factor,
                    static_threshold=current.static_threshold * factor
                )
            
            # If we have many low effectiveness sessions but low frequencies,
            # we might be optimizing too aggressively (increase thresholds)
            elif len(low_effectiveness) > len(sessions) * 0.4:  # 40% of sessions
                avg_freq = statistics.mean(s.performance_metrics.get('avg_frequency', 30) for s in sessions)
                if avg_freq < 40:  # Low average frequency
                    factor = 1.1
                    return ThresholdSet(
                        light_threshold=current.light_threshold * factor,
                        medium_threshold=current.medium_threshold * factor,
                        heavy_threshold=current.heavy_threshold * factor,
                        static_threshold=current.static_threshold * factor
                    )
            
            return None  # No optimization needed
            
        except Exception as e:
            logger.warning(f"Threshold optimization failed: {e}")
            return None
    
    def get_performance_analysis(self) -> Dict[str, Any]:
        """Get comprehensive performance analysis"""
        # Always return analysis structure, even with no data
        analysis = {
            "total_sessions": len(self.session_history),
            "recent_sessions": 0,
            "hardware_profile": asdict(self.hardware_profile),
            "average_effectiveness": 0,
            "contexts_learned": len(self.context_thresholds),
            "performance_trends": {"status": "No data available"},
            "threshold_recommendations": {"recommendations": [], "overall_status": "No data"}
        }
        
        if self.session_history:
            recent_sessions = self.session_history[-50:]  # Last 50 sessions
            
            analysis.update({
                "recent_sessions": len(recent_sessions),
                "average_effectiveness": statistics.mean(s.effectiveness_score for s in recent_sessions),
                "performance_trends": self._analyze_performance_trends(recent_sessions),
                "threshold_recommendations": self._get_threshold_recommendations()
            })
        
        return analysis
    
    def _analyze_performance_trends(self, sessions: List[OptimizationSession]) -> Dict[str, Any]:
        """Analyze performance trends from recent sessions"""
        if len(sessions) < 5:
            return {"status": "Insufficient data"}
        
        # Group by time periods
        now = time.time()
        recent = [s for s in sessions if now - s.timestamp < 7 * 24 * 3600]  # Last week
        older = [s for s in sessions if now - s.timestamp >= 7 * 24 * 3600]
        
        trends = {}
        
        if recent and older:
            recent_avg = statistics.mean(s.effectiveness_score for s in recent)
            older_avg = statistics.mean(s.effectiveness_score for s in older)
            trends["effectiveness_trend"] = recent_avg - older_avg
        
        # Frequency trends
        recent_freq = [s.performance_metrics.get('avg_frequency', 0) for s in recent]
        if recent_freq:
            trends["average_frequency"] = statistics.mean(recent_freq)
            trends["peak_frequency"] = max(s.performance_metrics.get('peak_frequency', 0) for s in recent)
        
        return trends
    
    def _get_threshold_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for threshold adjustments"""
        recommendations = []
        
        # Analyze each context
        for context_key, thresholds in self.context_thresholds.items():
            context_sessions = [
                s for s in self.session_history[-100:]  # Last 100 sessions
                if self._get_context_key(s.context) == context_key
            ]
            
            if len(context_sessions) >= 5:
                avg_effectiveness = statistics.mean(s.effectiveness_score for s in context_sessions)
                
                if avg_effectiveness < 60:
                    recommendations.append({
                        "context": context_key,
                        "issue": "Low effectiveness",
                        "current_effectiveness": avg_effectiveness,
                        "recommendation": "Consider adjusting thresholds"
                    })
        
        return {
            "recommendations": recommendations,
            "overall_status": "Good" if not recommendations else "Needs attention"
        }
    
    def reset_learning_data(self):
        """Reset all learning data (for testing or fresh start)"""
        self.session_history.clear()
        self.context_thresholds.clear()
        
        # Remove data files
        try:
            (self.data_dir / "session_history.json").unlink(missing_ok=True)
            (self.data_dir / "context_thresholds.json").unlink(missing_ok=True)
        except Exception as e:
            logger.warning(f"Failed to remove data files: {e}")
        
        logger.info("Learning data reset")
    
    def export_data(self) -> Dict[str, Any]:
        """Export all data for analysis or backup"""
        return {
            "hardware_profile": asdict(self.hardware_profile),
            "session_history": [asdict(s) for s in self.session_history],
            "context_thresholds": {
                k: asdict(v) for k, v in self.context_thresholds.items()
            },
            "performance_analysis": self.get_performance_analysis()
        } 