"""
Test script for resize diagnostic tools

This script tests the Phase 1 diagnostic tools to ensure they work correctly
before integrating them into the main TaskGrid.
"""

import sys
import time
from PySide6 import QtWidgets, QtCore, QtGui

# Add src to path for imports
sys.path.insert(0, '..')

from src.core.resize_optimization import (
    PerformanceMonitor, ResizeAnalyzer, PaintMonitor, MetricsCollector,
    TaskGridDiagnostics, create_diagnostics_for_task_grid
)


class TestTaskGrid(QtWidgets.QTableView):
    """Simple test TaskGrid for diagnostic testing"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test TaskGrid - Resize Diagnostics")
        self.resize(800, 600)
        
        # Create a simple model with test data
        model = QtGui.QStandardItemModel(100, 5)
        model.setHorizontalHeaderLabels(['Task', 'Duration', 'Status', 'Project', 'Notes'])
        
        for row in range(100):
            for col in range(5):
                item = QtGui.QStandardItem(f"Item {row},{col}")
                model.setItem(row, col, item)
        
        self.setModel(model)


class DiagnosticTestWindow(QtWidgets.QMainWindow):
    """Test window for diagnostic tools"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Resize Diagnostics Test")
        self.setGeometry(100, 100, 1000, 700)
        
        # Create central widget and layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Create test TaskGrid
        self.task_grid = TestTaskGrid()
        layout.addWidget(self.task_grid)
        
        # Initialize diagnostics first
        self.diagnostics = create_diagnostics_for_task_grid(self.task_grid, debug_mode=True)
        
        # Create control panel
        control_panel = self.create_control_panel()
        layout.addWidget(control_panel)
        
        # Create status display
        self.status_text = QtWidgets.QTextEdit()
        self.status_text.setMaximumHeight(200)
        self.status_text.setPlainText("Diagnostic Test Window Ready\n")
        layout.addWidget(self.status_text)
        
        # Connect diagnostic signals
        self.diagnostics.diagnosticsStarted.connect(self.on_diagnostics_started)
        self.diagnostics.diagnosticsStopped.connect(self.on_diagnostics_stopped)
        self.diagnostics.baselineCompleted.connect(self.on_baseline_completed)
        self.diagnostics.performanceIssueDetected.connect(self.on_performance_issue)
        
        self.log_message("Diagnostics initialized successfully")
    
    def create_control_panel(self):
        """Create control panel with test buttons"""
        panel = QtWidgets.QGroupBox("Diagnostic Controls")
        layout = QtWidgets.QHBoxLayout(panel)
        
        # Baseline collection button
        baseline_btn = QtWidgets.QPushButton("Start Baseline Collection (10s)")
        baseline_btn.clicked.connect(lambda: self.start_baseline_test())
        layout.addWidget(baseline_btn)
        
        # Performance test button
        perf_test_btn = QtWidgets.QPushButton("Start Performance Test (15s)")
        perf_test_btn.clicked.connect(lambda: self.start_performance_test())
        layout.addWidget(perf_test_btn)
        
        # Current metrics button
        metrics_btn = QtWidgets.QPushButton("Show Current Metrics")
        metrics_btn.clicked.connect(self.show_current_metrics)
        layout.addWidget(metrics_btn)
        
        # Generate report button
        report_btn = QtWidgets.QPushButton("Generate Report")
        report_btn.clicked.connect(self.generate_report)
        layout.addWidget(report_btn)
        
        # Stop diagnostics button
        stop_btn = QtWidgets.QPushButton("Stop Diagnostics")
        stop_btn.clicked.connect(self.diagnostics.stop_diagnostics)
        layout.addWidget(stop_btn)
        
        return panel
    
    def start_baseline_test(self):
        """Start baseline collection test"""
        self.log_message("Starting baseline collection test...")
        session_id = self.diagnostics.start_baseline_collection(duration_seconds=10)
        self.log_message(f"Baseline collection started with session ID: {session_id}")
        self.log_message("Try resizing the window during the next 10 seconds!")
    
    def start_performance_test(self):
        """Start performance test"""
        self.log_message("Starting performance test...")
        session_id = self.diagnostics.start_performance_test("manual_test", duration_seconds=15)
        self.log_message(f"Performance test started with session ID: {session_id}")
        self.log_message("Try resizing the window during the next 15 seconds!")
    
    def show_current_metrics(self):
        """Show current metrics"""
        metrics = self.diagnostics.get_current_metrics()
        self.log_message("Current Metrics:")
        for key, value in metrics.items():
            self.log_message(f"  {key}: {value}")
    
    def generate_report(self):
        """Generate diagnostic report"""
        report = self.diagnostics.generate_diagnostic_report()
        self.log_message("Diagnostic Report:")
        for key, value in report.items():
            self.log_message(f"  {key}: {value}")
    
    def on_diagnostics_started(self):
        """Handle diagnostics started signal"""
        self.log_message("✅ Diagnostics monitoring started")
    
    def on_diagnostics_stopped(self):
        """Handle diagnostics stopped signal"""
        self.log_message("⏹️ Diagnostics monitoring stopped")
    
    def on_baseline_completed(self, baseline_data):
        """Handle baseline completion"""
        self.log_message("📊 Baseline collection completed!")
        self.log_message(f"Baseline timestamp: {baseline_data.get('timestamp', 'unknown')}")
    
    def on_performance_issue(self, issue_type, issue_data):
        """Handle performance issue detection"""
        self.log_message(f"⚠️ Performance issue detected: {issue_type}")
        for key, value in issue_data.items():
            self.log_message(f"  {key}: {value}")
    
    def log_message(self, message):
        """Log a message to the status display"""
        timestamp = QtCore.QTime.currentTime().toString("hh:mm:ss")
        self.status_text.append(f"[{timestamp}] {message}")
        
        # Auto-scroll to bottom
        scrollbar = self.status_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def closeEvent(self, event):
        """Clean up on close"""
        self.diagnostics.cleanup()
        event.accept()


def main():
    """Main test function"""
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show test window
    window = DiagnosticTestWindow()
    window.show()
    
    print("Resize Diagnostics Test Window")
    print("=" * 40)
    print("Instructions:")
    print("1. Click 'Start Baseline Collection' and resize the window")
    print("2. Wait for baseline to complete")
    print("3. Click 'Start Performance Test' and resize the window again")
    print("4. Use other buttons to view metrics and reports")
    print("5. Watch the status area for diagnostic messages")
    print()
    print("The diagnostic tools will monitor resize events, paint events,")
    print("and performance metrics in real-time.")
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 