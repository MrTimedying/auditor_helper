import sys
import os
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import QPropertyAnimation

# Import our new components
from week_widget import WeekWidget
from task_grid import TaskGrid
from analysis_widget import AnalysisWidget
from db_schema import init_db, migrate_time_columns
from export_data import export_week_to_csv, export_all_weeks_to_excel
from import_data import main_import
from toaster import ToasterManager
from theme_manager import ThemeManager
from options_dialog import OptionsDialog

basedir = os.path.dirname(__file__)

try:
    from ctypes import windll  # Only exists on Windows.
    myappid = 'com.auditorhelper.app' # Arbitrary string
    windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
except ImportError:
    pass

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auditor Helper") # Set proper title instead of empty string
        self.resize(1200, 800)
        self.setWindowIcon(QtGui.QIcon(os.path.join(basedir, "icons", "app_icon.ico")))
        
        # Initialize the database
        init_db()
        migrate_time_columns()
        
        # Initialize toaster manager
        self.toaster_manager = ToasterManager(self)
        
        # Set default dark mode
        self.dark_mode = True
        
        # Initialize ThemeManager
        self.theme_manager = ThemeManager()
        
        # Create central widget and main layout
        central_widget = QtWidgets.QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QtWidgets.QVBoxLayout(central_widget)
        
        # Create top bar with theme toggle button
        top_bar = QtWidgets.QWidget()
        top_bar_layout = QtWidgets.QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(5, 5, 5, 5)
        
        # Add spacer to push button to the right
        top_bar_layout.addStretch()
        
        # Week sidebar toggle button
        self.toggle_week_sidebar_btn = QtWidgets.QPushButton("⬅️ Hide Weeks")
        self.toggle_week_sidebar_btn.setToolTip("Toggle visibility of the Weeks sidebar")
        self.toggle_week_sidebar_btn.clicked.connect(self.toggle_week_sidebar)
        top_bar_layout.addWidget(self.toggle_week_sidebar_btn)
        
        main_layout.addWidget(top_bar)
        
        # Initialize week widget and dock widget
        self.week_widget = WeekWidget()
        self.week_widget.main_window = self  # Set the main window reference
        self.week_dock = QtWidgets.QDockWidget("Weeks", self)
        self.week_dock.setWidget(self.week_widget)
        self.week_dock.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.week_dock)

        # Week sidebar animation
        self.week_animation_min_width = QPropertyAnimation(self.week_dock, b"minimumWidth", self)
        self.week_animation_max_width = QPropertyAnimation(self.week_dock, b"maximumWidth", self)
        self.week_animation_min_width.setDuration(200) # milliseconds
        self.week_animation_max_width.setDuration(200) # milliseconds

        # Connect animation finished signal to a single handler
        self.week_animation_min_width.finished.connect(self._on_animation_finished)
        self.week_animation_max_width.finished.connect(self._on_animation_finished)

        # Initialize analysis widget here as a standalone window
        self.analysis_widget = AnalysisWidget()
        
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
            "QPushButton { background-color: #ff6b6b; color: white; border: 1px solid #1f201f; border-radius: 4px; padding: 1px 2px; font-size: 11px; }"
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
        
        # Apply theme now that all UI elements are created
        self.apply_theme()
    
    def apply_theme(self):
        """Apply the current theme (dark or light) to the application"""
        self.theme_manager.apply_theme(self.dark_mode)
        
        # Keep the delete button style consistent regardless of theme
        self.delete_rows_btn.setStyleSheet(
            "QPushButton { background-color: #ff6b6b; color: white; border-radius: 4px; }"
            "QPushButton:hover { background-color: #ff4747; }"
            "QPushButton:disabled { background-color: #ffb1b1; color: #f0f0f0; }"
        )
        
        # Apply rounded styles to the add task button
        self.add_task_btn.setStyleSheet(
            "QPushButton { border-radius: 4px; }"
        )

    def toggle_theme(self):
        """Toggle between dark and light mode"""
        self.dark_mode = not self.dark_mode
        self.apply_theme()
        self.update_theme_button()
        
        # Show a notification that theme changed
        theme_name = "Dark" if self.dark_mode else "Light"
        self.toaster_manager.show_info(f"{theme_name} mode activated", "Theme Changed", 3000)

    def update_theme_button(self):
        """Update the theme button text based on current mode"""
        # This method is now called from OptionsDialog to update the main window's internal state
        # It no longer updates a button in the main window directly.
        pass
    
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
        
        # Add Preferences action
        preferences_action = QtGui.QAction("Preferences", self)
        preferences_action.triggered.connect(self.show_preferences)
        file_menu.addSeparator()
        file_menu.addAction(preferences_action)

        # Add exit action
        exit_action = QtGui.QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menu_bar.addMenu("View")
        view_menu.addAction(self.week_dock.toggleViewAction())
        
        # Add new action to open Analysis Widget as a separate window
        open_analysis_action = QtGui.QAction("Data Analysis Window", self)
        open_analysis_action.triggered.connect(self.show_analysis_widget)
        view_menu.addAction(open_analysis_action)
    
    def create_dock_widgets(self):
        # This method is now empty as week_dock is created in __init__
        pass

    def on_week_changed(self, week_id, week_label):
        self.current_week_id = week_id
        self.task_grid.refresh_tasks(week_id)
        # Note: Analysis widget is no longer automatically refreshed here
        # Users must manually select the week in the analysis widget
        
        # Refresh the week combo in analysis widget to mirror week widget changes
        self.analysis_widget.refresh_week_combo()
        
        # Update window title with week label or default title
        if week_label:
            self.setWindowTitle(f"Auditor Helper - {week_label}")
        else:
            self.setWindowTitle("Auditor Helper")
    
    def add_task(self):
        if self.current_week_id is not None:
            self.task_grid.add_task(self.current_week_id)
            # Note: Analysis widget is no longer automatically refreshed
            # Show toaster notification
            self.toaster_manager.show_info("New task added successfully", "Task Added", 3000)
    
    def delete_selected_tasks(self):
        # Use a toaster with confirmation instead of a dialog
        count = len(self.task_grid.selected_tasks)
        if count > 0:
            message = f"Are you sure you want to delete {count} {'task' if count == 1 else 'tasks'}?"
            self.toaster_manager.show_question(message, "Confirm Deletion", self.confirm_delete_tasks)
    
    def confirm_delete_tasks(self, result):
        # Called when the user responds to the delete confirmation toaster
        if result:
            self.task_grid.delete_selected_tasks()
            # Show success toaster
            self.toaster_manager.show_info("Tasks deleted successfully", "Tasks Deleted", 3000)
    
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
            # Show warning toaster
            self.toaster_manager.show_warning("Please select a week to export.", "No Week Selected", 5000)
            return
        
        # Open file dialog to get save location
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save CSV File", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if filename:
            try:
                export_week_to_csv(self.current_week_id, filename)
                # Show success toaster
                self.toaster_manager.show_info(f"Week exported successfully to {filename}", "Export Successful", 5000)
            except Exception as e:
                # Show error toaster
                self.toaster_manager.show_error(f"Failed to export week: {str(e)}", "Export Failed", 5000)
    
    def export_all_weeks(self):
        """Export all weeks to an Excel file with multiple sheets"""
        # Open file dialog to get save location
        filename, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Excel File", "", "Excel Files (*.xlsx);;All Files (*)"
        )
        
        if filename:
            try:
                export_all_weeks_to_excel(filename)
                # Show success toaster
                self.toaster_manager.show_info(f"All weeks exported successfully to {filename}", "Export Successful", 5000)
            except Exception as e:
                # Show error toaster
                self.toaster_manager.show_error(f"Failed to export all weeks: {str(e)}", "Export Failed", 5000)
    
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
                # Refresh the week combo in analysis widget to reflect imported weeks
                self.analysis_widget.refresh_week_combo()
                if self.current_week_id:
                    self.task_grid.refresh_tasks(self.current_week_id)
                
                # Show success toaster
                self.toaster_manager.show_info(f"Data import from {filename} complete.", "Import Complete", 5000)
            except Exception as e:
                # Show error toaster
                self.toaster_manager.show_error(f"Failed to import data: {str(e)}", "Import Failed", 5000)

    def show_analysis_widget(self):
        """Show the AnalysisWidget as a separate window"""
        self.analysis_widget.show()

    def toggle_week_sidebar(self):
        """Toggle the visibility of the WeekWidget sidebar with animation"""
        if self.week_animation_min_width.state() == QtCore.QAbstractAnimation.Running or \
           self.week_animation_max_width.state() == QtCore.QAbstractAnimation.Running:
            self.week_animation_min_width.stop()
            self.week_animation_max_width.stop()

        current_width = self.week_dock.width()
        # Get the preferred width of the week_widget for showing
        target_width = self.week_widget.sizeHint().width()
        if not self.week_widget.sizeHint().isValid() or target_width == 0:
            target_width = 250 # Fallback default width
        hidden_width = 0

        if self.week_dock.isVisible():
            # Hiding the sidebar
            self.week_animation_min_width.setStartValue(current_width)
            self.week_animation_min_width.setEndValue(hidden_width)
            self.week_animation_max_width.setStartValue(current_width)
            self.week_animation_max_width.setEndValue(hidden_width)
            
            self.toggle_week_sidebar_btn.setText("➡️ Show Weeks")
        else:
            # Showing the sidebar
            self.week_animation_min_width.setStartValue(hidden_width)
            self.week_animation_min_width.setEndValue(target_width)
            self.week_animation_max_width.setStartValue(hidden_width)
            self.week_animation_max_width.setEndValue(target_width)

            self.week_dock.show() # Show before animation starts
            
            self.toggle_week_sidebar_btn.setText("⬅️ Hide Weeks")
        
        self.week_animation_min_width.start()
        self.week_animation_max_width.start()

    def _on_animation_finished(self):
        """Callback when animation finishes"""
        # If the animation finished with width 0, then the dock was hidden
        if self.week_dock.width() == 0:
            self.week_dock.hide()

    def show_preferences(self):
        dialog = OptionsDialog(parent=self, theme_manager=self.theme_manager, initial_dark_mode=self.dark_mode)
        dialog.exec()
        self.dark_mode = dialog.dark_mode # Update main window's dark_mode based on dialog's final state
        self.apply_theme() # Re-apply theme in case it was changed in the dialog

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationDisplayName("") # Set empty application display name
    app.setWindowIcon(QtGui.QIcon(os.path.join(basedir, "icons", "helper_icon.ico")))
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

