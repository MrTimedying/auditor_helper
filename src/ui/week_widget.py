import sqlite3
import os
import shutil
import sys
from datetime import datetime
from PySide6 import QtCore, QtWidgets
from core.settings.global_settings import global_settings

# Data Service Layer imports
from core.services.data_service import DataService, DataServiceError
from core.services.week_dao import WeekDAO

# Event Bus imports
from core.events import get_event_bus, EventType

DB_FILE = "tasks.db"

def is_production():
    """Check if running in production (bundled) environment"""
    return getattr(sys, 'frozen', False)

class WeekWidget(QtWidgets.QWidget):
    weekChanged = QtCore.Signal(int, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize Event Bus
        self.event_bus = get_event_bus()
        
        # Initialize Data Service Layer
        try:
            self.data_service = DataService.get_instance()
            self.week_dao = WeekDAO(self.data_service)
        except DataServiceError as e:
            print(f"Warning: Failed to initialize Data Service Layer: {e}")
            # Fallback to direct SQLite if needed
            self.data_service = None
            self.week_dao = None
        
        # Layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Week list
        self.week_list = QtWidgets.QListWidget()
        layout.addWidget(self.week_list)
        
        # Week controls
        self.start_date = QtWidgets.QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QtCore.QDate.currentDate())
        
        self.end_date = QtWidgets.QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QtCore.QDate.currentDate())
        
        date_layout = QtWidgets.QHBoxLayout()
        date_layout.addWidget(QtWidgets.QLabel("From:"))
        date_layout.addWidget(self.start_date)
        date_layout.addWidget(QtWidgets.QLabel("To:"))
        date_layout.addWidget(self.end_date)
        layout.addLayout(date_layout)
        
        # Create buttons in a horizontal layout
        buttons_layout = QtWidgets.QHBoxLayout()
        
        self.new_week_btn = QtWidgets.QPushButton("Add Week")
        self.del_week_btn = QtWidgets.QPushButton("Delete Week")
        self.sort_weeks_btn = QtWidgets.QPushButton("Sort Weeks")
        
        buttons_layout.addWidget(self.new_week_btn)
        buttons_layout.addWidget(self.del_week_btn)
        buttons_layout.addWidget(self.sort_weeks_btn)
        
        layout.addLayout(buttons_layout)
        layout.addStretch()
        
        # Connect signals
        self.week_list.itemSelectionChanged.connect(self.selection_changed)
        self.new_week_btn.clicked.connect(self.add_week)
        self.del_week_btn.clicked.connect(self.delete_week)
        self.sort_weeks_btn.clicked.connect(self.sort_weeks)
        
        self.weeks = []
        self.refresh_weeks()
    
    def selection_changed(self):
        week_id, week_label = self.current_week_id()
        if week_id is not None:
            # Emit traditional Qt signal for backward compatibility
            self.weekChanged.emit(week_id, week_label)
            
            # Emit event through event bus
            self.event_bus.emit_event(
                EventType.WEEK_CHANGED,
                {
                    'week_id': week_id,
                    'week_label': week_label
                },
                'WeekWidget'
            )
    
    def refresh_weeks(self):
        self.week_list.clear()
        self.weeks = self.get_weeks()
        for week_id, week_label in self.weeks:
            self.week_list.addItem(week_label)
    
    def sort_weeks(self):
        """Sort weeks chronologically and preserve current selection"""
        # Remember current selection
        current_week_id, current_week_label = self.current_week_id()
        
        # Refresh the weeks (which sorts them)
        self.refresh_weeks()
        
        # Restore selection if it existed
        if current_week_id is not None:
            self.select_week_by_id(current_week_id)
        
        # Show notification that weeks were sorted
        if hasattr(self.main_window, 'toaster_manager'):
            self.main_window.toaster_manager.show_info("Weeks sorted chronologically", "Weeks Sorted", 2000)
    
    def current_week_id(self):
        row = self.week_list.currentRow()
        if row < 0 or row >= len(self.weeks):
            return None, None
        return self.weeks[row]
    
    def select_week_by_id(self, week_id):
        for idx, (wid, _) in enumerate(self.weeks):
            if wid == week_id:
                self.week_list.setCurrentRow(idx)
                break
    
    def create_db_backup(self):
        """Create a backup of the database only in production environment"""
        # Only create backups in production environment
        if not is_production() or not os.path.exists(DB_FILE):
            return None
        
        # Create backups directory if it doesn't exist
        backup_dir = os.path.join(os.path.dirname(os.path.abspath(DB_FILE)), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        
        # Create a backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        backup_file = os.path.join(backup_dir, f"tasks_backup_{timestamp}.db")
        
        try:
            shutil.copy2(DB_FILE, backup_file)
            print(f"Created database backup: {backup_file}")
            return backup_file
        except Exception as e:
            print(f"Failed to create backup: {e}")
            return None
    
    def add_week(self):
        # Validate week duration if enforcement is enabled
        if global_settings.should_enforce_week_duration():
            start_date_py = self.start_date.date().toPython()
            end_date_py = self.end_date.date().toPython()
            duration_days = (end_date_py - start_date_py).days + 1  # +1 to include both start and end days
            
            if duration_days != 7:
                # Show error message
                if hasattr(self.main_window, 'toaster_manager'):
                    self.main_window.toaster_manager.show_warning(
                        f"Week duration must be exactly 7 days. Current selection is {duration_days} days.",
                        "Invalid Week Duration",
                        5000
                    )
                else:
                    QtWidgets.QMessageBox.warning(
                        self, "Invalid Week Duration",
                        f"Week duration must be exactly 7 days.\nCurrent selection is {duration_days} days.\n\nPlease adjust your date range."
                    )
                return
        
        # Create a database backup before adding a new week (only in production)
        self.create_db_backup()
        
        start_date_py = self.start_date.date().toPython()
        end_date_py = self.end_date.date().toPython()
        
        start_date = self.start_date.date().toString("dd/MM/yyyy")
        end_date = self.end_date.date().toString("dd/MM/yyyy")
        week_label = f"{start_date} - {end_date}"
        
        # Calculate the start and end day of week from the selected dates
        # Python weekday(): Monday=0, Tuesday=1, ..., Sunday=6
        # We'll store as: Monday=1, Tuesday=2, ..., Sunday=7 to match global settings format
        week_start_day = start_date_py.weekday() + 1  # Convert to 1-7 format
        week_end_day = end_date_py.weekday() + 1     # Convert to 1-7 format
        
        # Set start/end hours to match global defaults initially
        global_defaults = global_settings.get_default_week_settings()
        week_start_hour = global_defaults['week_start_hour']
        week_end_hour = global_defaults['week_end_hour']
        
        try:
            # Use Data Service Layer for week creation
            if self.week_dao:
                week_data = {
                    'week_label': week_label,
                    'week_start_day': week_start_day,
                    'week_start_hour': week_start_hour,
                    'week_end_day': week_end_day,
                    'week_end_hour': week_end_hour,
                    'is_custom_duration': True  # Mark as custom duration since we're setting specific days
                }
                
                new_week_id = self.week_dao.create_week(week_data)
                
                # Emit week created event
                self.event_bus.emit_event(
                    EventType.WEEK_CREATED,
                    {
                        'week_id': new_week_id,
                        'week_label': week_label,
                        'week_data': week_data
                    },
                    'WeekWidget'
                )
                
                # Show success notification via main window toaster manager
                if hasattr(self.main_window, 'toaster_manager'):
                    self.main_window.toaster_manager.show_info(f"Created new week: {week_label}", "Week Added", 3000)
            else:
                # Fallback to direct SQLite if Data Service Layer not available
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("""
                    INSERT INTO weeks (
                        week_label, 
                        week_start_day, week_start_hour, 
                        week_end_day, week_end_hour, 
                        is_custom_duration
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    week_label, 
                    week_start_day, week_start_hour,
                    week_end_day, week_end_hour,
                    True  # Mark as custom duration since we're setting specific days
                ))
                conn.commit()
                conn.close()
                
                # Show success notification via main window toaster manager
                if hasattr(self.main_window, 'toaster_manager'):
                    self.main_window.toaster_manager.show_info(f"Created new week: {week_label}", "Week Added", 3000)
                    
        except (DataServiceError, sqlite3.IntegrityError) as e:
            # Handle duplicate week error
            error_msg = str(e).lower()
            if 'unique' in error_msg or 'duplicate' in error_msg or 'integrity' in error_msg:
                # Show warning notification via main window toaster manager
                if hasattr(self.main_window, 'toaster_manager'):
                    self.main_window.toaster_manager.show_warning(
                        f"A week with the label '{week_label}' already exists.", "Duplicate Week", 5000
                    )
                else:
                    # Fallback to traditional dialog if toaster not available
                    QtWidgets.QMessageBox.warning(
                        self, "Duplicate Week", 
                        f"A week with the label '{week_label}' already exists."
                    )
            else:
                # Handle other database errors
                print(f"Error creating week: {e}")
                if hasattr(self.main_window, 'toaster_manager'):
                    self.main_window.toaster_manager.show_error(
                        f"Failed to create week: {e}", "Database Error", 5000
                    )
        
        self.refresh_weeks()
        for i in range(self.week_list.count()):
            if self.week_list.item(i).text() == week_label:
                self.week_list.setCurrentRow(i)
                break
        
        # Refresh the analysis widget's week combo to mirror the changes
        if hasattr(self.main_window, 'analysis_widget') and self.main_window.analysis_widget is not None:
            self.main_window.analysis_widget.refresh_week_combo()
    
    def delete_week(self):
        week_id, week_label = self.current_week_id()
        if week_id:
            # If we have access to main window toaster manager, use it for confirmation
            if hasattr(self.main_window, 'toaster_manager'):
                self.main_window.toaster_manager.show_question(
                    "Are you sure you want to delete this week and all its tasks?",
                    "Confirm Deletion",
                    self.confirm_delete_week
                )
            else:
                # Fallback to traditional dialog if toaster not available
                reply = QtWidgets.QMessageBox.question(
                    self, 'Confirm Deletion',
                    "Are you sure you want to delete this week and all its tasks?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
                    QtWidgets.QMessageBox.No
                )
                
                if reply == QtWidgets.QMessageBox.Yes:
                    self.do_delete_week()
    
    def confirm_delete_week(self, result):
        """Callback for toaster confirmation"""
        if result:
            self.do_delete_week()
    
    def do_delete_week(self):
        """Perform the actual week deletion after confirmation"""
        week_id, week_label = self.current_week_id()
        
        if not week_id:
            return
            
        # Create a backup before deleting (only in production)
        self.create_db_backup()
        
        try:
            # Use Data Service Layer for week deletion
            if self.week_dao:
                self.week_dao.delete_week(week_id)
            else:
                # Fallback to direct SQLite if Data Service Layer not available
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("DELETE FROM weeks WHERE id=?", (week_id,))
                conn.commit()
                conn.close()
            
            # Emit week deleted event
            self.event_bus.emit_event(
                EventType.WEEK_DELETED,
                {
                    'week_id': week_id,
                    'week_label': week_label
                },
                'WeekWidget'
            )
            
            # Show deletion notification via main window toaster manager
            if hasattr(self.main_window, 'toaster_manager'):
                self.main_window.toaster_manager.show_info(
                    f"Week '{week_label}' deleted", "Week Deleted", 3000
                )
                
        except DataServiceError as e:
            print(f"Error deleting week: {e}")
            if hasattr(self.main_window, 'toaster_manager'):
                self.main_window.toaster_manager.show_error(
                    f"Failed to delete week: {e}", "Database Error", 5000
                )
            return
        
        self.refresh_weeks()
        if self.week_list.count() > 0:
            self.week_list.setCurrentRow(0)
        else:
            # Emit traditional Qt signal for backward compatibility
            self.weekChanged.emit(None, None)
            
            # Emit event through event bus
            self.event_bus.emit_event(
                EventType.WEEK_CHANGED,
                {
                    'week_id': None,
                    'week_label': None
                },
                'WeekWidget'
            )
        
        # Refresh the analysis widget's week combo to mirror the changes
        if hasattr(self.main_window, 'analysis_widget') and self.main_window.analysis_widget is not None:
            self.main_window.analysis_widget.refresh_week_combo()
    
    def get_weeks(self):
        try:
            # Use Data Service Layer for week retrieval
            if self.week_dao:
                weeks_data = self.week_dao.get_all_weeks()
                # Convert to tuple format for compatibility with existing logic
                weeks = [(week['id'], week['week_label']) for week in weeks_data]
            else:
                # Fallback to direct SQLite if Data Service Layer not available
                conn = sqlite3.connect(DB_FILE)
                c = conn.cursor()
                c.execute("SELECT id, week_label FROM weeks")
                weeks = c.fetchall()
                conn.close()
        except DataServiceError as e:
            print(f"Error retrieving weeks: {e}")
            # Return empty list on error
            weeks = []
        
        # Sort weeks chronologically by parsing the start date from week_label
        def parse_start_date(week_tuple):
            week_id, week_label = week_tuple
            try:
                # Extract start date from format "dd/MM/yyyy - dd/MM/yyyy"
                start_date_str = week_label.split(" - ")[0]
                
                # Try parsing multiple date formats
                date_formats = ["%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"]
                
                for fmt in date_formats:
                    try:
                        return datetime.strptime(start_date_str, fmt)
                    except ValueError:
                        continue # Try next format if this one fails
                
                # If no format matched, fall back to a very old date and print a warning
                print(f"Warning: Could not parse date from week label '{week_label}'. Using default date.")
                return datetime(1900, 1, 1)
            except (ValueError, IndexError, AttributeError) as e:
                # If splitting or other initial operations fail, it's a completely malformed label
                print(f"Warning: Malformed week label '{week_label}'. Error: {e}. Using default date.")
                return datetime(1900, 1, 1)
        
        # Sort by parsed start date
        weeks.sort(key=parse_start_date)
        return weeks 