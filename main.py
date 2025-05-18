import sys
import os
from PySide6 import QtCore, QtWidgets, QtGui

# Import our new components
from week_widget import WeekWidget
from task_grid import TaskGrid
from analysis_widget import AnalysisWidget
from db_schema import init_db

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auditor Helper")
        self.resize(1200, 800)
        
        # Initialize the database
        init_db()
        
        # Create central widget and main layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Create dock widgets
        self.create_dock_widgets()
        
        # Task area
        task_area = QtWidgets.QWidget()
        task_layout = QtWidgets.QVBoxLayout(task_area)
        
        # Add task button
        add_task_layout = QtWidgets.QHBoxLayout()
        self.add_task_btn = QtWidgets.QPushButton("Add New Task")
        self.add_task_btn.clicked.connect(self.add_task)
        add_task_layout.addWidget(self.add_task_btn)
        add_task_layout.addStretch()
        task_layout.addLayout(add_task_layout)
        
        # Task grid
        self.task_grid = TaskGrid(self)
        task_layout.addWidget(self.task_grid)
        
        # Add task area to main layout
        main_layout.addWidget(task_area)
        
        # Connect signals
        self.week_widget.weekChanged.connect(self.on_week_changed)
        
        # Initial state
        self.current_week_id = None
    
    def create_dock_widgets(self):
        # Week widget dock
        self.week_widget = WeekWidget()
        week_dock = QtWidgets.QDockWidget("Weeks", self)
        week_dock.setWidget(self.week_widget)
        week_dock.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, week_dock)
        
        # Analysis widget dock
        self.analysis_widget = AnalysisWidget()
        analysis_dock = QtWidgets.QDockWidget("Data Analysis", self)
        analysis_dock.setWidget(self.analysis_widget)
        analysis_dock.setAllowedAreas(
            QtCore.Qt.BottomDockWidgetArea | QtCore.Qt.TopDockWidgetArea
        )
        self.addDockWidget(QtCore.Qt.BottomDockWidgetArea, analysis_dock)
        
        # Add to View menu
        view_menu = self.menuBar().addMenu("View")
        view_menu.addAction(week_dock.toggleViewAction())
        view_menu.addAction(analysis_dock.toggleViewAction())

    def on_week_changed(self, week_id, week_label):
        self.current_week_id = week_id
        self.task_grid.refresh_tasks(week_id)
        self.refresh_analysis()
        
        # Update window title
        if week_label:
            self.setWindowTitle(f"Auditor Helper - {week_label}")
        else:
            self.setWindowTitle("Auditor Helper")
    
    def add_task(self):
        if self.current_week_id is not None:
            self.task_grid.add_task(self.current_week_id)
            self.refresh_analysis()
    
    def refresh_analysis(self):
        self.analysis_widget.refresh_analysis(self.current_week_id)

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

