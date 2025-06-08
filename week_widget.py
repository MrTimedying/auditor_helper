import sqlite3
import os
import shutil
import sys
from datetime import datetime
from PySide6 import QtCore, QtWidgets

DB_FILE = "tasks.db"

def is_production():
    """Check if running in production (bundled) environment"""
    return getattr(sys, 'frozen', False)

class WeekWidget(QtWidgets.QWidget):
    weekChanged = QtCore.Signal(int, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Weeks")
        self.main_window = parent  # Store reference to main window
        
        # Allow this widget to be undocked/floated
        self.setWindowFlags(QtCore.Qt.Window)
        
        # Apply dark theme styling
        self.setStyleSheet(self.get_dark_stylesheet())
        
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
    
    def get_dark_stylesheet(self):
        """Return dark theme stylesheet for week widget"""
        return """
        QWidget {
            background-color: #2a2b2a;
            color: #D6D6D6;
            font-size: 11px;
        }
        
        QListWidget {
            background-color: #2a2b2a;
            color: #D6D6D6;
            border: 1px solid #1f201f;
            border-radius: 4px;
            font-size: 11px;
        }
        
        QListWidget::item {
            padding: 4px;
            border-radius: 2px;
            margin: 1px;
        }
        
        QListWidget::item:selected {
            background-color: #33342E;
            color: #D6D6D6;
        }
        
        QPushButton {
            background-color: #2a2b2a;
            color: #D6D6D6;
            border: 1px solid #1f201f;
            border-radius: 4px;
            padding: 1px 2px;
            font-size: 11px;
            min-height: 16px;
        }
        
        QPushButton:hover {
            background-color: #33342E;
        }
        
        QPushButton:pressed {
            background-color: #1f201f;
        }
        
        QDateEdit {
            background-color: #2a2b2a;
            color: #D6D6D6;
            border: 1px solid #1f201f;
            border-radius: 2px;
            padding: 3px;
            font-size: 11px;
        }
        
        QLabel {
            color: #D6D6D6;
            font-size: 11px;
        }
        """
    
    def selection_changed(self):
        week_id, week_label = self.current_week_id()
        if week_id is not None:
            self.weekChanged.emit(week_id, week_label)
    
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
        # Create a database backup before adding a new week (only in production)
        self.create_db_backup()
        
        start_date = self.start_date.date().toString("dd/MM/yyyy")
        end_date = self.end_date.date().toString("dd/MM/yyyy")
        week_label = f"{start_date} - {end_date}"
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO weeks (week_label) VALUES (?)", (week_label,))
            conn.commit()
            
            # Show success notification via main window toaster manager
            if hasattr(self.main_window, 'toaster_manager'):
                self.main_window.toaster_manager.show_info(f"Created new week: {week_label}", "Week Added", 3000)
        except sqlite3.IntegrityError:
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
        finally:
            conn.close()
        
        self.refresh_weeks()
        for i in range(self.week_list.count()):
            if self.week_list.item(i).text() == week_label:
                self.week_list.setCurrentRow(i)
                break
        
        # Refresh the analysis widget's week combo to mirror the changes
        if hasattr(self.main_window, 'analysis_widget'):
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
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("DELETE FROM weeks WHERE id=?", (week_id,))
        conn.commit()
        conn.close()
        
        # Show deletion notification via main window toaster manager
        if hasattr(self.main_window, 'toaster_manager'):
            self.main_window.toaster_manager.show_info(
                f"Week '{week_label}' deleted", "Week Deleted", 3000
            )
        
        self.refresh_weeks()
        if self.week_list.count() > 0:
            self.week_list.setCurrentRow(0)
        else:
            self.weekChanged.emit(None, None)
        
        # Refresh the analysis widget's week combo to mirror the changes
        if hasattr(self.main_window, 'analysis_widget'):
            self.main_window.analysis_widget.refresh_week_combo()
    
    def get_weeks(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, week_label FROM weeks")
        weeks = c.fetchall()
        conn.close()
        
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