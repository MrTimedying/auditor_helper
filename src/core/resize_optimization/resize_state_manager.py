"""
Resize State Manager

This module implements the core state management system for progressive resize optimization.
It monitors resize activity and automatically adjusts optimization levels to maintain smooth
performance while preserving full functionality and visual quality.
"""

import time
from enum import Enum
from typing import Optional, Dict, Any, Callable
from dataclasses import dataclass
from PySide6 import QtCore, QtWidgets


class OptimizationLevel(Enum):
    """Progressive optimization levels"""
    NONE = 0        # No optimization - full quality (default)
    LIGHT = 1       # Light optimization - reduce update frequency
    MEDIUM = 2      # Medium optimization - simplified rendering
    HEAVY = 3       # Heavy optimization - minimal rendering
    STATIC = 4      # Static mode - snapshot scaling (extreme cases)


@dataclass
class OptimizationState:
    """Current optimization state information"""
    level: OptimizationLevel
    reason: str
    start_time: float
    metrics: Dict[str, Any]
    fallback_available: bool = True


class ResizeStateManager(QtCore.QObject):
    """
    Manages progressive resize optimization levels based on activity intensity.
    
    This class monitors resize frequency and automatically adjusts optimization
    levels to maintain smooth performance while ensuring zero functional impact.
    """
    
    # Signals for state changes
    optimizationLevelChanged = QtCore.Signal(OptimizationLevel, OptimizationLevel)  # old, new
    optimizationActivated = QtCore.Signal(OptimizationLevel, str)  # level, reason
    optimizationDeactivated = QtCore.Signal(OptimizationLevel, str)  # level, reason
    fallbackTriggered = QtCore.Signal(str)  # reason
    
    def __init__(self, target_widget: QtWidgets.QWidget = None, debug_mode: bool = False, 
                 optimization_callbacks: Dict = None, fallback_callback: Callable = None):
        super().__init__()
        self.target_widget = target_widget
        self.debug_mode = debug_mode
        
        # Current state
        self._current_level = OptimizationLevel.NONE
        self._current_state: Optional[OptimizationState] = None
        self._last_resize_time = 0.0
        self._resize_frequency = 0.0
        
        # Optimization thresholds (based on diagnostic data showing 30-86Hz)
        self._thresholds = {
            OptimizationLevel.LIGHT: 25.0,   # Light optimization at 25Hz
            OptimizationLevel.MEDIUM: 40.0,  # Medium optimization at 40Hz  
            OptimizationLevel.HEAVY: 60.0,   # Heavy optimization at 60Hz
            OptimizationLevel.STATIC: 80.0,  # Static mode at 80Hz
        }
        
        # Timing configuration
        self._settle_delay_ms = 200      # Time to wait before deactivating optimization
        self._hysteresis_factor = 0.8   # Prevent oscillation (deactivate at 80% of activation threshold)
        
        # State management
        self._optimization_callbacks: Dict[OptimizationLevel, Callable] = {}
        self._deoptimization_callbacks: Dict[OptimizationLevel, Callable] = {}
        self._fallback_callback: Optional[Callable] = None
        
        # Timers
        self._settle_timer = QtCore.QTimer()
        self._settle_timer.setSingleShot(True)
        self._settle_timer.timeout.connect(self._check_deoptimization)
        
        # Performance monitoring
        self._performance_history = []
        self._max_history_size = 100
        
        # EMERGENCY FIX: Initialize callbacks if provided
        if optimization_callbacks:
            for level, (activate_cb, deactivate_cb) in optimization_callbacks.items():
                self.register_optimization_callback(level, activate_cb, deactivate_cb)
        
        if fallback_callback:
            self.register_fallback_callback(fallback_callback)
        
        if self.debug_mode:
            widget_name = target_widget.objectName() if target_widget else "Unknown"
            print(f"ResizeStateManager: Initialized for {widget_name}")
    
    def register_optimization_callback(self, level: OptimizationLevel, 
                                     activate_callback: Callable, 
                                     deactivate_callback: Callable):
        """Register callbacks for optimization level activation/deactivation"""
        self._optimization_callbacks[level] = activate_callback
        self._deoptimization_callbacks[level] = deactivate_callback
        
        if self.debug_mode:
            print(f"ResizeStateManager: Registered callbacks for {level.name}")
    
    def register_fallback_callback(self, callback: Callable):
        """Register fallback callback for when optimization fails"""
        self._fallback_callback = callback
    
    def update_resize_frequency(self, frequency_hz: float, additional_metrics: Dict[str, Any] = None):
        """Update resize frequency and adjust optimization level accordingly"""
        self._resize_frequency = frequency_hz
        self._last_resize_time = time.time()
        
        # Add to performance history
        metrics = {
            'frequency_hz': frequency_hz,
            'timestamp': self._last_resize_time,
            **(additional_metrics or {})
        }
        self._performance_history.append(metrics)
        
        # Trim history
        if len(self._performance_history) > self._max_history_size:
            self._performance_history.pop(0)
        
        # Determine target optimization level
        target_level = self._calculate_target_level(frequency_hz)
        
        # Apply optimization if needed
        if target_level != self._current_level:
            self._transition_to_level(target_level, f"Frequency: {frequency_hz:.1f}Hz")
        
        # Reset settle timer
        self._settle_timer.stop()
        self._settle_timer.start(self._settle_delay_ms)
    
    def _calculate_target_level(self, frequency_hz: float) -> OptimizationLevel:
        """Calculate the appropriate optimization level based on frequency"""
        # Apply hysteresis to prevent oscillation
        effective_frequency = frequency_hz
        if self._current_level != OptimizationLevel.NONE:
            # When already optimized, require lower frequency to deoptimize
            effective_frequency = frequency_hz / self._hysteresis_factor
        
        # Determine level based on thresholds
        if effective_frequency >= self._thresholds[OptimizationLevel.STATIC]:
            return OptimizationLevel.STATIC
        elif effective_frequency >= self._thresholds[OptimizationLevel.HEAVY]:
            return OptimizationLevel.HEAVY
        elif effective_frequency >= self._thresholds[OptimizationLevel.MEDIUM]:
            return OptimizationLevel.MEDIUM
        elif effective_frequency >= self._thresholds[OptimizationLevel.LIGHT]:
            return OptimizationLevel.LIGHT
        else:
            return OptimizationLevel.NONE
    
    def _transition_to_level(self, target_level: OptimizationLevel, reason: str):
        """Transition to a new optimization level"""
        old_level = self._current_level
        
        try:
            # Deactivate current level if needed
            if old_level != OptimizationLevel.NONE:
                self._deactivate_level(old_level)
            
            # Activate new level if needed
            if target_level != OptimizationLevel.NONE:
                self._activate_level(target_level, reason)
            
            # Update state
            self._current_level = target_level
            self._current_state = OptimizationState(
                level=target_level,
                reason=reason,
                start_time=time.time(),
                metrics={'frequency_hz': self._resize_frequency}
            ) if target_level != OptimizationLevel.NONE else None
            
            # Emit signals
            self.optimizationLevelChanged.emit(old_level, target_level)
            
            if self.debug_mode:
                print(f"ResizeStateManager: {old_level.name} → {target_level.name} ({reason})")
                
        except Exception as e:
            # Fallback on any error
            self._trigger_fallback(f"Transition error: {e}")
    
    def _activate_level(self, level: OptimizationLevel, reason: str):
        """Activate a specific optimization level"""
        try:
            if level in self._optimization_callbacks:
                self._optimization_callbacks[level]()
                self.optimizationActivated.emit(level, reason)
                
                if self.debug_mode:
                    print(f"ResizeStateManager: Activated {level.name} optimization")
            else:
                if self.debug_mode:
                    print(f"ResizeStateManager: No callback registered for {level.name}")
                    
        except Exception as e:
            self._trigger_fallback(f"Activation error for {level.name}: {e}")
    
    def _deactivate_level(self, level: OptimizationLevel):
        """Deactivate a specific optimization level"""
        try:
            if level in self._deoptimization_callbacks:
                self._deoptimization_callbacks[level]()
                self.optimizationDeactivated.emit(level, "Deactivated")
                
                if self.debug_mode:
                    print(f"ResizeStateManager: Deactivated {level.name} optimization")
                    
        except Exception as e:
            self._trigger_fallback(f"Deactivation error for {level.name}: {e}")
    
    def _check_deoptimization(self):
        """Check if we should deoptimize based on inactivity"""
        current_time = time.time()
        time_since_resize = current_time - self._last_resize_time
        
        # If no recent resize activity, deoptimize
        if time_since_resize >= (self._settle_delay_ms / 1000.0):
            if self._current_level != OptimizationLevel.NONE:
                self._transition_to_level(OptimizationLevel.NONE, "Resize activity settled")
    
    def _trigger_fallback(self, reason: str):
        """Trigger fallback to ensure functionality is preserved"""
        try:
            # Force return to no optimization
            self._current_level = OptimizationLevel.NONE
            self._current_state = None
            
            # Call fallback callback if registered
            if self._fallback_callback:
                # EMERGENCY FIX: Pass reason parameter to fallback callback
                self._fallback_callback(reason)
            
            self.fallbackTriggered.emit(reason)
            
            if self.debug_mode:
                print(f"ResizeStateManager: Fallback triggered - {reason}")
                
        except Exception as e:
            print(f"ResizeStateManager: Critical error in fallback: {e}")
    
    def force_deoptimize(self, reason: str = "Manual override"):
        """Force immediate deoptimization to ensure full functionality"""
        if self._current_level != OptimizationLevel.NONE:
            self._transition_to_level(OptimizationLevel.NONE, reason)
    
    def get_current_level(self) -> OptimizationLevel:
        """Get the current optimization level"""
        return self._current_level
    
    def get_current_state(self) -> Optional[OptimizationState]:
        """Get detailed current state information"""
        return self._current_state
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for analysis"""
        if not self._performance_history:
            return {}
        
        frequencies = [h['frequency_hz'] for h in self._performance_history]
        return {
            'current_level': self._current_level.name,
            'current_frequency': self._resize_frequency,
            'avg_frequency': sum(frequencies) / len(frequencies),
            'max_frequency': max(frequencies),
            'min_frequency': min(frequencies),
            'history_size': len(self._performance_history),
            'thresholds': {level.name: threshold for level, threshold in self._thresholds.items()}
        }
    
    def update_thresholds(self, new_thresholds: Dict[OptimizationLevel, float]):
        """Update optimization thresholds based on performance data"""
        self._thresholds.update(new_thresholds)
        
        if self.debug_mode:
            print(f"ResizeStateManager: Updated thresholds: {new_thresholds}")
    
    def cleanup(self):
        """Clean up resources"""
        self._settle_timer.stop()
        self.force_deoptimize("Cleanup")
        
        if self.debug_mode:
            print("ResizeStateManager: Cleanup completed") 