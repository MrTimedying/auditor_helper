#!/usr/bin/env python3
"""
Test Phase 2 Resize Optimization System

This test validates the complete Phase 2 optimization system including:
- State management
- Optimization strategies
- Integration with diagnostics
- Fallback mechanisms
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import time
from PySide6 import QtWidgets, QtCore, QtGui
from core.resize_optimization import (
    create_phase2_optimization, 
    OptimizationLevel,
    Phase2ResizeOptimization
)


class TestTaskGrid(QtWidgets.QTableView):
    """Test TaskGrid for Phase 2 optimization testing"""
    
    def __init__(self):
        super().__init__()
        self.setObjectName("TestTaskGrid")
        
        # Create a simple model with test data
        model = QtGui.QStandardItemModel(100, 5)
        for row in range(100):
            for col in range(5):
                item = QtGui.QStandardItem(f"Task {row}-{col}")
                model.setItem(row, col, item)
        
        self.setModel(model)
        self.resize(800, 600)
        
        # Track paint events for testing
        self.paint_count = 0
        
    def paintEvent(self, event):
        self.paint_count += 1
        super().paintEvent(event)


class Phase2OptimizationTest(QtWidgets.QWidget):
    """Interactive test interface for Phase 2 optimization"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Phase 2 Resize Optimization Test")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create test TaskGrid
        self.task_grid = TestTaskGrid()
        
        # Initialize Phase 2 optimization system
        self.phase2_system: Phase2ResizeOptimization = None
        self.optimization_log = []
        
        self.setup_ui()
        self.setup_phase2_system()
        
    def setup_ui(self):
        """Setup the test interface"""
        layout = QtWidgets.QHBoxLayout(self)
        
        # Left side: TaskGrid
        left_layout = QtWidgets.QVBoxLayout()
        left_layout.addWidget(QtWidgets.QLabel("TaskGrid (resize to test optimization):"))
        left_layout.addWidget(self.task_grid)
        
        # Right side: Controls and monitoring
        right_layout = QtWidgets.QVBoxLayout()
        right_layout.addWidget(QtWidgets.QLabel("Phase 2 Optimization Controls:"))
        
        # Control buttons
        self.init_button = QtWidgets.QPushButton("Initialize Phase 2 System")
        self.init_button.clicked.connect(self.setup_phase2_system)
        right_layout.addWidget(self.init_button)
        
        self.status_button = QtWidgets.QPushButton("Show Status")
        self.status_button.clicked.connect(self.show_status)
        right_layout.addWidget(self.status_button)
        
        self.report_button = QtWidgets.QPushButton("Generate Report")
        self.report_button.clicked.connect(self.generate_report)
        right_layout.addWidget(self.report_button)
        
        # Test optimization levels
        right_layout.addWidget(QtWidgets.QLabel("Test Optimization Levels:"))
        
        self.test_light_button = QtWidgets.QPushButton("Test Light Optimization")
        self.test_light_button.clicked.connect(lambda: self.test_optimization_level(OptimizationLevel.LIGHT))
        right_layout.addWidget(self.test_light_button)
        
        self.test_medium_button = QtWidgets.QPushButton("Test Medium Optimization")
        self.test_medium_button.clicked.connect(lambda: self.test_optimization_level(OptimizationLevel.MEDIUM))
        right_layout.addWidget(self.test_medium_button)
        
        self.test_heavy_button = QtWidgets.QPushButton("Test Heavy Optimization")
        self.test_heavy_button.clicked.connect(lambda: self.test_optimization_level(OptimizationLevel.HEAVY))
        right_layout.addWidget(self.test_heavy_button)
        
        self.test_static_button = QtWidgets.QPushButton("Test Static Optimization")
        self.test_static_button.clicked.connect(lambda: self.test_optimization_level(OptimizationLevel.STATIC))
        right_layout.addWidget(self.test_static_button)
        
        self.deoptimize_button = QtWidgets.QPushButton("Force Deoptimize")
        self.deoptimize_button.clicked.connect(lambda: self.test_optimization_level(OptimizationLevel.NONE))
        right_layout.addWidget(self.deoptimize_button)
        
        # Monitoring display
        right_layout.addWidget(QtWidgets.QLabel("Optimization Log:"))
        self.log_display = QtWidgets.QTextEdit()
        self.log_display.setMaximumHeight(200)
        right_layout.addWidget(self.log_display)
        
        # Status display
        right_layout.addWidget(QtWidgets.QLabel("Current Status:"))
        self.status_display = QtWidgets.QTextEdit()
        self.status_display.setMaximumHeight(150)
        right_layout.addWidget(self.status_display)
        
        # Layout setup
        left_widget = QtWidgets.QWidget()
        left_widget.setLayout(left_layout)
        right_widget = QtWidgets.QWidget()
        right_widget.setLayout(right_layout)
        
        layout.addWidget(left_widget, 2)  # TaskGrid takes 2/3 of space
        layout.addWidget(right_widget, 1)  # Controls take 1/3 of space
        
        # Update timer
        self.update_timer = QtCore.QTimer()
        self.update_timer.timeout.connect(self.update_displays)
        self.update_timer.start(1000)  # Update every second
        
    def setup_phase2_system(self):
        """Initialize the Phase 2 optimization system"""
        try:
            if self.phase2_system:
                self.phase2_system.cleanup()
            
            # Create Phase 2 optimization system
            self.phase2_system = create_phase2_optimization(self.task_grid, debug_mode=True)
            
            # Connect signals for monitoring
            self.phase2_system.optimizationActivated.connect(self.on_optimization_activated)
            self.phase2_system.optimizationDeactivated.connect(self.on_optimization_deactivated)
            self.phase2_system.performanceImproved.connect(self.on_performance_improved)
            self.phase2_system.fallbackTriggered.connect(self.on_fallback_triggered)
            
            self.log_message("✅ Phase 2 optimization system initialized successfully")
            self.init_button.setText("Reinitialize Phase 2 System")
            
        except Exception as e:
            self.log_message(f"❌ Error initializing Phase 2 system: {e}")
    
    def test_optimization_level(self, level: OptimizationLevel):
        """Test a specific optimization level"""
        if not self.phase2_system:
            self.log_message("❌ Phase 2 system not initialized")
            return
        
        try:
            if level == OptimizationLevel.NONE:
                # Force deoptimization
                if hasattr(self.phase2_system.state_manager, 'force_deoptimize'):
                    self.phase2_system.state_manager.force_deoptimize("Manual test")
                self.log_message("🔄 Forced deoptimization")
            else:
                # Force specific optimization level
                self.phase2_system.force_optimization_level(level, "Manual test")
                self.log_message(f"🔄 Testing {level.name} optimization level")
            
        except Exception as e:
            self.log_message(f"❌ Error testing {level.name}: {e}")
    
    def show_status(self):
        """Show current optimization status"""
        if not self.phase2_system:
            self.log_message("❌ Phase 2 system not initialized")
            return
        
        try:
            status = self.phase2_system.get_optimization_status()
            self.log_message("📊 Status retrieved - check status display")
            
            # Update status display
            status_text = "Current Optimization Status:\n\n"
            for key, value in status.items():
                if isinstance(value, dict):
                    status_text += f"{key}:\n"
                    for sub_key, sub_value in value.items():
                        status_text += f"  {sub_key}: {sub_value}\n"
                else:
                    status_text += f"{key}: {value}\n"
            
            self.status_display.setText(status_text)
            
        except Exception as e:
            self.log_message(f"❌ Error getting status: {e}")
    
    def generate_report(self):
        """Generate comprehensive performance report"""
        if not self.phase2_system:
            self.log_message("❌ Phase 2 system not initialized")
            return
        
        try:
            report = self.phase2_system.get_performance_report()
            self.log_message("📋 Performance report generated")
            
            # Show report in a dialog
            dialog = QtWidgets.QDialog(self)
            dialog.setWindowTitle("Phase 2 Performance Report")
            dialog.setGeometry(200, 200, 600, 400)
            
            layout = QtWidgets.QVBoxLayout(dialog)
            text_edit = QtWidgets.QTextEdit()
            text_edit.setPlainText(str(report))
            layout.addWidget(text_edit)
            
            close_button = QtWidgets.QPushButton("Close")
            close_button.clicked.connect(dialog.accept)
            layout.addWidget(close_button)
            
            dialog.exec()
            
        except Exception as e:
            self.log_message(f"❌ Error generating report: {e}")
    
    def on_optimization_activated(self, level: str, reason: str):
        """Handle optimization activation"""
        self.log_message(f"🚀 Optimization activated: {level} ({reason})")
    
    def on_optimization_deactivated(self, level: str, reason: str):
        """Handle optimization deactivation"""
        self.log_message(f"⏹️ Optimization deactivated: {level} ({reason})")
    
    def on_performance_improved(self, old_freq: float, new_freq: float):
        """Handle performance improvement"""
        improvement = ((old_freq - new_freq) / old_freq) * 100
        self.log_message(f"📈 Performance improved: {old_freq:.1f}Hz → {new_freq:.1f}Hz ({improvement:.1f}% better)")
    
    def on_fallback_triggered(self, reason: str):
        """Handle fallback scenarios"""
        self.log_message(f"⚠️ Fallback triggered: {reason}")
    
    def log_message(self, message: str):
        """Add message to optimization log"""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.optimization_log.append(log_entry)
        
        # Update log display (keep last 20 entries)
        recent_logs = self.optimization_log[-20:]
        self.log_display.setText("\n".join(recent_logs))
        
        # Auto-scroll to bottom
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        print(log_entry)  # Also print to console
    
    def update_displays(self):
        """Update status displays periodically"""
        if self.phase2_system:
            try:
                # Update paint count display
                paint_info = f"Paint Events: {self.task_grid.paint_count}"
                
                # Get current optimization level
                if hasattr(self.phase2_system, 'state_manager') and self.phase2_system.state_manager:
                    current_level = self.phase2_system.state_manager.get_current_level()
                    paint_info += f" | Current Level: {current_level.name}"
                
                # Update window title with current info
                self.setWindowTitle(f"Phase 2 Resize Optimization Test - {paint_info}")
                
            except Exception as e:
                pass  # Ignore update errors
    
    def closeEvent(self, event):
        """Clean up on close"""
        if self.phase2_system:
            self.phase2_system.cleanup()
        event.accept()


def main():
    """Run the Phase 2 optimization test"""
    app = QtWidgets.QApplication(sys.argv)
    
    # Create and show test window
    test_window = Phase2OptimizationTest()
    test_window.show()
    
    print("Phase 2 Resize Optimization Test Started")
    print("=" * 50)
    print("Instructions:")
    print("1. Click 'Initialize Phase 2 System' to start")
    print("2. Resize the TaskGrid to trigger automatic optimization")
    print("3. Use test buttons to manually trigger optimization levels")
    print("4. Monitor the log and status displays")
    print("5. Check console output for detailed debug information")
    print("=" * 50)
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main() 