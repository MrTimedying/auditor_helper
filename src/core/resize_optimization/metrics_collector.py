"""
Metrics Collector for Resize Optimization

This module provides comprehensive metrics collection and analysis capabilities
for establishing baseline performance measurements and tracking improvements.
"""

import time
import json
import os
from datetime import datetime
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from PySide6 import QtCore

from .performance_monitor import PerformanceMonitor, PerformanceMetric
from .resize_analyzer import ResizeAnalyzer, ResizeState
from .paint_monitor import PaintMonitor, PaintEvent


@dataclass
class BaselineMetrics:
    """Baseline performance metrics for comparison"""
    timestamp: str
    system_info: Dict[str, Any]
    resize_metrics: Dict[str, Any]
    paint_metrics: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    test_conditions: Dict[str, Any]


@dataclass
class MetricsReport:
    """Comprehensive metrics report"""
    report_id: str
    generation_time: str
    baseline_metrics: Optional[BaselineMetrics]
    current_metrics: Dict[str, Any]
    comparison_analysis: Dict[str, Any]
    recommendations: List[str]


class MetricsCollector(QtCore.QObject):
    """
    Collects and analyzes performance metrics for resize optimization.
    
    This class coordinates with other monitoring components to:
    - Establish baseline performance measurements
    - Track performance improvements over time
    - Generate comprehensive reports
    - Provide recommendations for optimization
    """
    
    # Signals for metrics collection
    baselineEstablished = QtCore.Signal(BaselineMetrics)
    reportGenerated = QtCore.Signal(MetricsReport)
    metricsUpdated = QtCore.Signal(dict)
    
    def __init__(self, data_directory: str = "metrics_data"):
        super().__init__()
        self.data_directory = data_directory
        
        # Ensure data directory exists
        os.makedirs(data_directory, exist_ok=True)
        
        # Component references
        self.performance_monitor: Optional[PerformanceMonitor] = None
        self.resize_analyzer: Optional[ResizeAnalyzer] = None
        self.paint_monitor: Optional[PaintMonitor] = None
        
        # Metrics storage
        self._baseline_metrics: Optional[BaselineMetrics] = None
        self._metrics_history: List[Dict] = []
        self._current_test_session: Optional[Dict] = None
        
        # Configuration
        self._debug_mode = False
        
        # Load existing baseline if available
        self._load_baseline_metrics()
    
    def set_debug_mode(self, debug: bool):
        """Enable or disable debug output"""
        self._debug_mode = debug
    
    def set_monitoring_components(self, performance_monitor: PerformanceMonitor = None,
                                resize_analyzer: ResizeAnalyzer = None,
                                paint_monitor: PaintMonitor = None):
        """Set references to monitoring components"""
        self.performance_monitor = performance_monitor
        self.resize_analyzer = resize_analyzer
        self.paint_monitor = paint_monitor
        
        if self._debug_mode:
            print("MetricsCollector: Monitoring components configured")
    
    def start_baseline_collection(self, test_conditions: Dict = None) -> str:
        """
        Start collecting baseline performance metrics.
        
        Args:
            test_conditions: Dictionary describing test conditions
            
        Returns:
            Test session ID
        """
        session_id = f"baseline_{int(time.time())}"
        
        self._current_test_session = {
            'session_id': session_id,
            'start_time': time.time(),
            'test_conditions': test_conditions or {},
            'type': 'baseline'
        }
        
        # Start monitoring components
        if self.performance_monitor:
            self.performance_monitor.start_session("baseline_perf")
        
        if self.resize_analyzer:
            self.resize_analyzer.reset()
        
        if self.paint_monitor:
            self.paint_monitor.start_monitoring_session("baseline")
        
        if self._debug_mode:
            print(f"MetricsCollector: Started baseline collection session {session_id}")
        
        return session_id
    
    def end_baseline_collection(self) -> BaselineMetrics:
        """
        End baseline collection and establish baseline metrics.
        
        Returns:
            BaselineMetrics object with collected data
        """
        if not self._current_test_session:
            raise ValueError("No active baseline collection session")
        
        end_time = time.time()
        duration = end_time - self._current_test_session['start_time']
        
        # Collect metrics from all components
        resize_metrics = self._collect_resize_metrics()
        paint_metrics = self._collect_paint_metrics()
        performance_metrics = self._collect_performance_metrics()
        system_info = self._collect_system_info()
        
        # Create baseline metrics
        baseline = BaselineMetrics(
            timestamp=datetime.now().isoformat(),
            system_info=system_info,
            resize_metrics=resize_metrics,
            paint_metrics=paint_metrics,
            performance_metrics=performance_metrics,
            test_conditions=self._current_test_session['test_conditions']
        )
        
        # Store baseline
        self._baseline_metrics = baseline
        self._save_baseline_metrics(baseline)
        
        # Stop monitoring
        if self.performance_monitor:
            self.performance_monitor.end_session()
        
        if self.paint_monitor:
            self.paint_monitor.end_monitoring_session()
        
        self._current_test_session = None
        
        if self._debug_mode:
            print(f"MetricsCollector: Baseline collection completed, duration: {duration:.2f}s")
        
        self.baselineEstablished.emit(baseline)
        return baseline
    
    def start_performance_test(self, test_name: str, test_conditions: Dict = None) -> str:
        """
        Start a performance test session.
        
        Args:
            test_name: Name/description of the test
            test_conditions: Dictionary describing test conditions
            
        Returns:
            Test session ID
        """
        session_id = f"test_{test_name}_{int(time.time())}"
        
        self._current_test_session = {
            'session_id': session_id,
            'start_time': time.time(),
            'test_name': test_name,
            'test_conditions': test_conditions or {},
            'type': 'performance_test'
        }
        
        # Start monitoring components
        if self.performance_monitor:
            self.performance_monitor.start_session(f"test_{test_name}")
        
        if self.resize_analyzer:
            self.resize_analyzer.reset()
        
        if self.paint_monitor:
            self.paint_monitor.start_monitoring_session(f"test_{test_name}")
        
        if self._debug_mode:
            print(f"MetricsCollector: Started performance test '{test_name}' session {session_id}")
        
        return session_id
    
    def end_performance_test(self) -> MetricsReport:
        """
        End performance test and generate comparison report.
        
        Returns:
            MetricsReport with analysis and recommendations
        """
        if not self._current_test_session:
            raise ValueError("No active performance test session")
        
        end_time = time.time()
        duration = end_time - self._current_test_session['start_time']
        
        # Collect current metrics
        current_metrics = {
            'resize_metrics': self._collect_resize_metrics(),
            'paint_metrics': self._collect_paint_metrics(),
            'performance_metrics': self._collect_performance_metrics(),
            'test_duration': duration,
            'test_conditions': self._current_test_session['test_conditions']
        }
        
        # Generate comparison analysis
        comparison_analysis = self._generate_comparison_analysis(current_metrics)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(current_metrics, comparison_analysis)
        
        # Create report
        report = MetricsReport(
            report_id=self._current_test_session['session_id'],
            generation_time=datetime.now().isoformat(),
            baseline_metrics=self._baseline_metrics,
            current_metrics=current_metrics,
            comparison_analysis=comparison_analysis,
            recommendations=recommendations
        )
        
        # Save report
        self._save_metrics_report(report)
        
        # Stop monitoring
        if self.performance_monitor:
            self.performance_monitor.end_session()
        
        if self.paint_monitor:
            self.paint_monitor.end_monitoring_session()
        
        self._current_test_session = None
        
        if self._debug_mode:
            print(f"MetricsCollector: Performance test completed, duration: {duration:.2f}s")
        
        self.reportGenerated.emit(report)
        return report
    
    def _collect_resize_metrics(self) -> Dict:
        """Collect metrics from resize analyzer"""
        if not self.resize_analyzer:
            return {}
        
        return {
            'current_state': self.resize_analyzer.get_current_state().value,
            'current_frequency': self.resize_analyzer.get_current_frequency(),
            'recent_events_count': len(self.resize_analyzer._recent_events)
        }
    
    def _collect_paint_metrics(self) -> Dict:
        """Collect metrics from paint monitor"""
        if not self.paint_monitor:
            return {}
        
        widget_stats = self.paint_monitor.get_widget_statistics()
        recent_events = self.paint_monitor.get_recent_events(limit=100)
        
        return {
            'widget_statistics': widget_stats,
            'recent_events_count': len(recent_events),
            'total_widgets_monitored': len(widget_stats)
        }
    
    def _collect_performance_metrics(self) -> Dict:
        """Collect metrics from performance monitor"""
        if not self.performance_monitor:
            return {}
        
        operation_stats = self.performance_monitor.get_operation_statistics()
        recent_metrics = self.performance_monitor.get_recent_metrics(limit=100)
        
        # Calculate summary statistics
        if recent_metrics:
            durations = [m.duration_ms for m in recent_metrics]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
        else:
            avg_duration = max_duration = min_duration = 0
        
        return {
            'operation_statistics': operation_stats,
            'recent_metrics_count': len(recent_metrics),
            'duration_statistics': {
                'avg_duration_ms': avg_duration,
                'max_duration_ms': max_duration,
                'min_duration_ms': min_duration
            }
        }
    
    def _collect_system_info(self) -> Dict:
        """Collect system information for context"""
        import platform
        import psutil
        
        try:
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'cpu_count': psutil.cpu_count(),
                'memory_total_gb': psutil.virtual_memory().total / (1024**3),
                'qt_version': QtCore.__version__ if hasattr(QtCore, '__version__') else 'unknown'
            }
        except ImportError:
            # Fallback if psutil is not available
            return {
                'platform': platform.platform(),
                'python_version': platform.python_version(),
                'qt_version': QtCore.__version__ if hasattr(QtCore, '__version__') else 'unknown'
            }
    
    def _generate_comparison_analysis(self, current_metrics: Dict) -> Dict:
        """Generate comparison analysis between current and baseline metrics"""
        if not self._baseline_metrics:
            return {'status': 'no_baseline', 'message': 'No baseline metrics available for comparison'}
        
        analysis = {
            'status': 'comparison_available',
            'improvements': [],
            'regressions': [],
            'unchanged': []
        }
        
        # Compare resize metrics
        baseline_resize = self._baseline_metrics.resize_metrics
        current_resize = current_metrics.get('resize_metrics', {})
        
        if 'current_frequency' in baseline_resize and 'current_frequency' in current_resize:
            baseline_freq = baseline_resize['current_frequency']
            current_freq = current_resize['current_frequency']
            
            if current_freq < baseline_freq * 0.9:  # 10% improvement
                analysis['improvements'].append(f"Resize frequency reduced from {baseline_freq:.1f}Hz to {current_freq:.1f}Hz")
            elif current_freq > baseline_freq * 1.1:  # 10% regression
                analysis['regressions'].append(f"Resize frequency increased from {baseline_freq:.1f}Hz to {current_freq:.1f}Hz")
        
        # Compare paint metrics
        baseline_paint = self._baseline_metrics.paint_metrics
        current_paint = current_metrics.get('paint_metrics', {})
        
        baseline_events = baseline_paint.get('recent_events_count', 0)
        current_events = current_paint.get('recent_events_count', 0)
        
        if current_events < baseline_events * 0.9:
            analysis['improvements'].append(f"Paint events reduced from {baseline_events} to {current_events}")
        elif current_events > baseline_events * 1.1:
            analysis['regressions'].append(f"Paint events increased from {baseline_events} to {current_events}")
        
        # Compare performance metrics
        baseline_perf = self._baseline_metrics.performance_metrics
        current_perf = current_metrics.get('performance_metrics', {})
        
        baseline_avg = baseline_perf.get('duration_statistics', {}).get('avg_duration_ms', 0)
        current_avg = current_perf.get('duration_statistics', {}).get('avg_duration_ms', 0)
        
        if current_avg < baseline_avg * 0.9:
            analysis['improvements'].append(f"Average operation duration reduced from {baseline_avg:.2f}ms to {current_avg:.2f}ms")
        elif current_avg > baseline_avg * 1.1:
            analysis['regressions'].append(f"Average operation duration increased from {baseline_avg:.2f}ms to {current_avg:.2f}ms")
        
        return analysis
    
    def _generate_recommendations(self, current_metrics: Dict, comparison_analysis: Dict) -> List[str]:
        """Generate optimization recommendations based on metrics"""
        recommendations = []
        
        # Analyze resize frequency
        resize_metrics = current_metrics.get('resize_metrics', {})
        current_freq = resize_metrics.get('current_frequency', 0)
        
        if current_freq > 15:
            recommendations.append("High resize frequency detected (>15Hz). Consider implementing Level 2 optimization.")
        elif current_freq > 25:
            recommendations.append("Very high resize frequency detected (>25Hz). Implement Level 3 optimization immediately.")
        
        # Analyze paint events
        paint_metrics = current_metrics.get('paint_metrics', {})
        paint_events = paint_metrics.get('recent_events_count', 0)
        
        if paint_events > 100:
            recommendations.append("High paint event count detected. Consider paint event throttling.")
        
        # Analyze performance regressions
        if comparison_analysis.get('regressions'):
            recommendations.append("Performance regressions detected. Review recent changes and consider rollback.")
        
        # Analyze improvements
        if comparison_analysis.get('improvements'):
            recommendations.append("Performance improvements detected. Consider documenting successful optimizations.")
        
        if not recommendations:
            recommendations.append("Performance appears stable. Continue monitoring for optimization opportunities.")
        
        return recommendations
    
    def _save_baseline_metrics(self, baseline: BaselineMetrics):
        """Save baseline metrics to file"""
        filepath = os.path.join(self.data_directory, "baseline_metrics.json")
        try:
            with open(filepath, 'w') as f:
                json.dump(asdict(baseline), f, indent=2)
            if self._debug_mode:
                print(f"MetricsCollector: Baseline metrics saved to {filepath}")
        except Exception as e:
            print(f"Error saving baseline metrics: {e}")
    
    def _load_baseline_metrics(self):
        """Load baseline metrics from file"""
        filepath = os.path.join(self.data_directory, "baseline_metrics.json")
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                self._baseline_metrics = BaselineMetrics(**data)
                if self._debug_mode:
                    print(f"MetricsCollector: Baseline metrics loaded from {filepath}")
        except Exception as e:
            print(f"Error loading baseline metrics: {e}")
    
    def _save_metrics_report(self, report: MetricsReport):
        """Save metrics report to file"""
        filename = f"metrics_report_{report.report_id}.json"
        filepath = os.path.join(self.data_directory, filename)
        try:
            with open(filepath, 'w') as f:
                json.dump(asdict(report), f, indent=2)
            if self._debug_mode:
                print(f"MetricsCollector: Report saved to {filepath}")
        except Exception as e:
            print(f"Error saving metrics report: {e}")
    
    def get_baseline_metrics(self) -> Optional[BaselineMetrics]:
        """Get current baseline metrics"""
        return self._baseline_metrics
    
    def has_baseline(self) -> bool:
        """Check if baseline metrics are available"""
        return self._baseline_metrics is not None
    
    def clear_baseline(self):
        """Clear current baseline metrics"""
        self._baseline_metrics = None
        filepath = os.path.join(self.data_directory, "baseline_metrics.json")
        if os.path.exists(filepath):
            os.remove(filepath)
        
        if self._debug_mode:
            print("MetricsCollector: Baseline metrics cleared") 