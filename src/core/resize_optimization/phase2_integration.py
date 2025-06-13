"""
Phase 2 Resize Optimization Integration

This module provides the complete integration layer for Phase 2 resize optimization,
connecting diagnostics, state management, and optimization strategies into a
cohesive system that automatically optimizes TaskGrid performance during resize operations.
"""

import time
from typing import Dict, Any, Optional
from PySide6 import QtCore, QtWidgets

from .diagnostic_integration import TaskGridDiagnostics
from .resize_state_manager import ResizeStateManager, OptimizationLevel
from .optimization_strategies import TaskGridOptimizationStrategies


class Phase2ResizeOptimization(QtCore.QObject):
    """
    Complete Phase 2 resize optimization system.
    
    This class integrates all components to provide automatic, invisible
    performance optimization during resize operations.
    """
    
    # Signals for monitoring and debugging
    optimizationActivated = QtCore.Signal(str, str)  # level, reason
    optimizationDeactivated = QtCore.Signal(str, str)  # level, reason
    performanceImproved = QtCore.Signal(float, float)  # old_frequency, new_frequency
    fallbackTriggered = QtCore.Signal(str)  # reason
    
    def __init__(self, task_grid: QtWidgets.QTableView, debug_mode: bool = False):
        super().__init__()
        self.task_grid = task_grid
        self.debug_mode = debug_mode
        
        # EMERGENCY: Circuit breaker to prevent recursive optimization
        self._optimization_in_progress = False
        self._emergency_shutdown = False
        self._paint_frequency_history = []
        self._max_frequency_threshold = 500.0  # Emergency shutdown at 500Hz
        
        # Component instances
        self.diagnostics: Optional[TaskGridDiagnostics] = None
        self.state_manager: Optional[ResizeStateManager] = None
        self.strategies: Optional[TaskGridOptimizationStrategies] = None
        
        # Performance tracking
        self._total_optimizations = 0
        self._baseline_frequency = 0.0
        self._optimization_sessions = []
        
        # Initialize system
        self._initialize_components()
        self._connect_signals()
        
        if self.debug_mode:
            print("Phase2ResizeOptimization: System initialized with emergency safeguards")
    
    def _initialize_components(self):
        """Initialize all Phase 2 components"""
        try:
            # Initialize diagnostic integration
            self.diagnostics = TaskGridDiagnostics(self.task_grid, debug_mode=self.debug_mode)
            
            # Initialize optimization strategies
            self.strategies = TaskGridOptimizationStrategies(self.task_grid, debug_mode=self.debug_mode)
            
            # Initialize state manager with strategies
            optimization_callbacks = self.strategies.get_optimization_callbacks()
            fallback_callback = self.strategies.get_fallback_callback()
            
            self.state_manager = ResizeStateManager(
                optimization_callbacks=optimization_callbacks,
                fallback_callback=fallback_callback,
                debug_mode=self.debug_mode
            )
            
            if self.debug_mode:
                print("Phase2ResizeOptimization: All components initialized successfully")
                
        except Exception as e:
            print(f"Phase2ResizeOptimization: Component initialization error: {e}")
            self._trigger_system_fallback(f"Initialization failed: {e}")
    
    def _connect_signals(self):
        """Connect signals between components"""
        try:
            if self.diagnostics:
                # Connect diagnostic signals to our handlers
                if hasattr(self.diagnostics, 'resize_analyzer') and self.diagnostics.resize_analyzer:
                    self.diagnostics.resize_analyzer.highFrequencyDetected.connect(self._on_high_frequency_detected)
                
                self.diagnostics.performanceIssueDetected.connect(self._on_performance_issue)
                
                # CRITICAL FIX: Connect to paint frequency signal
                if hasattr(self.diagnostics, 'paint_monitor') and self.diagnostics.paint_monitor:
                    self.diagnostics.paint_monitor.highPaintFrequency.connect(self._on_high_paint_frequency)
            
            if self.state_manager:
                # Connect state manager signals to our signals
                self.state_manager.optimizationActivated.connect(self._on_optimization_activated)
                self.state_manager.optimizationDeactivated.connect(self._on_optimization_deactivated)
                self.state_manager.fallbackTriggered.connect(self._on_fallback_triggered)
            
            if self.debug_mode:
                print("Phase2ResizeOptimization: Signals connected successfully")
                
        except Exception as e:
            print(f"Phase2ResizeOptimization: Signal connection error: {e}")
    
    def _on_high_frequency_detected(self, frequency_hz: float):
        """Handle high frequency resize events from diagnostics"""
        try:
            # EMERGENCY: Check for recursive optimization
            if self._optimization_in_progress or self._emergency_shutdown:
                return
                
            if self.state_manager:
                # Update state manager with frequency data
                metrics = {'source': 'resize_frequency_detection', 'timestamp': time.time()}
                self.state_manager.update_resize_frequency(frequency_hz, metrics)
                
                # Track performance improvements
                if self._baseline_frequency > 0 and frequency_hz < self._baseline_frequency * 0.8:
                    self.performanceImproved.emit(self._baseline_frequency, frequency_hz)
                
                # Update baseline if this is normal operation
                current_level = self.state_manager.get_current_level()
                if current_level == OptimizationLevel.NONE:
                    self._baseline_frequency = frequency_hz
                    
        except Exception as e:
            print(f"Phase2ResizeOptimization: Error handling resize frequency update: {e}")
    
    def _on_high_paint_frequency(self, widget_name: str, frequency_hz: float):
        """Handle high frequency paint events from diagnostics (main optimization trigger)"""
        try:
            # EMERGENCY: Circuit breaker for recursive optimization
            if self._optimization_in_progress:
                if self.debug_mode:
                    print(f"Phase2ResizeOptimization: Blocked recursive optimization call (freq: {frequency_hz:.1f}Hz)")
                return
            
            # EMERGENCY: Shutdown if frequency is too extreme
            if frequency_hz > self._max_frequency_threshold:
                if not self._emergency_shutdown:
                    self._emergency_shutdown = True
                    self._trigger_system_fallback(f"Emergency shutdown: Paint frequency {frequency_hz:.1f}Hz exceeds safe threshold")
                return
            
            # Track frequency history for pattern detection
            self._paint_frequency_history.append(frequency_hz)
            if len(self._paint_frequency_history) > 10:
                self._paint_frequency_history.pop(0)
            
            # Check for escalating frequency pattern (sign of recursive loop)
            if len(self._paint_frequency_history) >= 3:
                recent_freqs = self._paint_frequency_history[-3:]
                if all(f > 200 for f in recent_freqs) and recent_freqs[-1] > recent_freqs[0] * 1.5:
                    self._trigger_system_fallback("Detected escalating paint frequency pattern - possible recursive loop")
                    return
            
            if self.state_manager and widget_name == "TaskGrid":
                # Set circuit breaker
                self._optimization_in_progress = True
                
                try:
                    # Use QTimer.singleShot to defer optimization until after current paint event
                    QtCore.QTimer.singleShot(0, lambda: self._deferred_optimization_update(frequency_hz))
                    
                except Exception as e:
                    print(f"Phase2ResizeOptimization: Error in deferred optimization: {e}")
                finally:
                    # Always clear circuit breaker
                    self._optimization_in_progress = False
                    
        except Exception as e:
            print(f"Phase2ResizeOptimization: Error handling paint frequency update: {e}")
            self._optimization_in_progress = False
    
    def _deferred_optimization_update(self, frequency_hz: float):
        """Deferred optimization update to avoid paint event interference"""
        try:
            if self._emergency_shutdown:
                return
                
            # Update state manager with paint frequency data (this is the main trigger)
            metrics = {'source': 'paint_frequency_detection', 'widget': 'TaskGrid', 'timestamp': time.time()}
            self.state_manager.update_resize_frequency(frequency_hz, metrics)
            
            # Track performance improvements
            if self._baseline_frequency > 0 and frequency_hz < self._baseline_frequency * 0.8:
                self.performanceImproved.emit(self._baseline_frequency, frequency_hz)
            
            # Update baseline if this is normal operation
            current_level = self.state_manager.get_current_level()
            if current_level == OptimizationLevel.NONE:
                self._baseline_frequency = frequency_hz
                
        except Exception as e:
            print(f"Phase2ResizeOptimization: Error in deferred optimization update: {e}")
    
    def _on_resize_frequency_updated(self, frequency_hz: float, metrics: Dict[str, Any]):
        """Handle resize frequency updates from diagnostics (legacy method for compatibility)"""
        self._on_high_frequency_detected(frequency_hz)
    
    def _on_performance_issue(self, issue_type: str, details: Dict[str, Any]):
        """Handle performance issues detected by diagnostics"""
        try:
            if self.debug_mode:
                print(f"Phase2ResizeOptimization: Performance issue detected: {issue_type}")
            
            # The state manager will automatically handle optimization based on frequency
            # This is just for additional monitoring and logging
            
        except Exception as e:
            print(f"Phase2ResizeOptimization: Error handling performance issue: {e}")
    
    def _on_optimization_activated(self, level: OptimizationLevel, reason: str):
        """Handle optimization activation"""
        try:
            self._total_optimizations += 1
            
            # Start tracking this optimization session
            session_data = {
                'level': level.name,
                'reason': reason,
                'start_time': time.time(),  # EMERGENCY FIX: Use time.time() instead of get_current_time()
                'start_frequency': self._baseline_frequency
            }
            self._optimization_sessions.append(session_data)
            
            # Emit signal
            self.optimizationActivated.emit(level.name, reason)
            
            if self.debug_mode:
                print(f"Phase2ResizeOptimization: Optimization activated - {level.name} ({reason})")
                
        except Exception as e:
            print(f"Phase2ResizeOptimization: Error handling optimization activation: {e}")
    
    def _on_optimization_deactivated(self, level: OptimizationLevel, reason: str):
        """Handle optimization deactivation"""
        try:
            # Complete the current optimization session
            if self._optimization_sessions:
                session = self._optimization_sessions[-1]
                session['end_time'] = time.time()  # EMERGENCY FIX: Use time.time() instead of get_current_time()
                session['end_reason'] = reason
                session['duration'] = session['end_time'] - session['start_time']
            
            # Emit signal
            self.optimizationDeactivated.emit(level.name, reason)
            
            if self.debug_mode:
                print(f"Phase2ResizeOptimization: Optimization deactivated - {level.name} ({reason})")
                
        except Exception as e:
            print(f"Phase2ResizeOptimization: Error handling optimization deactivation: {e}")
    
    def _on_fallback_triggered(self, reason: str):
        """Handle fallback scenarios"""
        try:
            self.fallbackTriggered.emit(reason)
            
            if self.debug_mode:
                print(f"Phase2ResizeOptimization: Fallback triggered - {reason}")
                
        except Exception as e:
            print(f"Phase2ResizeOptimization: Error handling fallback: {e}")
    
    def _trigger_system_fallback(self, reason: str):
        """Trigger system-wide fallback to ensure functionality"""
        try:
            # Set emergency shutdown
            self._emergency_shutdown = True
            self._optimization_in_progress = False
            
            # Disable all optimizations
            if self.state_manager:
                self.state_manager.force_deoptimize(f"System fallback: {reason}")
            
            if self.strategies:
                self.strategies.cleanup()
            
            # Ensure TaskGrid is in good state
            self.task_grid.setUpdatesEnabled(True)
            self.task_grid.viewport().update()
            
            print(f"Phase2ResizeOptimization: EMERGENCY SYSTEM FALLBACK - {reason}")
            
        except Exception as e:
            print(f"Phase2ResizeOptimization: Critical error in system fallback: {e}")
    
    def reset_emergency_state(self):
        """Reset emergency state (for recovery after fixing issues)"""
        self._emergency_shutdown = False
        self._optimization_in_progress = False
        self._paint_frequency_history.clear()
        
        if self.debug_mode:
            print("Phase2ResizeOptimization: Emergency state reset")
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status and metrics"""
        try:
            status = {
                'system_active': not self._emergency_shutdown,
                'emergency_shutdown': self._emergency_shutdown,
                'optimization_in_progress': self._optimization_in_progress,
                'total_optimizations': self._total_optimizations,
                'baseline_frequency': self._baseline_frequency,
                'session_count': len(self._optimization_sessions),
                'recent_paint_frequencies': self._paint_frequency_history[-5:] if self._paint_frequency_history else []
            }
            
            if self.state_manager:
                status.update({
                    'current_level': self.state_manager.get_current_level().name,
                    'current_state': self.state_manager.get_current_state(),
                    'performance_summary': self.state_manager.get_performance_summary()
                })
            
            if self.strategies:
                status.update({
                    'optimization_active': self.strategies.is_optimization_active(),
                    'optimization_metrics': self.strategies.get_optimization_metrics()
                })
            
            return status
            
        except Exception as e:
            print(f"Phase2ResizeOptimization: Error getting status: {e}")
            return {'system_active': False, 'error': str(e)}
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        try:
            report = {
                'system_info': {
                    'total_optimizations': self._total_optimizations,
                    'baseline_frequency_hz': self._baseline_frequency,
                    'optimization_sessions': len(self._optimization_sessions),
                    'emergency_shutdown': self._emergency_shutdown
                },
                'current_status': self.get_optimization_status(),
                'optimization_history': self._optimization_sessions[-10:],  # Last 10 sessions
                'paint_frequency_history': self._paint_frequency_history
            }
            
            # Add diagnostic data if available
            if self.diagnostics:
                report['diagnostic_data'] = {
                    'performance_metrics': self.diagnostics.get_performance_metrics(),
                    'resize_analysis': self.diagnostics.get_resize_analysis(),
                }
            
            return report
            
        except Exception as e:
            print(f"Phase2ResizeOptimization: Error generating report: {e}")
            return {'error': str(e)}
    
    def force_optimization_level(self, level: OptimizationLevel, reason: str = "Manual override"):
        """Force a specific optimization level (for testing)"""
        try:
            if self._emergency_shutdown:
                print("Phase2ResizeOptimization: Cannot force optimization - system in emergency shutdown")
                return
                
            if self.state_manager:
                # Simulate high frequency to trigger the desired level
                frequency_map = {
                    OptimizationLevel.LIGHT: 30.0,
                    OptimizationLevel.MEDIUM: 45.0,
                    OptimizationLevel.HEAVY: 65.0,
                    OptimizationLevel.STATIC: 85.0
                }
                
                target_frequency = frequency_map.get(level, 30.0)
                metrics = {'source': 'manual_override', 'timestamp': time.time()}
                self.state_manager.update_resize_frequency(target_frequency, metrics)
                
        except Exception as e:
            print(f"Phase2ResizeOptimization: Error forcing optimization level: {e}")
    
    def cleanup(self):
        """Clean up all components and resources"""
        try:
            # Reset emergency state
            self._emergency_shutdown = False
            self._optimization_in_progress = False
            
            # Clean up components
            if self.strategies:
                self.strategies.cleanup()
            
            if self.state_manager:
                self.state_manager.cleanup()
            
            if self.diagnostics:
                self.diagnostics.cleanup()
            
            if self.debug_mode:
                print("Phase2ResizeOptimization: Cleanup completed")
                
        except Exception as e:
            print(f"Phase2ResizeOptimization: Error during cleanup: {e}")


def create_phase2_optimization(task_grid: QtWidgets.QTableView, debug_mode: bool = False) -> Phase2ResizeOptimization:
    """
    Factory function to create a Phase 2 optimization system.
    
    Args:
        task_grid: The TaskGrid widget to optimize
        debug_mode: Enable debug output
        
    Returns:
        Configured Phase2ResizeOptimization instance
    """
    return Phase2ResizeOptimization(task_grid, debug_mode=debug_mode) 