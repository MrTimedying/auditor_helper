import sqlite3
from datetime import datetime
from PySide6 import QtCore, QtWidgets

DB_FILE = "tasks.db"

class WeekWidget(QtWidgets.QWidget):
    weekChanged = QtCore.Signal(int, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Weeks")
        
        # Allow this widget to be undocked/floated
        self.setWindowFlags(QtCore.Qt.Window)
        
        # Layout
        layout = QtWidgets.QVBoxLayout(self)
        
        # Week list
        self.week_list = QtWidgets.QListWidget()
        layout.addWidget(QtWidgets.QLabel("Weeks"))
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
    
    def add_week(self):
        start_date = self.start_date.date().toString("dd/MM/yyyy")
        end_date = self.end_date.date().toString("dd/MM/yyyy")
        week_label = f"{start_date} - {end_date}"
        
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute("INSERT INTO weeks (week_label) VALUES (?)", (week_label,))
            conn.commit()
        except sqlite3.IntegrityError:
            pass  # Week already exists
        conn.close()
        
        self.refresh_weeks()
        for i in range(self.week_list.count()):
            if self.week_list.item(i).text() == week_label:
                self.week_list.setCurrentRow(i)
                break
    
    def delete_week(self):
        week_id, _ = self.current_week_id()
        if week_id:
            conn = sqlite3.connect(DB_FILE)
            c = conn.cursor()
            c.execute("DELETE FROM weeks WHERE id=?", (week_id,))
            conn.commit()
            conn.close()
            
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