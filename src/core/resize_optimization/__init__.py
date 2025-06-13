"""
Resize Optimization Module

This module contains tools and utilities for optimizing window resize performance
in the Auditor Helper application, specifically targeting the TaskGrid component.

Phase 1: Diagnostic and Foundation
- Performance monitoring and profiling
- Resize event analysis
- Paint event tracking
- Baseline metrics collection
- Easy diagnostic integration

Phase 2: Core State Management and Optimization
- Progressive optimization levels
- Automatic state management
- Invisible performance improvements
- Complete integration system
"""

# Phase 1: Diagnostic Foundation
from .performance_monitor import PerformanceMonitor, get_global_monitor, TimedOperation
from .resize_analyzer import ResizeAnalyzer, ResizeState
from .paint_monitor import PaintMonitor
from .metrics_collector import MetricsCollector
from .diagnostic_integration import TaskGridDiagnostics, create_diagnostics_for_task_grid

# Phase 2: Core State Management and Optimization
from .resize_state_manager import ResizeStateManager, OptimizationLevel, OptimizationState
from .optimization_strategies import TaskGridOptimizationStrategies
from .phase2_integration import Phase2ResizeOptimization, create_phase2_optimization

__all__ = [
    # Phase 1 components
    'PerformanceMonitor',
    'ResizeAnalyzer', 
    'PaintMonitor',
    'MetricsCollector',
    'TaskGridDiagnostics',
    'create_diagnostics_for_task_grid',
    'get_global_monitor',
    'TimedOperation',
    'ResizeState',
    
    # Phase 2 components
    'ResizeStateManager',
    'OptimizationLevel',
    'OptimizationState',
    'TaskGridOptimizationStrategies',
    'Phase2ResizeOptimization',
    'create_phase2_optimization'
] 