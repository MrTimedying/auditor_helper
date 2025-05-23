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
        
        self.new_week_btn = QtWidgets.QPushButton("Add Week")
        self.del_week_btn = QtWidgets.QPushButton("Delete Week")
        
        layout.addWidget(self.new_week_btn)
        layout.addWidget(self.del_week_btn)
        layout.addStretch()
        
        # Connect signals
        self.week_list.itemSelectionChanged.connect(self.selection_changed)
        self.new_week_btn.clicked.connect(self.add_week)
        self.del_week_btn.clicked.connect(self.delete_week)
        
        self.weeks = []
        self.refresh_weeks()
    
    def selection_changed(self):
        week_id, week_label = self.current_week_id()
        if week_id is not None:
            self.weekChanged.emit(week_id, week_label)
    
    def refresh_weeks(self):
        self.week_list.clear()
        self.weeks = self.get_weeks()
        for week_id, week_label in self.weeks:
            self.week_list.addItem(week_label)
    
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
    
    def get_weeks(self):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, week_label FROM weeks ORDER BY week_label")
        weeks = c.fetchall()
        conn.close()
        return weeks 