"""
Diagnostic Integration for TaskGrid

This module provides easy integration of diagnostic tools into the existing TaskGrid
for Phase 1 data collection without disrupting current functionality.
"""

from typing import Optional
from PySide6 import QtCore, QtWidgets

from .performance_monitor import PerformanceMonitor, get_global_monitor, TimedOperation
from .resize_analyzer import ResizeAnalyzer, ResizeState
from .paint_monitor import PaintMonitor
from .metrics_collector import MetricsCollector


class TaskGridDiagnostics(QtCore.QObject):
    """
    Diagnostic wrapper for TaskGrid that adds performance monitoring capabilities.
    
    This class can be easily integrated into existing TaskGrid without modifying
    the core TaskGrid code significantly.
    """
    
    # Signals for diagnostic events
    diagnosticsStarted = QtCore.Signal()
    diagnosticsStopped = QtCore.Signal()
    baselineCompleted = QtCore.Signal(dict)
    performanceIssueDetected = QtCore.Signal(str, dict)
    
    def __init__(self, task_grid: QtWidgets.QTableView, debug_mode: bool = False):
        super().__init__()
        self.task_grid = task_grid
        self.debug_mode = debug_mode
        
        # Initialize monitoring components
        self.performance_monitor = get_global_monitor()
        self.performance_monitor.set_debug_mode(debug_mode)
        
        self.resize_analyzer = ResizeAnalyzer()
        self.resize_analyzer.set_debug_mode(debug_mode)
        
        self.paint_monitor = PaintMonitor()
        self.paint_monitor.set_debug_mode(debug_mode)
        
        self.metrics_collector = MetricsCollector()
        self.metrics_collector.set_debug_mode(debug_mode)
        self.metrics_collector.set_monitoring_components(
            self.performance_monitor,
            self.resize_analyzer,
            self.paint_monitor
        )
        
        # State tracking
        self._diagnostics_active = False
        self._baseline_session_id: Optional[str] = None
        self._current_test_session_id: Optional[str] = None
        
        # Connect signals
        self._connect_signals()
        
        # Install monitoring
        self._install_monitoring()
        
        if self.debug_mode:
            print("TaskGridDiagnostics: Initialized for TaskGrid monitoring")
    
    def _connect_signals(self):
        """Connect signals from monitoring components"""
        # Resize analyzer signals
        self.resize_analyzer.stateChanged.connect(self._on_resize_state_changed)
        self.resize_analyzer.highFrequencyDetected.connect(self._on_high_frequency_detected)
        
        # Paint monitor signals
        self.paint_monitor.highPaintFrequency.connect(self._on_high_paint_frequency)
        
        # Metrics collector signals
        self.metrics_collector.baselineEstablished.connect(self._on_baseline_established)
    
    def _install_monitoring(self):
        """Install monitoring hooks into TaskGrid"""
        # Add TaskGrid to paint monitoring
        self.paint_monitor.add_monitored_widget(self.task_grid, "TaskGrid")
        
        # Hook into TaskGrid's resize events
        self._original_resize_event = self.task_grid.resizeEvent
        self.task_grid.resizeEvent = self._monitored_resize_event
        
        # Hook into TaskGrid's paint events (already handled by paint monitor)
        
        if self.debug_mode:
            print("TaskGridDiagnostics: Monitoring hooks installed")
    
    def _monitored_resize_event(self, event):
        """Monitored version of TaskGrid's resizeEvent"""
        # Get old and new sizes
        old_size = (self.task_grid.width(), self.task_grid.height())
        
        # Time the resize event
        with TimedOperation(self.performance_monitor, "resize_event"):
            # Call original resize event
            result = self._original_resize_event(event)
        
        # Get new size after resize
        new_size = (event.size().width(), event.size().height())
        
        # Analyze resize event
        if self._diagnostics_active:
            self.resize_analyzer.analyze_resize_event(old_size, new_size, "user_drag")
        
        return result
    
    def start_baseline_collection(self, duration_seconds: int = 30) -> str:
        """
        Start collecting baseline performance metrics.
        
        Args:
            duration_seconds: How long to collect baseline data
            
        Returns:
            Session ID for the baseline collection
        """
        if self._diagnostics_active:
            self.stop_diagnostics()
        
        test_conditions = {
            'test_type': 'baseline',
            'duration_seconds': duration_seconds,
            'task_count': self.task_grid.model().rowCount() if self.task_grid.model() else 0,
            'widget_size': (self.task_grid.width(), self.task_grid.height())
        }
        
        self._baseline_session_id = self.metrics_collector.start_baseline_collection(test_conditions)
        self._diagnostics_active = True
        
        # Start paint monitoring
        self.paint_monitor.start_monitoring_session("baseline")
        
        # Set up timer to automatically end baseline collection
        QtCore.QTimer.singleShot(duration_seconds * 1000, self._end_baseline_collection)
        
        if self.debug_mode:
            print(f"TaskGridDiagnostics: Started baseline collection for {duration_seconds}s")
        
        self.diagnosticsStarted.emit()
        return self._baseline_session_id
    
    def _end_baseline_collection(self):
        """End baseline collection automatically"""
        if self._baseline_session_id:
            baseline_metrics = self.metrics_collector.end_baseline_collection()
            self._baseline_session_id = None
            self._diagnostics_active = False
            
            # Stop paint monitoring
            self.paint_monitor.end_monitoring_session()
            
            if self.debug_mode:
                print("TaskGridDiagnostics: Baseline collection completed automatically")
            
            self.baselineCompleted.emit(baseline_metrics.__dict__)
            self.diagnosticsStopped.emit()
    
    def start_performance_test(self, test_name: str, duration_seconds: int = 60) -> str:
        """
        Start a performance test session.
        
        Args:
            test_name: Name of the performance test
            duration_seconds: How long to run the test
            
        Returns:
            Session ID for the performance test
        """
        if self._diagnostics_active:
            self.stop_diagnostics()
        
        test_conditions = {
            'test_type': 'performance_test',
            'test_name': test_name,
            'duration_seconds': duration_seconds,
            'task_count': self.task_grid.model().rowCount() if self.task_grid.model() else 0,
            'widget_size': (self.task_grid.width(), self.task_grid.height())
        }
        
        self._current_test_session_id = self.metrics_collector.start_performance_test(test_name, test_conditions)
        self._diagnostics_active = True
        
        # Start paint monitoring
        self.paint_monitor.start_monitoring_session("performance_test")
        
        # Set up timer to automatically end test
        QtCore.QTimer.singleShot(duration_seconds * 1000, self._end_performance_test)
        
        if self.debug_mode:
            print(f"TaskGridDiagnostics: Started performance test '{test_name}' for {duration_seconds}s")
        
        self.diagnosticsStarted.emit()
        return self._current_test_session_id
    
    def _end_performance_test(self):
        """End performance test automatically"""
        if self._current_test_session_id:
            report = self.metrics_collector.end_performance_test()
            self._current_test_session_id = None
            self._diagnostics_active = False
            
            # Stop paint monitoring
            self.paint_monitor.end_monitoring_session()
            
            if self.debug_mode:
                print("TaskGridDiagnostics: Performance test completed automatically")
            
            self.diagnosticsStopped.emit()
    
    def stop_diagnostics(self):
        """Stop all diagnostic monitoring"""
        if self._baseline_session_id:
            self.metrics_collector.end_baseline_collection()
            self._baseline_session_id = None
        
        if self._current_test_session_id:
            self.metrics_collector.end_performance_test()
            self._current_test_session_id = None
        
        self._diagnostics_active = False
        self.paint_monitor.end_monitoring_session()
        
        if self.debug_mode:
            print("TaskGridDiagnostics: All diagnostics stopped")
        
        self.diagnosticsStopped.emit()
    
    def get_current_metrics(self) -> dict:
        """Get current performance metrics"""
        return {
            'resize_state': self.resize_analyzer.get_current_state().value,
            'resize_frequency': self.resize_analyzer.get_current_frequency(),
            'paint_statistics': self.paint_monitor.get_widget_statistics(),
            'performance_statistics': self.performance_monitor.get_operation_statistics(),
            'has_baseline': self.metrics_collector.has_baseline()
        }
    
    def generate_diagnostic_report(self) -> dict:
        """Generate a comprehensive diagnostic report"""
        current_metrics = self.get_current_metrics()
        
        # Get recent events for analysis
        recent_resize_events = list(self.resize_analyzer._recent_events)[-50:] if hasattr(self.resize_analyzer, '_recent_events') else []
        recent_paint_events = self.paint_monitor.get_recent_events(limit=50)
        recent_performance_metrics = self.performance_monitor.get_recent_metrics(limit=50)
        
        return {
            'timestamp': QtCore.QDateTime.currentDateTime().toString(),
            'current_metrics': current_metrics,
            'recent_events': {
                'resize_events': len(recent_resize_events),
                'paint_events': len(recent_paint_events),
                'performance_metrics': len(recent_performance_metrics)
            },
            'diagnostics_active': self._diagnostics_active,
            'baseline_available': self.metrics_collector.has_baseline()
        }
    
    def _on_resize_state_changed(self, old_state: ResizeState, new_state: ResizeState):
        """Handle resize state changes"""
        if self.debug_mode:
            print(f"TaskGridDiagnostics: Resize state changed {old_state.value} -> {new_state.value}")
    
    def _on_high_frequency_detected(self, frequency: float):
        """Handle high frequency resize detection"""
        issue_data = {
            'type': 'high_resize_frequency',
            'frequency_hz': frequency,
            'threshold_hz': 10.0
        }
        
        if self.debug_mode:
            print(f"TaskGridDiagnostics: High resize frequency detected: {frequency:.1f}Hz")
        
        self.performanceIssueDetected.emit("high_resize_frequency", issue_data)
    
    def _on_high_paint_frequency(self, widget_name: str, frequency: float):
        """Handle high frequency paint detection"""
        issue_data = {
            'type': 'high_paint_frequency',
            'widget_name': widget_name,
            'frequency_hz': frequency,
            'threshold_hz': 30.0
        }
        
        if self.debug_mode:
            print(f"TaskGridDiagnostics: High paint frequency detected for {widget_name}: {frequency:.1f}Hz")
        
        self.performanceIssueDetected.emit("high_paint_frequency", issue_data)
    
    def _on_baseline_established(self, baseline_metrics):
        """Handle baseline establishment"""
        if self.debug_mode:
            print("TaskGridDiagnostics: Baseline metrics established")
    
    def cleanup(self):
        """Clean up diagnostic monitoring"""
        self.stop_diagnostics()
        
        # Restore original resize event
        if hasattr(self, '_original_resize_event'):
            self.task_grid.resizeEvent = self._original_resize_event
        
        # Remove paint monitoring
        self.paint_monitor.remove_monitored_widget("TaskGrid")
        
        if self.debug_mode:
            print("TaskGridDiagnostics: Cleanup completed")


def create_diagnostics_for_task_grid(task_grid: QtWidgets.QTableView, debug_mode: bool = False) -> TaskGridDiagnostics:
    """
    Convenience function to create and configure diagnostics for a TaskGrid.
    
    Args:
        task_grid: The TaskGrid widget to monitor
        debug_mode: Enable debug output
        
    Returns:
        TaskGridDiagnostics instance
    """
    return TaskGridDiagnostics(task_grid, debug_mode) 