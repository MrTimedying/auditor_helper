import sys
import os
from PySide6 import QtCore, QtWidgets, QtGui

# Import our new components
from week_widget import WeekWidget
from task_grid import TaskGrid
from analysis_widget import AnalysisWidget
from db_schema import init_db
from export_data import export_week_to_csv, export_all_weeks_to_excel
from import_data import main_import

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
        
        # Create menu bar
        self.create_menu_bar()
        
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
        
        # Add delete rows button
        self.delete_rows_btn = QtWidgets.QPushButton("Delete Rows")
        self.delete_rows_btn.clicked.connect(self.delete_selected_tasks)
        self.delete_rows_btn.setEnabled(False)  # Disable initially
        
        # Set delete button style to be red-ish
        self.delete_rows_btn.setStyleSheet(
            "QPushButton { background-color: #ff6b6b; color: white; }"
            "QPushButton:hover { background-color: #ff4747; }"
            "QPushButton:disabled { background-color: #ffb1b1; color: #f0f0f0; }"
        )
        
        add_task_layout.addWidget(self.delete_rows_btn)
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
    
    def create_menu_bar(self):
        # Create menu bar
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("File")
        
        # Export submenu
        export_menu = file_menu.addMenu("Export")
        
        # Export Week action
        export_week_action = QtGui.QAction("Export Week", self)
        export_week_action.triggered.connect(self.export_current_week)
        export_menu.addAction(export_week_action)
        
        # Export All action
        export_all_action = QtGui.QAction("Export All", self)
        export_all_action.triggered.connect(self.export_all_weeks)
        export_menu.addAction(export_all_action)
        
        # Import submenu
        import_menu = file_menu.addMenu("Import")
        
        # Import CSV/Excel action
        import_action = QtGui.QAction("Import CSV/Excel", self)
        import_action.triggered.connect(self.import_data)
        import_menu.addAction(import_action)
        
        # Add exit action
        exit_action = QtGui.QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
    
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
    
    def delete_selected_tasks(self):
        self.task_grid.delete_selected_tasks()
    
    def update_delete_button(self):
        """Update the delete button text based on selection count"""
        count = len(self.task_grid.selected_tasks)
        if count == 0:
            self.delete_rows_btn.setText("Delete Rows")
            self.delete_rows_btn.setEnabled(False)
        elif count == 1:
            self.delete_rows_btn.setText("Delete Row")
            self.delete_rows_btn.setEnabled(True)
        else:
            self.delete_rows_btn.setText(f"Delete Rows ({count})")
            self.delete_rows_btn.setEnabled(True)
    
    def refresh_analysis(self):
        self.analysis_widget.refresh_analysis(self.current_week_id)
    
    def export_current_week(self):
        """Export the current week's tasks to a CSV file"""
        if self.current_week_id is None:
            QtWidgets.QMessageBox.warning(
                self, "No Week Selected", 
                "Please select a week to export."
            )
            return
        
        # Open file dialog to get save location
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            try:
                export_week_to_csv(self.current_week_id, filename)
                QtWidgets.QMessageBox.information(
                    self, "Export Successful", 
                    f"Week exported successfully to {filename}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Export Failed", 
                    f"Failed to export week: {str(e)}"
                )
    
    def export_all_weeks(self):
        """Export all weeks to an Excel file with multiple sheets"""
        # Open file dialog to get save location
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Excel File", "", "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if filename:
            try:
                export_all_weeks_to_excel(filename)
                QtWidgets.QMessageBox.information(
                    self, "Export Successful", 
                    f"All weeks exported successfully to {filename}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Export Failed", 
                    f"Failed to export all weeks: {str(e)}"
                )
    
    def import_data(self):
        """Import data from a CSV or Excel file"""
        # Open file dialog to get file to import
        filename, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open File for Import", "", "Data Files (*.csv *.xlsx);;CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)"
        )
        
        if filename:
            try:
                # Show a progress dialog
                progress_dialog = QtWidgets.QProgressDialog("Importing data...", "Cancel", 0, 0, self)
                progress_dialog.setWindowTitle("Import Progress")
                progress_dialog.setWindowModality(QtCore.Qt.WindowModal)
                progress_dialog.show()
                QtWidgets.QApplication.processEvents()
                
                # Execute the import
                main_import(filename)
                
                # Close the progress dialog
                progress_dialog.close()
                
                # Refresh UI
                self.week_widget.refresh_weeks()
                if self.current_week_id:
                    self.task_grid.refresh_tasks(self.current_week_id)
                    self.refresh_analysis()
                
                QtWidgets.QMessageBox.information(
                    self, "Import Complete", 
                    f"Data import from {filename} complete."
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Import Failed", 
                    f"Failed to import data: {str(e)}"
                )

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

