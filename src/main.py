import sys
import os
from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCore import QPropertyAnimation, QTimer
import pathlib
import logging

# Startup optimization imports
from core.optimization.startup_monitor import get_startup_monitor, monitor_startup_phase
from core.optimization.lazy_imports import setup_scientific_libraries, preload_critical_modules

# Removed debug logging - no longer needed

# Import our new components
from ui.week_widget import WeekWidget
from ui.qml_task_grid import QMLTaskGrid
from analysis.analysis_widget import AnalysisWidget
from core.db.db_schema import run_all_migrations
from core.db.export_data import export_week_to_csv, export_all_weeks_to_excel
from core.db.import_data import main_import
from core.utils.toaster import ToasterManager
from ui.theme_manager import ThemeManager
from ui.options import OptionsDialog
from ui.collapsible_week_sidebar import CollapsibleWeekSidebar
from core.settings.global_settings import get_icon_path

# Import Data Service Layer components
from core.services import WeekDAO, DataServiceError

# Import Event Bus components
from core.events import get_event_bus, EventType

# Import DataService
from core.services.data_service import DataService

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
    @monitor_startup_phase("MainWindow Initialization", "Initialize main window and core components", critical=True)
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Auditor Helper") # Set proper title instead of empty string
        
        # Initialize logger first
        self.logger = logging.getLogger(__name__)
        
        # Set window icon
        try:
            icon_path = get_icon_path('app_icon.ico')
            self.setWindowIcon(QtGui.QIcon(icon_path))
        except Exception as e:
            pass  # Ignore icon errors
        
        self.resize(1200, 800)
        
        # Initialize the database and run all migrations
        self._run_optimized_migrations()
        
        # Initialize Event Bus
        self.event_bus = get_event_bus()
        
        # Initialize toaster manager
        self.toaster_manager = ToasterManager(self)
        
        # Set default dark mode
        self.dark_mode = True
        
        # Initialize ThemeManager
        self.theme_manager = ThemeManager()
        
        # Initialize Data Access Objects
        self.week_dao = WeekDAO()
        
        # Initialize UI state
        self.current_week_id = None
        self.bonus_toggle_btn = None
        
        # Initialize Redis and DataService
        self._init_redis_and_data_service()
        
        # Setup lazy imports for scientific libraries (background loading)
        self._setup_lazy_imports()
        
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
        # Removed explicit width constraints - let the sidebar manage its own size
        
        # Create a content widget that will contain both sidebar and task area
        content_widget = QtWidgets.QWidget()
        content_widget.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        content_layout = QtWidgets.QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(5)
        content_layout.addWidget(self.collapsible_week_sidebar, 0)  # No stretch - sidebar takes its preferred size
        
        # Initialize analysis widget lazily - only create when needed
        self.analysis_widget = None
        
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

        # Task grid (QML-based)
        self.task_grid = QMLTaskGrid(self)
        self.task_grid.set_office_hour_count_label(self.office_hour_count_label) # Pass the label to TaskGrid
        task_layout.addWidget(self.task_grid)

        # Now connect office hour buttons after task_grid is created
        self.add_oh_session_btn.clicked.connect(self.task_grid.add_office_hour_session)
        self.remove_oh_session_btn.clicked.connect(self.task_grid.remove_office_hour_session)

        # Add task area to content layout with stretch factor
        content_layout.addWidget(add_task_area, 1)  # Stretch factor 1 - fills remaining space
        
        # Add the content widget to the main layout
        main_layout.addWidget(content_widget, 1)  # Allow content to expand
        
        # Connect signals - maintain backward compatibility
        self.week_widget.weekChanged.connect(self.on_week_changed)
        
        # Connect to Event Bus events
        self.setup_event_bus_listeners()
        
        # Initial state
        self.current_week_id = None
        
        # Apply theme now that all UI elements are created
        self.apply_theme()
        
        # Update bonus button style on init
        self.update_bonus_button_style() # Initial style update
        
        # Set up timer to update bonus button style periodically
        self.bonus_update_timer = QTimer()
        self.bonus_update_timer.timeout.connect(self.update_bonus_button_style)
        self.bonus_update_timer.start(5000)  # Update every 5 seconds
    
    def _init_redis_and_data_service(self):
        """Initialize multi-tier cache system (no Redis dependencies)"""
        try:
            # Use FastDataService with multi-tier cache (no network dependencies)
            from core.optimization.multi_tier_cache import FastDataService
            self.logger.info("Initializing multi-tier cache system")
            self.data_service = FastDataService.get_instance()
            self.logger.info("✅ Multi-tier cache system initialized - Memory + SQLite tiers active")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize multi-tier cache: {e}")
            raise
    
    def get_cache_statistics(self):
        """Get current cache performance statistics"""
        if hasattr(self, 'data_service'):
            return self.data_service.get_performance_stats()
        return {"multi_tier_cache_active": False}
    
    def clear_application_cache(self):
        """Clear all application cache"""
        if hasattr(self, 'data_service') and hasattr(self.data_service, 'cache_manager'):
            self.data_service.cache_manager.clear_all_cache()
            self.logger.info("🧹 Application cache cleared")
            
            # Refresh UI components
            if hasattr(self, 'refresh_analysis'):
                self.refresh_analysis()
    
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

    def setup_event_bus_listeners(self):
        """Set up event bus listeners for application-wide events"""
        # Week-related events
        self.event_bus.connect_handler(EventType.WEEK_CHANGED, self.on_week_changed_event)
        self.event_bus.connect_handler(EventType.WEEK_CREATED, self.on_week_created_event)
        self.event_bus.connect_handler(EventType.WEEK_DELETED, self.on_week_deleted_event)
        
        # Task-related events
        self.event_bus.connect_handler(EventType.TASK_CREATED, self.on_task_created_event)
        self.event_bus.connect_handler(EventType.TASK_UPDATED, self.on_task_updated_event)
        self.event_bus.connect_handler(EventType.TASK_DELETED, self.on_task_deleted_event)
        self.event_bus.connect_handler(EventType.TASK_SELECTION_CHANGED, self.on_task_selection_changed_event)
        
        # Timer-related events
        self.event_bus.connect_handler(EventType.TIMER_STARTED, self.on_timer_started_event)
        self.event_bus.connect_handler(EventType.TIMER_STOPPED, self.on_timer_stopped_event)
        self.event_bus.connect_handler(EventType.TIMER_UPDATED, self.on_timer_updated_event)
        
        # UI-related events
        self.event_bus.connect_handler(EventType.UI_REFRESH_REQUESTED, self.on_ui_refresh_requested_event)
        self.event_bus.connect_handler(EventType.DELETE_BUTTON_UPDATE_REQUESTED, self.on_delete_button_update_requested_event)

    def on_week_changed_event(self, event_data):
        """Handle week changed events from event bus"""
        week_id = event_data.data.get('week_id')
        week_label = event_data.data.get('week_label')
        
        # Emit event to notify other components that need to update
        self.event_bus.emit_event(
            EventType.UI_REFRESH_REQUESTED,
            {'reason': 'week_changed', 'week_id': week_id, 'week_label': week_label},
            'MainWindow'
        )
        
        # Update analysis widget (only if it exists)
        if self.analysis_widget is not None:
            self.analysis_widget.refresh_week_combo()
        
        # Update bonus button
        self.update_bonus_button_style()

    def on_week_created_event(self, event_data):
        """Handle week created events from event bus"""
        week_label = event_data.data.get('week_label')
        
        # Refresh analysis widget week combo (only if it exists)
        if self.analysis_widget is not None:
            self.analysis_widget.refresh_week_combo()
        
        # Show notification if not already shown by the source component
        if event_data.source != 'MainWindow':
            self.toaster_manager.show_info(f"Week '{week_label}' created", "Week Created", 3000)

    def on_week_deleted_event(self, event_data):
        """Handle week deleted events from event bus"""
        week_label = event_data.data.get('week_label')
        
        # Refresh analysis widget week combo (only if it exists)
        if self.analysis_widget is not None:
            self.analysis_widget.refresh_week_combo()
        
        # Show notification if not already shown by the source component
        if event_data.source != 'MainWindow':
            self.toaster_manager.show_info(f"Week '{week_label}' deleted", "Week Deleted", 3000)

    def on_task_created_event(self, event_data):
        """Handle task created events from event bus"""
        # Refresh analysis if needed
        self.refresh_analysis()

    def on_task_updated_event(self, event_data):
        """Handle task updated events from event bus"""
        # Refresh analysis if needed
        self.refresh_analysis()

    def on_task_deleted_event(self, event_data):
        """Handle task deleted events from event bus"""
        # Refresh analysis if needed
        self.refresh_analysis()

    def on_task_selection_changed_event(self, event_data):
        """Handle task selection changed events from event bus"""
        # Update delete button
        self.update_delete_button()

    def on_timer_started_event(self, event_data):
        """Handle timer started events from event bus"""
        # Could show notification or update UI state
        pass

    def on_timer_stopped_event(self, event_data):
        """Handle timer stopped events from event bus"""
        # Refresh analysis to reflect time updates
        self.refresh_analysis()

    def on_timer_updated_event(self, event_data):
        """Handle timer updated events from event bus"""
        # Could update UI to show current timer state
        pass

    def on_ui_refresh_requested_event(self, event_data):
        """Handle UI refresh requests from event bus"""
        reason = event_data.data.get('reason')
        
        if reason == 'week_changed':
            week_id = event_data.data.get('week_id')
            week_label = event_data.data.get('week_label')
            
            # Update current week tracking
            self.current_week_id = week_id
            
            # Refresh task grid
            self.task_grid.refresh_tasks(week_id)
            
            # Update office hour count display
            self.task_grid.update_office_hour_count_display()
            
            # Update window title
            if week_label:
                self.setWindowTitle(f"Auditor Helper - {week_label}")
            else:
                self.setWindowTitle("Auditor Helper")

    def on_delete_button_update_requested_event(self, event_data):
        """Handle delete button update requests from event bus"""
        self.update_delete_button()

    def on_week_changed(self, week_id, week_label):
        self.current_week_id = week_id
        self.task_grid.refresh_tasks(week_id)
        
        # Refresh the week combo in analysis widget to mirror week widget changes (only if it exists)
        if self.analysis_widget is not None:
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
        try:
            week_data = self.week_dao.get_week_by_id(self.current_week_id)
            if week_data:
                current_bonus_status = bool(week_data.get('is_bonus_week', 0))
                new_bonus_status = not current_bonus_status
                
                # Update database
                success = self.week_dao.update_week(
                    self.current_week_id, 
                    is_bonus_week=1 if new_bonus_status else 0
                )
                
                if success:
                    self.logger.info(f"Updated week {self.current_week_id} bonus status to {new_bonus_status}")
                    
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
                else:
                    self.logger.error(f"Failed to update week {self.current_week_id} bonus status")
                    self.toaster_manager.show_error(
                        "Failed to update bonus status",
                        "Update Failed",
                        3000
                    )
        except DataServiceError as e:
            self.logger.error(f"Error toggling week bonus: {e}")
            self.toaster_manager.show_error(
                f"Database error: {str(e)}",
                "Error",
                5000
            )
    
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
            try:
                week_data = self.week_dao.get_week_by_id(self.current_week_id)
                if week_data:
                    is_bonus_week = bool(week_data.get('is_bonus_week', 0))
            except DataServiceError as e:
                self.logger.error(f"Error getting week bonus status: {e}")
                # Continue with default (False) value
        
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
        """Refresh analysis widget if it exists"""
        if self.analysis_widget is not None:
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
                # Refresh the week combo in analysis widget if it exists
                if self.analysis_widget is not None:
                    self.analysis_widget.refresh_week_combo()
                if self.current_week_id:
                    self.task_grid.refresh_tasks(self.current_week_id)
                
                # Show success toaster
                self.toaster_manager.show_info(f"Data import from {filename} complete.", "Import Complete", 5000)
            except Exception as e:
                # Show error toaster
                self.toaster_manager.show_error(f"Failed to import data: {str(e)}", "Import Failed", 5000)

    def show_analysis_widget(self):
        """Show the AnalysisWidget as a separate window (lazy initialization)"""
        if self.analysis_widget is None:
            # Create the AnalysisWidget only when first needed
            self.analysis_widget = AnalysisWidget()
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
            
            # Multi-tier cache cleanup (no Redis dependencies)
            try:
                if hasattr(self, 'data_service') and hasattr(self.data_service, 'cache_manager'):
                    # Clean shutdown of cache system
                    self.logger.info("Cleaning up multi-tier cache system")
            except Exception as cache_error:
                self.logger.error(f"Error cleaning up cache: {cache_error}")
            
            # Accept the close event
            event.accept()
        except Exception as e:
            print(f"Error during application cleanup: {e}")
            event.accept()
    
    @monitor_startup_phase("Database Migrations", "Run database schema migrations", critical=True)
    def _run_optimized_migrations(self):
        """Run database migrations with Phase 2 optimizations"""
        try:
            from core.optimization.database_optimizer import optimize_database_startup
            from core.optimization.startup_profiler import profile_phase
            
            with profile_phase("Database Optimization"):
                # Phase 2: Use optimized database system
                self.db_manager = optimize_database_startup()
                self.logger.info("Phase 2: Database optimizations applied")
                self.logger.info("✅ Connection pooling, WAL mode, and performance settings active")
                
        except Exception as e:
            self.logger.error(f"Phase 2 database optimization error: {e}")
            # Fallback to original migrations
            self.logger.info("🔄 Falling back to original migration system")
            try:
                run_all_migrations()
                self.logger.info("✅ Database migrations completed successfully")
            except Exception as fallback_error:
                self.logger.error(f"❌ Database migration failed: {fallback_error}")
                raise
    
    def _setup_lazy_imports(self):
        """Setup lazy imports for scientific libraries"""
        try:
            # Setup lazy imports for heavy scientific libraries
            lazy_libraries = setup_scientific_libraries()
            
            # Start background preloading of critical modules
            preload_critical_modules()
            
            # Mark optimization as active
            monitor = get_startup_monitor()
            monitor.set_optimization_flags(lazy_imports=True, cache_system=False)
            
            self.logger.info(f"Lazy imports configured for {len(lazy_libraries)} scientific libraries")
            
        except Exception as e:
            self.logger.warning(f"⚠️  Lazy import setup failed: {e}")
            # Continue without lazy imports - not critical for functionality

# Main application entry point
if __name__ == "__main__":
    # Start Phase 2 startup performance monitoring
    from core.optimization.startup_profiler import get_startup_profiler, print_startup_report
    
    profiler = get_startup_profiler()
    
    # Start startup performance monitoring
    startup_monitor = get_startup_monitor()
    startup_monitor.start_session("main_startup")
    
    startup_monitor.start_phase("Application Setup", "Initialize Qt application and environment", critical=True)
    
    # Set environment variable to force Qt style before creating QApplication
    os.environ['QT_QUICK_CONTROLS_STYLE'] = 'Material'
    
    app = QtWidgets.QApplication(sys.argv)
    app.setApplicationDisplayName("") # Set empty application display name
    
    # Set Qt style to Material to enable ScrollBar customization
    app.setStyle("Material")
    
    startup_monitor.finish_phase("Application Setup")

    # Check for first startup and show wizard if needed
    startup_monitor.start_phase("First Startup Check", "Check if first startup wizard is needed")
    
    from core.settings.global_settings import global_settings
    if global_settings.is_first_startup():
        from ui.first_startup_wizard import FirstStartupWizard
        wizard = FirstStartupWizard()
        if wizard.exec() != QtWidgets.QDialog.Accepted:
            # User canceled setup, exit application
            sys.exit(0)
    
    startup_monitor.finish_phase("First Startup Check")
    
    # Create and show main window
    startup_monitor.start_phase("Main Window Creation", "Create and display main application window", critical=True)
    
    main_window = MainWindow()
    main_window.show()
    
    startup_monitor.finish_phase("Main Window Creation")
    
    # Finish startup monitoring
    startup_monitor.finish_session()
    
    # Generate simple startup summary
    report = startup_monitor.get_performance_report()
    if 'error' not in report:
        latest_time = report['timing_analysis']['latest_time']
        grade = report['summary']['current_performance_grade']
        print(f"\nAuditor Helper started successfully in {latest_time:.2f}s (Performance: {grade})")
    else:
        print("\nAuditor Helper started successfully")
    
    sys.exit(app.exec())

