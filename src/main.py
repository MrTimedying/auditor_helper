import sys
import os
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import QPropertyAnimation
import pathlib
import logging

# Removed debug logging - no longer needed

# Import our new components
from ui.week_widget import WeekWidget
from ui.task_grid import TaskGrid
from analysis.analysis_widget import AnalysisWidget
from core.db.db_schema import run_all_migrations
from core.db.export_data import export_week_to_csv, export_all_weeks_to_excel
from core.db.import_data import main_import
from core.utils.toaster import ToasterManager
from ui.theme_manager import ThemeManager
from ui.options import OptionsDialog
from ui.collapsible_week_sidebar import CollapsibleWeekSidebar
from core.settings.global_settings import get_icon_path

basedir = os.path.dirname(__file__)
project_root = pathlib.Path(__file__).resolve().parent.parent
icons_dir = project_root / 'icons'

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
        
        # Set window icon
        try:
            icon_path = get_icon_path('app_icon.ico')
            self.setWindowIcon(QtGui.QIcon(icon_path))
        except Exception as e:
            pass  # Ignore icon errors
        
        self.resize(1200, 800)
        
        # Initialize the database and run all migrations
        run_all_migrations()
        
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
        
        # Week sidebar toggle button - now integrated into the sidebar itself
        # self.toggle_week_sidebar_btn = QtWidgets.QPushButton("⬅️ Hide Weeks")
        # self.toggle_week_sidebar_btn.setToolTip("Toggle visibility of the Weeks sidebar")
        # self.toggle_week_sidebar_btn.clicked.connect(self.toggle_week_sidebar)
        # top_bar_layout.addWidget(self.toggle_week_sidebar_btn)
        
        main_layout.addWidget(top_bar)
        
        # Initialize week widget - now contained in a custom collapsible sidebar
        self.week_widget = WeekWidget()
        self.week_widget.main_window = self  # Set the main window reference
        
        # Create the custom collapsible week sidebar
        self.collapsible_week_sidebar = CollapsibleWeekSidebar(self.week_widget, parent=self)
        self.collapsible_week_sidebar.setMinimumWidth(self.collapsible_week_sidebar.collapsed_width)
        self.collapsible_week_sidebar.setMaximumWidth(self.collapsible_week_sidebar.expanded_width)
        
        # Add the collapsible sidebar to the main layout (e.g., left side)
        # For now, let's assume it goes into a horizontal layout with the task area
        # We need to create a main horizontal layout for task area and sidebar
        content_layout = QtWidgets.QHBoxLayout()
        content_layout.addWidget(self.collapsible_week_sidebar)
        
        # Initialize analysis widget here as a standalone window
        self.analysis_widget = AnalysisWidget()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create dock widgets (this method will become empty or removed later)
        self.create_dock_widgets()
        
        # Task area
        add_task_area = QtWidgets.QWidget()
        task_layout = QtWidgets.QVBoxLayout(add_task_area)

        # Top row of buttons and controls
        top_buttons_layout = QtWidgets.QHBoxLayout()

        # 1. Task Actions (Add/Delete) - Left aligned
        task_action_layout = QtWidgets.QHBoxLayout()
        self.add_task_btn = QtWidgets.QPushButton("Add New Task")
        self.add_task_btn.clicked.connect(self.add_task)
        task_action_layout.addWidget(self.add_task_btn)

        self.delete_rows_btn = QtWidgets.QPushButton("Delete Rows")
        self.delete_rows_btn.clicked.connect(self.delete_selected_tasks)
        self.delete_rows_btn.setEnabled(False)  # Disable initially
        self.delete_rows_btn.setStyleSheet(
            "QPushButton { background-color: #ff6b6b; color: white; border: 1px solid #1f201f; border-radius: 4px; padding: 1px 2px; font-size: 11px; }"
            "QPushButton:hover { background-color: #ff4747; }"
            "QPushButton:disabled { background-color: #ffb1b1; color: #f0f0f0; }"
        )
        task_action_layout.addWidget(self.delete_rows_btn)
        top_buttons_layout.addLayout(task_action_layout)

        # Add a stretch to push subsequent elements to the right
        top_buttons_layout.addStretch()

        # Group Office Hours and Bonus Toggle on the right
        right_aligned_controls_layout = QtWidgets.QHBoxLayout()

        # 2. Office Hours Controls
        office_hours_controls_layout = QtWidgets.QHBoxLayout()
        office_hours_controls_layout.addWidget(QtWidgets.QLabel("Office Hours:"))
        self.add_oh_session_btn = QtWidgets.QPushButton("+")
        self.add_oh_session_btn.setFixedSize(25, 25)
        self.add_oh_session_btn.setStyleSheet("QPushButton { border-radius: 12px; font-weight: bold; }")
        office_hours_controls_layout.addWidget(self.add_oh_session_btn)

        self.remove_oh_session_btn = QtWidgets.QPushButton("-")
        self.remove_oh_session_btn.setFixedSize(25, 25)
        self.remove_oh_session_btn.setStyleSheet("QPushButton { border-radius: 12px; font-weight: bold; }")
        office_hours_controls_layout.addWidget(self.remove_oh_session_btn)

        self.office_hour_count_label = QtWidgets.QLabel("N/A")
        self.office_hour_count_label.setStyleSheet("QLabel { color: #D6D6D6; font-weight: bold; }")
        office_hours_controls_layout.addWidget(self.office_hour_count_label)
        right_aligned_controls_layout.addLayout(office_hours_controls_layout)
        
        # Add a small spacer between Office Hours and Bonus Toggle
        right_aligned_controls_layout.addSpacing(10)

        # 3. Bonus Toggle
        bonus_layout = QtWidgets.QHBoxLayout()
        self.bonus_toggle_btn = QtWidgets.QPushButton("Global: OFF")
        self.bonus_toggle_btn.clicked.connect(self.toggle_week_bonus)
        self.bonus_toggle_btn.setCheckable(True)
        self.bonus_toggle_btn.setToolTip("Toggle bonus eligibility for the current week")
        bonus_layout.addWidget(self.bonus_toggle_btn)
        right_aligned_controls_layout.addLayout(bonus_layout)

        top_buttons_layout.addLayout(right_aligned_controls_layout)

        task_layout.addLayout(top_buttons_layout)

        # Task grid
        self.task_grid = TaskGrid(self)
        self.task_grid.set_office_hour_count_label(self.office_hour_count_label) # Pass the label to TaskGrid
        task_layout.addWidget(self.task_grid)

        # Now connect office hour buttons after task_grid is created
        self.add_oh_session_btn.clicked.connect(self.task_grid.add_office_hour_session)
        self.remove_oh_session_btn.clicked.connect(self.task_grid.remove_office_hour_session)

        # Add task area to main layout
        content_layout.addWidget(add_task_area)
        main_layout.addLayout(content_layout)
        
        # Connect signals
        self.week_widget.weekChanged.connect(self.on_week_changed)
        
        # Initial state
        self.current_week_id = None
        
        # Apply theme now that all UI elements are created
        self.apply_theme()
        
        # Update bonus button style on init
        self.update_bonus_button_style() # Initial style update
    
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
        
        # Style the bonus toggle button
        self.update_bonus_button_style()

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
        # Remove the old week_dock toggle action
        # view_menu.addAction(self.week_dock.toggleViewAction())
        
        # Add new action to open Analysis Widget as a separate window
        open_analysis_action = QtGui.QAction("Data Analysis Window", self)
        open_analysis_action.triggered.connect(self.show_analysis_widget)
        view_menu.addAction(open_analysis_action)
        
        # Add new action for toggling the custom collapsible week sidebar
        self.toggle_custom_week_sidebar_action = QtGui.QAction("Toggle Week Sidebar", self)
        self.toggle_custom_week_sidebar_action.triggered.connect(self.toggle_week_sidebar)
        view_menu.addAction(self.toggle_custom_week_sidebar_action)

    def create_dock_widgets(self):
        # This method is now empty as week_dock is no longer used
        pass

    def on_week_changed(self, week_id, week_label):
        self.current_week_id = week_id
        self.task_grid.refresh_tasks(week_id)
        
        # Refresh the week combo in analysis widget to mirror week widget changes
        self.analysis_widget.refresh_week_combo()
        
        # Update bonus button for the new week
        self.update_bonus_button_style()
        
        # Update office hour count display
        self.task_grid.update_office_hour_count_display()
        
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
    
    def toggle_week_bonus(self):
        """Toggle bonus eligibility for the current week"""
        if self.current_week_id is None:
            self.toaster_manager.show_warning("Please select a week first.", "No Week Selected", 3000)
            return
        
        # Check if global bonus is enabled first
        from core.settings.global_settings import global_settings
        if not global_settings.is_global_bonus_enabled():
            self.toaster_manager.show_warning(
                "Global bonus system is disabled. Enable it in Preferences > Global Bonus Defaults first.",
                "Global Bonus Disabled",
                5000
            )
            self.bonus_toggle_btn.setChecked(False)
            return
        
        # Get current week bonus status
        import sqlite3
        conn = sqlite3.connect("tasks.db")
        c = conn.cursor()
        c.execute("SELECT is_bonus_week FROM weeks WHERE id=?", (self.current_week_id,))
        result = c.fetchone()
        
        if result is None:
            conn.close()
            return
        
        current_bonus_status = bool(result[0])
        new_bonus_status = not current_bonus_status
        
        # Update database
        c.execute("UPDATE weeks SET is_bonus_week=? WHERE id=?", (int(new_bonus_status), self.current_week_id))
        conn.commit()
        conn.close()
        
        # Update button state and style
        self.bonus_toggle_btn.setChecked(new_bonus_status)
        self.update_bonus_button_style()
        
        # Show feedback to user
        status_text = "enabled" if new_bonus_status else "disabled"
        self.toaster_manager.show_info(
            f"Bonus {status_text} for current week",
            "Bonus Status Updated",
            3000
        )
        
        # Refresh analysis to reflect bonus changes
        self.refresh_analysis()
    
    def update_bonus_button_style(self):
        """Update the bonus button styling based on current state"""
        if not hasattr(self, 'bonus_toggle_btn'):
            return
            
        # Check if global bonus is enabled first
        from core.settings.global_settings import global_settings
        if not global_settings.is_global_bonus_enabled():
            # Global bonus disabled
            self.bonus_toggle_btn.setText("Global: DISABLED")
            self.bonus_toggle_btn.setStyleSheet(
                "QPushButton { background-color: #555555; color: white; border-radius: 4px; }"
                "QPushButton:hover { background-color: #666666; }"
            )
            self.bonus_toggle_btn.setEnabled(False)
            self.bonus_toggle_btn.setToolTip("Global bonus system is disabled. Enable in Preferences first.")
            return
        
        # Global bonus is enabled, check current week status
        is_bonus_week = False
        if self.current_week_id is not None:
            import sqlite3
            conn = sqlite3.connect("tasks.db")
            c = conn.cursor()
            c.execute("SELECT is_bonus_week FROM weeks WHERE id=?", (self.current_week_id,))
            result = c.fetchone()
            conn.close()
            if result:
                is_bonus_week = bool(result[0])
        
        self.bonus_toggle_btn.setEnabled(True)
        self.bonus_toggle_btn.setChecked(is_bonus_week)
        
        if is_bonus_week:
            self.bonus_toggle_btn.setText("Global: ON")
            self.bonus_toggle_btn.setStyleSheet(
                "QPushButton { background-color: #007bff; color: white; border-radius: 4px; }" # A shade of blue
                "QPushButton:hover { background-color: #0069d9; }"
                "QPushButton:checked { background-color: #0056b3; }"
            )
            self.bonus_toggle_btn.setToolTip("This week uses global bonus settings. Click to disable.")
        else:
            self.bonus_toggle_btn.setText("Global: OFF")
            self.bonus_toggle_btn.setStyleSheet(
                "QPushButton { background-color: #6c757d; color: white; border-radius: 4px; }" # A shade of grey
                "QPushButton:hover { background-color: #5a6268; }"
                "QPushButton:checked { background-color: #545b62; }"
            )
            self.bonus_toggle_btn.setToolTip("This week does not use bonus. Click to enable global bonus settings.")
    
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
                # Refresh the week combo in analysis widget to mirror week widget changes
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
        self.collapsible_week_sidebar.toggle()

    def show_preferences(self):
        """Show the preferences dialog"""
        options_dialog = OptionsDialog(self)
        options_dialog.exec()
    
    def closeEvent(self, event):
        """Handle application close event to clean up resources"""
        try:
            # Clean up TaskGrid diagnostics
            if hasattr(self, 'task_grid') and self.task_grid:
                self.task_grid.cleanup_diagnostics()
            
            # Accept the close event
            event.accept()
        except Exception as e:
            print(f"Error during application cleanup: {e}")
            event.accept()

# Main application entry point
if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationDisplayName("") # Set empty application display name

    # Check for first startup and show wizard if needed
    from core.settings.global_settings import global_settings
    if global_settings.is_first_startup():
        from ui.first_startup_wizard import FirstStartupWizard
        wizard = FirstStartupWizard()
        if wizard.exec() != QtWidgets.QDialog.Accepted:
            # User canceled setup, exit application
            sys.exit(0)

    main_window = MainWindow()
    main_window.show()
    sys.exit(app.exec())

