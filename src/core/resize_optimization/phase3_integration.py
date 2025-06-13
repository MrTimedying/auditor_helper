"""
Phase 3 Resize Optimization Integration

This module extends Phase 2 with advanced adaptive optimization features including:
- Adaptive threshold management based on real-world performance data
- Context-aware optimization strategies
- Performance analytics and learning
- Enhanced feedback systems
"""

import time
from typing import Dict, Any, Optional, Tuple
from PySide6 import QtCore, QtWidgets, QtGui
from pathlib import Path

from .phase2_integration import Phase2ResizeOptimization
from .adaptive_threshold_manager import (
    AdaptiveThresholdManager, 
    ContextProfile, 
    ThresholdSet,
    HardwareProfile
)
from .resize_state_manager import OptimizationLevel


class Phase3ResizeOptimization(Phase2ResizeOptimization):
    """
    Phase 3 resize optimization system with adaptive intelligence.
    
    Extends Phase 2 with:
    - Adaptive threshold management
    - Context-aware optimization
    - Performance learning and analytics
    - Enhanced user feedback
    """
    
    # Additional signals for Phase 3
    thresholdsAdapted = QtCore.Signal(str, dict)  # context, new_thresholds
    performanceAnalysisUpdated = QtCore.Signal(dict)  # analysis_data
    contextChanged = QtCore.Signal(str)  # new_context_key
    
    def __init__(self, task_grid: QtWidgets.QTableView, debug_mode: bool = False, data_dir: Optional[Path] = None):
        # Initialize Phase 2 first
        super().__init__(task_grid, debug_mode)
        
        # Phase 3 components
        self.adaptive_manager: Optional[AdaptiveThresholdManager] = None
        self.current_context: Optional[ContextProfile] = None
        self.current_thresholds: Optional[ThresholdSet] = None
        
        # Performance tracking for learning
        self._session_start_time: Optional[float] = None
        self._session_metrics: Dict[str, Any] = {}
        self._optimization_effectiveness_scores = []
        
        # Context detection
        self._last_context_update = 0.0
        self._context_update_interval = 5.0  # Update context every 5 seconds
        
        # Initialize Phase 3 components
        self._initialize_phase3_components(data_dir)
        self._connect_phase3_signals()
        
        if self.debug_mode:
            print("Phase3ResizeOptimization: Advanced optimization system initialized")
    
    def _initialize_phase3_components(self, data_dir: Optional[Path]):
        """Initialize Phase 3 specific components"""
        try:
            # Initialize adaptive threshold manager
            self.adaptive_manager = AdaptiveThresholdManager(data_dir)
            
            # Detect initial context
            self._update_current_context()
            
            # Apply adaptive thresholds to state manager
            if self.state_manager and self.current_thresholds:
                self._apply_adaptive_thresholds()
            
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Adaptive manager initialized")
                print(f"Hardware score: {self.adaptive_manager.hardware_profile.performance_score:.1f}")
                print(f"Initial context: {self._get_context_key(self.current_context) if self.current_context else 'None'}")
                
        except Exception as e:
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Phase 3 initialization error: {e}")
    
    def _connect_phase3_signals(self):
        """Connect Phase 3 specific signals"""
        try:
            # Connect to Phase 2 signals for learning
            self.optimizationActivated.connect(self._on_optimization_session_start)
            self.optimizationDeactivated.connect(self._on_optimization_session_end)
            self.performanceImproved.connect(self._on_performance_improvement)
            
            # Set up context update timer
            self._context_timer = QtCore.QTimer()
            self._context_timer.timeout.connect(self._periodic_context_update)
            self._context_timer.start(int(self._context_update_interval * 1000))
            
            if self.debug_mode:
                print("Phase3ResizeOptimization: Phase 3 signals connected")
                
        except Exception as e:
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Phase 3 signal connection error: {e}")
    
    def _update_current_context(self):
        """Update current context profile"""
        try:
            # Get task count from model
            task_count = 0
            if self.task_grid.model():
                task_count = self.task_grid.model().rowCount()
            
            # Get window size
            window_size = (self.task_grid.width(), self.task_grid.height())
            
            # Get monitor information
            screen = QtWidgets.QApplication.primaryScreen()
            monitor_count = len(QtWidgets.QApplication.screens())
            high_dpi = screen.devicePixelRatio() > 1.0 if screen else False
            
            # Check accessibility (basic detection)
            accessibility_enabled = False
            try:
                # Simple check for accessibility features
                app = QtWidgets.QApplication.instance()
                if app and hasattr(app, 'isEffectEnabled'):
                    # This is a basic check - could be enhanced
                    accessibility_enabled = False  # Default for now
            except Exception:
                pass
            
            new_context = ContextProfile(
                task_count=task_count,
                window_size=window_size,
                monitor_count=monitor_count,
                high_dpi=high_dpi,
                accessibility_enabled=accessibility_enabled
            )
            
            # Check if context has changed significantly
            if self._context_changed(new_context):
                self.current_context = new_context
                
                # Get optimal thresholds for this context
                if self.adaptive_manager:
                    self.current_thresholds = self.adaptive_manager.get_optimal_thresholds(new_context)
                    self._apply_adaptive_thresholds()
                    
                    context_key = self._get_context_key(new_context)
                    self.contextChanged.emit(context_key)
                    
                    if self.debug_mode:
                        print(f"Phase3ResizeOptimization: Context updated to {context_key}")
                        print(f"New thresholds: {self.current_thresholds.to_dict()}")
            
        except Exception as e:
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Context update error: {e}")
    
    def _context_changed(self, new_context: ContextProfile) -> bool:
        """Check if context has changed significantly"""
        if not self.current_context:
            return True
        
        # Check for significant changes
        old = self.current_context
        
        # Task count change threshold
        task_change = abs(new_context.task_count - old.task_count) > 5
        
        # Window size change threshold (10% change)
        size_change = (
            abs(new_context.window_size[0] - old.window_size[0]) > old.window_size[0] * 0.1 or
            abs(new_context.window_size[1] - old.window_size[1]) > old.window_size[1] * 0.1
        )
        
        # Other changes
        other_changes = (
            new_context.monitor_count != old.monitor_count or
            new_context.high_dpi != old.high_dpi or
            new_context.accessibility_enabled != old.accessibility_enabled
        )
        
        return task_change or size_change or other_changes
    
    def _get_context_key(self, context: ContextProfile) -> str:
        """Get context key for logging"""
        if not context:
            return "unknown"
        return self.adaptive_manager._get_context_key(context) if self.adaptive_manager else "no_manager"
    
    def _apply_adaptive_thresholds(self):
        """Apply adaptive thresholds to the state manager"""
        if not self.state_manager or not self.current_thresholds:
            return
        
        try:
            # Convert ThresholdSet to the format expected by ResizeStateManager
            from .resize_state_manager import OptimizationLevel
            
            thresholds_dict = {
                OptimizationLevel.LIGHT: self.current_thresholds.light_threshold,
                OptimizationLevel.MEDIUM: self.current_thresholds.medium_threshold,
                OptimizationLevel.HEAVY: self.current_thresholds.heavy_threshold,
                OptimizationLevel.STATIC: self.current_thresholds.static_threshold
            }
            
            # Apply to state manager
            self.state_manager.update_thresholds(thresholds_dict)
            
            # Emit signal with string format for UI
            context_key = self._get_context_key(self.current_context)
            string_thresholds = self.current_thresholds.to_dict()
            self.thresholdsAdapted.emit(context_key, string_thresholds)
            
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Applied adaptive thresholds: {string_thresholds}")
                
        except Exception as e:
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Error applying adaptive thresholds: {e}")
    
    def _periodic_context_update(self):
        """Periodic context update check"""
        current_time = time.time()
        if current_time - self._last_context_update >= self._context_update_interval:
            self._update_current_context()
            self._last_context_update = current_time
    
    def _on_optimization_session_start(self, level: str, reason: str):
        """Handle optimization session start for learning"""
        try:
            self._session_start_time = time.time()
            self._session_metrics = {
                'start_level': level,
                'start_reason': reason,
                'start_frequency': self._get_current_frequency(),
                'context': self.current_context,
                'thresholds_used': self.current_thresholds.to_dict() if self.current_thresholds else {}
            }
            
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Optimization session started - {level} ({reason})")
                
        except Exception as e:
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Error starting optimization session: {e}")
    
    def _on_optimization_session_end(self, level: str, reason: str):
        """Handle optimization session end for learning"""
        try:
            if not self._session_start_time or not self.adaptive_manager:
                return
            
            session_duration = time.time() - self._session_start_time
            end_frequency = self._get_current_frequency()
            
            # Calculate effectiveness score
            effectiveness_score = self._calculate_effectiveness_score(
                self._session_metrics.get('start_frequency', 50.0),
                end_frequency,
                session_duration
            )
            
            # Record session for learning
            if self.current_context and self.current_thresholds:
                performance_metrics = {
                    'session_duration': session_duration,
                    'start_frequency': self._session_metrics.get('start_frequency', 0),
                    'end_frequency': end_frequency,
                    'avg_frequency': (self._session_metrics.get('start_frequency', 0) + end_frequency) / 2,
                    'peak_frequency': max(self._session_metrics.get('start_frequency', 0), end_frequency)
                }
                
                self.adaptive_manager.record_optimization_session(
                    context=self.current_context,
                    thresholds_used=self.current_thresholds.to_dict(),
                    performance_metrics=performance_metrics,
                    effectiveness_score=effectiveness_score
                )
            
            # Track effectiveness
            self._optimization_effectiveness_scores.append(effectiveness_score)
            if len(self._optimization_effectiveness_scores) > 50:
                self._optimization_effectiveness_scores.pop(0)
            
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Optimization session ended - effectiveness: {effectiveness_score:.1f}%")
            
            # Reset session tracking
            self._session_start_time = None
            self._session_metrics = {}
            
        except Exception as e:
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Error ending optimization session: {e}")
    
    def _on_performance_improvement(self, old_frequency: float, new_frequency: float):
        """Handle performance improvement events"""
        try:
            improvement_percent = ((old_frequency - new_frequency) / old_frequency) * 100
            
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Performance improved by {improvement_percent:.1f}% "
                      f"({old_frequency:.1f}Hz → {new_frequency:.1f}Hz)")
            
            # This could be used for additional learning or user feedback
            
        except Exception as e:
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Error handling performance improvement: {e}")
    
    def _get_current_frequency(self) -> float:
        """Get current paint frequency estimate"""
        try:
            if self.diagnostics and hasattr(self.diagnostics, 'paint_monitor'):
                return self.diagnostics.paint_monitor.get_current_frequency()
            return 30.0  # Default estimate
        except Exception:
            return 30.0
    
    def _calculate_effectiveness_score(self, start_freq: float, end_freq: float, duration: float) -> float:
        """Calculate optimization effectiveness score (0-100)"""
        try:
            # Base score from frequency reduction
            if start_freq > 0:
                freq_improvement = max(0, (start_freq - end_freq) / start_freq)
                freq_score = min(freq_improvement * 100, 80)  # Max 80 points
            else:
                freq_score = 50  # Neutral score
            
            # Duration bonus (faster optimization is better)
            if duration < 1.0:
                duration_bonus = 20
            elif duration < 3.0:
                duration_bonus = 10
            elif duration < 5.0:
                duration_bonus = 5
            else:
                duration_bonus = 0
            
            # Final frequency penalty (if still high)
            if end_freq > 60:
                final_penalty = 10
            elif end_freq > 40:
                final_penalty = 5
            else:
                final_penalty = 0
            
            total_score = freq_score + duration_bonus - final_penalty
            return max(0, min(100, total_score))
            
        except Exception as e:
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Error calculating effectiveness: {e}")
            return 50.0  # Neutral score
    
    def get_adaptive_status(self) -> Dict[str, Any]:
        """Get Phase 3 adaptive optimization status"""
        try:
            status = super().get_optimization_status()  # Get Phase 2 status
            
            # Add Phase 3 specific information
            if self.adaptive_manager:
                analysis = self.adaptive_manager.get_performance_analysis()
                status.update({
                    'phase3_enabled': True,
                    'hardware_profile': self.adaptive_manager.hardware_profile.__dict__,
                    'current_context': self.current_context.__dict__ if self.current_context else None,
                    'current_thresholds': self.current_thresholds.to_dict() if self.current_thresholds else None,
                    'learning_sessions': analysis.get('total_sessions', 0),
                    'contexts_learned': analysis.get('contexts_learned', 0),
                    'average_effectiveness': analysis.get('average_effectiveness', 0),
                    'recent_effectiveness': (
                        sum(self._optimization_effectiveness_scores[-10:]) / len(self._optimization_effectiveness_scores[-10:])
                        if self._optimization_effectiveness_scores else 0
                    )
                })
            else:
                status['phase3_enabled'] = False
            
            return status
            
        except Exception as e:
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Error getting adaptive status: {e}")
            return {'error': str(e)}
    
    def get_performance_analytics(self) -> Dict[str, Any]:
        """Get comprehensive performance analytics"""
        try:
            if not self.adaptive_manager:
                return {'error': 'Adaptive manager not available'}
            
            analysis = self.adaptive_manager.get_performance_analysis()
            
            # Add Phase 3 specific analytics
            analysis.update({
                'optimization_effectiveness_history': self._optimization_effectiveness_scores[-20:],
                'current_context_key': self._get_context_key(self.current_context),
                'active_thresholds': self.current_thresholds.to_dict() if self.current_thresholds else None,
                'total_optimizations': self._total_optimizations,
                'baseline_frequency': self._baseline_frequency
            })
            
            # Emit signal for UI updates
            self.performanceAnalysisUpdated.emit(analysis)
            
            return analysis
            
        except Exception as e:
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Error getting performance analytics: {e}")
            return {'error': str(e)}
    
    def force_threshold_adaptation(self, context_key: Optional[str] = None):
        """Force threshold adaptation for testing/debugging"""
        try:
            if not self.adaptive_manager:
                return
            
            if context_key:
                # Find context by key and adapt
                for session in self.adaptive_manager.session_history:
                    if self.adaptive_manager._get_context_key(session.context) == context_key:
                        self.adaptive_manager._update_thresholds_from_session(session)
                        break
            else:
                # Adapt current context
                if self.current_context:
                    # Create a dummy session for adaptation
                    dummy_session = type('DummySession', (), {
                        'context': self.current_context,
                        'effectiveness_score': 50.0  # Neutral score to trigger adaptation
                    })()
                    self.adaptive_manager._update_thresholds_from_session(dummy_session)
            
            # Update thresholds
            if self.current_context:
                self.current_thresholds = self.adaptive_manager.get_optimal_thresholds(self.current_context)
                self._apply_adaptive_thresholds()
            
            if self.debug_mode:
                print("Phase3ResizeOptimization: Forced threshold adaptation")
                
        except Exception as e:
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Error forcing threshold adaptation: {e}")
    
    def export_learning_data(self) -> Dict[str, Any]:
        """Export all learning data for analysis"""
        try:
            if not self.adaptive_manager:
                return {'error': 'Adaptive manager not available'}
            
            return self.adaptive_manager.export_data()
            
        except Exception as e:
            if self.debug_mode:
                print(f"Phase3ResizeOptimization: Error exporting learning data: {e}")
            return {'error': str(e)}
    
    def reset_learning_data(self):
        """Reset all learning data"""
        try:
            if self.adaptive_manager:
                self.adaptive_manager.reset_learning_data()
                
                # Reset local tracking
                self._optimization_effectiveness_scores.clear()
                
                # Update to default thresholds
                if self.current_context:
                    self.current_thresholds = self.adaptive_manager.get_optimal_thresholds(self.current_context)
                    self._apply_adaptive_thresholds()
                
                if self.debug_mode:
                    print("Phase3ResizeOptimization: Learning data reset")
                    
        except Exception as e:
            print(f"Phase3ResizeOptimization: Error resetting learning data: {e}")
    
    def cleanup(self):
        """Clean up Phase 3 resources"""
        try:
            # Stop context timer
            if hasattr(self, '_context_timer'):
                self._context_timer.stop()
            
            # Save adaptive manager data
            if self.adaptive_manager:
                self.adaptive_manager._save_data()
            
            # Call parent cleanup
            super().cleanup()
            
            if self.debug_mode:
                print("Phase3ResizeOptimization: Cleanup completed")
                
        except Exception as e:
            print(f"Phase3ResizeOptimization: Cleanup error: {e}")


def create_phase3_optimization(task_grid: QtWidgets.QTableView, 
                             debug_mode: bool = False,
                             data_dir: Optional[Path] = None) -> Phase3ResizeOptimization:
    """
    Create and configure a Phase 3 resize optimization system.
    
    Args:
        task_grid: The TaskGrid widget to optimize
        debug_mode: Enable debug output
        data_dir: Directory for storing learning data
    
    Returns:
        Configured Phase3ResizeOptimization instance
    """
    try:
        optimization = Phase3ResizeOptimization(task_grid, debug_mode, data_dir)
        
        if debug_mode:
            print("Phase3ResizeOptimization: System created successfully")
            
            # Print initial status
            status = optimization.get_adaptive_status()
            print(f"Hardware score: {status.get('hardware_profile', {}).get('performance_score', 'Unknown')}")
            print(f"Learning sessions: {status.get('learning_sessions', 0)}")
            print(f"Contexts learned: {status.get('contexts_learned', 0)}")
        
        return optimization
        
    except Exception as e:
        print(f"Phase3ResizeOptimization: Creation failed: {e}")
        # Fallback to Phase 2
        from .phase2_integration import create_phase2_optimization
        return create_phase2_optimization(task_grid, debug_mode) 