"""
Classic Task Edit Dialog - Qt Widgets Implementation  
A classic dialog for editing task data that matches the app's existing UI style.
"""

from datetime import datetime
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel, QLineEdit, 
    QTextEdit, QComboBox, QPushButton, QGroupBox, QDialogButtonBox
)
from PySide6.QtCore import Qt, QTimer, Signal
from core.db.db_connection_pool import get_db_connection


class ClassicTaskEditDialog(QDialog):
    """Classic task edit dialog with integrated timer functionality"""
    
    # Signals
    taskDataSaved = Signal(int, dict)
    timerStarted = Signal(int)
    timerStopped = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.task_id = 0
        self.timer_running = False
        self.timer_paused = False
        self.timer_seconds = 0
        self.session_start_time = None  # Track when current session started
        
        # Timer for updating display
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.timer_tick)
        
        self.setup_ui()
        
    def setup_ui(self):
        """Set up the user interface using classic dialog style"""
        self.setWindowTitle("Edit Task")
        self.setModal(True)
        self.resize(500, 600)
        
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(15)
        
        # Timer group
        self.create_timer_group(main_layout)
        
        # Basic information group
        self.create_basic_info_group(main_layout)
        
        # Time tracking group
        self.create_time_tracking_group(main_layout)
        
        # Feedback group
        self.create_feedback_group(main_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel,
            Qt.Horizontal, self
        )
        button_box.accepted.connect(self.save_task_data)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)
        
    def create_timer_group(self, parent_layout):
        """Create timer group box"""
        timer_group = QGroupBox("Timer & Duration")
        parent_layout.addWidget(timer_group)
        
        timer_layout = QVBoxLayout(timer_group)
        
        # Timer display row
        timer_row = QHBoxLayout()
        timer_row.addWidget(QLabel("Current Timer:"))
        
        self.timer_display = QLabel("00:00:00")
        self.timer_display.setObjectName("timerDisplay")
        self.timer_display.setStyleSheet("""
            QLabel#timerDisplay {
                font-size: 18px;
                font-weight: bold;
                font-family: 'Consolas', 'Monaco', monospace;
                padding: 8px;
                border: 1px solid #1f201f;
                border-radius: 4px;
                background-color: #2a2b2a;
            }
        """)
        timer_row.addWidget(self.timer_display)
        
        # Timer status indicator
        self.timer_status = QLabel("Stopped")
        self.timer_status.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #808080;
                padding: 2px 6px;
                border-radius: 3px;
                background-color: #1f201f;
            }
        """)
        timer_row.addWidget(self.timer_status)
        
        timer_row.addStretch()
        
        # Timer control buttons
        timer_controls_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_timer)
        timer_controls_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self.pause_timer)
        self.pause_btn.setEnabled(False)
        timer_controls_layout.addWidget(self.pause_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.clicked.connect(self.stop_timer)
        self.stop_btn.setEnabled(False)
        timer_controls_layout.addWidget(self.stop_btn)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_timer)
        timer_controls_layout.addWidget(self.refresh_btn)
        
        timer_row.addLayout(timer_controls_layout)
        
        timer_layout.addLayout(timer_row)
        
        # Duration field
        duration_row = QHBoxLayout()
        duration_row.addWidget(QLabel("Duration:"))
        
        self.duration_field = QLineEdit()
        self.duration_field.setPlaceholderText("HH:MM:SS")
        duration_row.addWidget(self.duration_field)
        
        timer_layout.addLayout(duration_row)
        
    def create_basic_info_group(self, parent_layout):
        """Create basic information group box"""
        basic_group = QGroupBox("Basic Information")
        parent_layout.addWidget(basic_group)
        
        grid_layout = QGridLayout(basic_group)
        
        # Attempt ID
        grid_layout.addWidget(QLabel("Attempt ID:"), 0, 0)
        self.attempt_id_field = QLineEdit()
        grid_layout.addWidget(self.attempt_id_field, 0, 1)
        
        # Project ID
        grid_layout.addWidget(QLabel("Project ID:"), 1, 0)
        self.project_id_field = QLineEdit()
        grid_layout.addWidget(self.project_id_field, 1, 1)
        
        # Project Name
        grid_layout.addWidget(QLabel("Project Name:"), 2, 0)
        self.project_name_field = QLineEdit()
        grid_layout.addWidget(self.project_name_field, 2, 1)
        
        # Operation ID
        grid_layout.addWidget(QLabel("Operation ID:"), 3, 0)
        self.operation_id_field = QLineEdit()
        grid_layout.addWidget(self.operation_id_field, 3, 1)
        
        # Time Limit
        grid_layout.addWidget(QLabel("Time Limit:"), 4, 0)
        self.time_limit_field = QLineEdit()
        self.time_limit_field.setPlaceholderText("HH:MM:SS")
        grid_layout.addWidget(self.time_limit_field, 4, 1)
        
        # Date Audited
        grid_layout.addWidget(QLabel("Date Audited:"), 5, 0)
        self.date_audited_field = QLineEdit()
        self.date_audited_field.setPlaceholderText("YYYY-MM-DD")
        grid_layout.addWidget(self.date_audited_field, 5, 1)
        
        # Score
        grid_layout.addWidget(QLabel("Score (1-5):"), 6, 0)
        self.score_combobox = QComboBox()
        self.score_combobox.addItems(["1", "2", "3", "4", "5"])
        self.score_combobox.setCurrentText("1")
        grid_layout.addWidget(self.score_combobox, 6, 1)
        
        # Locale
        grid_layout.addWidget(QLabel("Locale:"), 7, 0)
        self.locale_field = QLineEdit()
        grid_layout.addWidget(self.locale_field, 7, 1)
        
    def create_time_tracking_group(self, parent_layout):
        """Create time tracking group box"""
        time_group = QGroupBox("Time Tracking")
        parent_layout.addWidget(time_group)
        
        grid_layout = QGridLayout(time_group)
        
        # Time Begin
        grid_layout.addWidget(QLabel("Time Begin:"), 0, 0)
        self.time_begin_field = QLineEdit()
        self.time_begin_field.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        grid_layout.addWidget(self.time_begin_field, 0, 1)
        
        # Time End
        grid_layout.addWidget(QLabel("Time End:"), 1, 0)
        self.time_end_field = QLineEdit()
        self.time_end_field.setPlaceholderText("YYYY-MM-DD HH:MM:SS")
        grid_layout.addWidget(self.time_end_field, 1, 1)
        
    def create_feedback_group(self, parent_layout):
        """Create feedback group box"""
        feedback_group = QGroupBox("Feedback")
        parent_layout.addWidget(feedback_group)
        
        feedback_layout = QVBoxLayout(feedback_group)
        
        self.feedback_area = QTextEdit()
        self.feedback_area.setPlaceholderText("Enter feedback here...")
        self.feedback_area.setMaximumHeight(120)
        feedback_layout.addWidget(self.feedback_area)
        
    def set_task_data(self, task_id, task_data):
        """Set task data in the dialog fields"""
        self.task_id = task_id
        self.setWindowTitle(f"Edit Task #{task_id}")
        
        # Populate fields
        self.attempt_id_field.setText(task_data.get('attemptId', ''))
        self.duration_field.setText(task_data.get('duration', '00:00:00'))
        self.project_id_field.setText(task_data.get('projectId', ''))
        self.project_name_field.setText(task_data.get('projectName', ''))
        self.operation_id_field.setText(task_data.get('operationId', ''))
        self.time_limit_field.setText(task_data.get('timeLimit', '00:00:00'))
        self.date_audited_field.setText(task_data.get('dateAudited', ''))
        self.score_combobox.setCurrentText(str(task_data.get('score', '1')))
        self.feedback_area.setPlainText(task_data.get('feedback', ''))
        self.locale_field.setText(task_data.get('locale', ''))
        self.time_begin_field.setText(task_data.get('timeBegin', ''))
        self.time_end_field.setText(task_data.get('timeEnd', ''))
        
        # Initialize timer
        self.timer_seconds = self.parse_time_to_seconds(task_data.get('duration', '00:00:00'))
        self.update_timer_display()
        
    def parse_time_to_seconds(self, time_string):
        """Parse time string to seconds"""
        if not time_string or time_string == "00:00:00":
            return 0
        
        try:
            parts = time_string.split(":")
            if len(parts) != 3:
                return 0
            
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = int(parts[2])
            
            return hours * 3600 + minutes * 60 + seconds
        except (ValueError, AttributeError):
            return 0
    
    def update_timer_display(self):
        """Update the timer display"""
        hours = self.timer_seconds // 3600
        minutes = (self.timer_seconds % 3600) // 60
        seconds = self.timer_seconds % 60
        
        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.timer_display.setText(time_str)
        
        # Update duration field in real-time if timer is running
        if self.timer_running:
            self.duration_field.setText(time_str)
    
    def update_timer_status(self, status, color="#808080", bg_color="#1f201f"):
        """Update timer status indicator"""
        self.timer_status.setText(status)
        self.timer_status.setStyleSheet(f"""
            QLabel {{
                font-size: 10px;
                color: {color};
                padding: 2px 6px;
                border-radius: 3px;
                background-color: {bg_color};
            }}
        """)
    
    def start_timer(self):
        """Start the timer"""
        if not self.timer_running and not self.timer_paused:
            # Fresh start
            self.timer_running = True
            self.timer_paused = False
            self.session_start_time = datetime.now()
            self.update_timer.start(1000)  # Update every second
            self.timerStarted.emit(self.task_id)
            
            # Set time_begin if not already set (first time starting this task)
            if not self.time_begin_field.text().strip():
                self.time_begin_field.setText(self.session_start_time.strftime("%Y-%m-%d %H:%M:%S"))
            
            # Update button states and status
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.update_timer_status("Running", "#ffffff", "#0078d4")
            
        elif self.timer_paused:
            # Resume from pause
            self.timer_running = True
            self.timer_paused = False
            self.session_start_time = datetime.now()  # Reset session start for accurate time tracking
            self.update_timer.start(1000)
            
            # Update button states and status
            self.start_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.update_timer_status("Running", "#ffffff", "#0078d4")
    
    def pause_timer(self):
        """Pause the timer"""
        if self.timer_running:
            self.timer_running = False
            self.timer_paused = True
            self.update_timer.stop()
            
            # Update button states and status
            self.start_btn.setEnabled(True)
            self.start_btn.setText("Resume")
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.update_timer_status("Paused", "#ffffff", "#ff8c00")
    
    def stop_timer(self):
        """Stop the timer completely"""
        if self.timer_running or self.timer_paused:
            self.timer_running = False
            self.timer_paused = False
            self.update_timer.stop()
            self.timerStopped.emit(self.task_id)
            
            # Set time_end to current time
            now = datetime.now()
            self.time_end_field.setText(now.strftime("%Y-%m-%d %H:%M:%S"))
            
            # Update button states and status
            self.start_btn.setEnabled(True)
            self.start_btn.setText("Start")
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.update_timer_status("Stopped", "#808080", "#1f201f")
    
    def refresh_timer(self):
        """Refresh timer from duration field or reset to zero"""
        # Stop timer if running
        was_running = self.timer_running
        if self.timer_running or self.timer_paused:
            self.stop_timer()
        
        # Parse duration field and update timer
        duration_text = self.duration_field.text().strip()
        if duration_text:
            self.timer_seconds = self.parse_time_to_seconds(duration_text)
        else:
            self.timer_seconds = 0
            self.duration_field.setText("00:00:00")
        
        self.update_timer_display()
        
        # If timer was running, ask user if they want to restart
        if was_running:
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(
                self, 
                "Restart Timer?", 
                "Timer was running. Do you want to restart it with the refreshed time?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.start_timer()
    
    def timer_tick(self):
        """Timer tick - increment seconds and update display"""
        self.timer_seconds += 1
        self.update_timer_display()
    
    def save_task_data(self):
        """Save task data to database and emit signal"""
        task_data = {
            'attemptId': self.attempt_id_field.text(),
            'duration': self.duration_field.text(),
            'projectId': self.project_id_field.text(),
            'projectName': self.project_name_field.text(),
            'operationId': self.operation_id_field.text(),
            'timeLimit': self.time_limit_field.text(),
            'dateAudited': self.date_audited_field.text(),
            'score': self.score_combobox.currentText(),
            'feedback': self.feedback_area.toPlainText(),
            'locale': self.locale_field.text(),
            'timeBegin': self.time_begin_field.text(),
            'timeEnd': self.time_end_field.text()
        }
        
        # Update database
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                UPDATE tasks SET 
                    attempt_id=?, duration=?, project_id=?, project_name=?, 
                    operation_id=?, time_limit=?, date_audited=?, score=?, 
                    feedback=?, locale=?, time_begin=?, time_end=?
                WHERE id=?
            """, (
                task_data['attemptId'], task_data['duration'], task_data['projectId'],
                task_data['projectName'], task_data['operationId'], task_data['timeLimit'],
                task_data['dateAudited'], task_data['score'], task_data['feedback'],
                task_data['locale'], task_data['timeBegin'], task_data['timeEnd'],
                self.task_id
            ))
            conn.commit()
        
        # Emit signal and close
        self.taskDataSaved.emit(self.task_id, task_data)
        self.accept()
    
    def closeEvent(self, event):
        """Handle close event - stop timer if running"""
        if self.timer_running or self.timer_paused:
            self.stop_timer()
        super().closeEvent(event) 