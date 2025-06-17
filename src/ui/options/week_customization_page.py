"""
Week customization settings page for the options dialog
"""

from PySide6 import QtWidgets, QtCore
from .base_page import BasePage
import sqlite3
from core.settings.global_settings import global_settings

# Data Service Layer imports
from core.services.data_service import DataService, DataServiceError
from core.services.week_dao import WeekDAO


class WeekCustomizationPage(BasePage):
    """Week-specific customization settings page"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Initialize Data Service Layer
        try:
            self.data_service = DataService.get_instance()
            self.week_dao = WeekDAO(self.data_service)
        except (DataServiceError, Exception) as e:
            print(f"Warning: Failed to initialize Data Service Layer: {e}")
            # Fallback to direct SQLite if needed
            self.data_service = None
            self.week_dao = None
        
        # Note: setup_ui() is called by BasePage.__init__, no need to call it again

    def setup_ui(self):
        """Setup the UI for the week customization settings page"""
        layout = QtWidgets.QVBoxLayout(self)
        
        # Title
        title = self.create_title("Week Customization")
        layout.addWidget(title)
        
        # Week selection
        week_selection_layout = QtWidgets.QHBoxLayout()
        week_selection_layout.addWidget(QtWidgets.QLabel("Select Week:"))
        
        self.week_combo = QtWidgets.QComboBox()
        self.week_combo.currentTextChanged.connect(self.load_week_settings)
        week_selection_layout.addWidget(self.week_combo)
        
        # Add a revert to global defaults button
        revert_button = QtWidgets.QPushButton("Revert to Global Defaults")
        revert_button.clicked.connect(self.revert_to_global_defaults)
        week_selection_layout.addWidget(revert_button)
        
        week_selection_layout.addStretch()
        
        layout.addLayout(week_selection_layout)
        
        # Duration Settings
        duration_group = QtWidgets.QGroupBox("Duration Settings")
        duration_layout = QtWidgets.QFormLayout(duration_group)
        
        # Custom duration toggle
        self.custom_duration_cb = QtWidgets.QCheckBox("Use custom duration for this week")
        self.custom_duration_cb.toggled.connect(self.toggle_duration_controls)
        duration_layout.addRow("", self.custom_duration_cb)
        
        # Start day/hour
        start_layout = QtWidgets.QHBoxLayout()
        self.week_start_day_combo = QtWidgets.QComboBox()
        self.week_start_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        
        self.week_start_hour_spin = QtWidgets.QDoubleSpinBox()
        self.week_start_hour_spin.setRange(0.0, 23.0)
        self.week_start_hour_spin.setDecimals(0)
        self.week_start_hour_spin.setSuffix(":00")
        
        start_layout.addWidget(self.week_start_day_combo)
        start_layout.addWidget(self.week_start_hour_spin)
        
        # End day/hour
        end_layout = QtWidgets.QHBoxLayout()
        self.week_end_day_combo = QtWidgets.QComboBox()
        self.week_end_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        
        self.week_end_hour_spin = QtWidgets.QDoubleSpinBox()
        self.week_end_hour_spin.setRange(0.0, 23.0)
        self.week_end_hour_spin.setDecimals(0)
        self.week_end_hour_spin.setSuffix(":00")
        
        end_layout.addWidget(self.week_end_day_combo)
        end_layout.addWidget(self.week_end_hour_spin)
        
        duration_layout.addRow("Start:", start_layout)
        duration_layout.addRow("End:", end_layout)
        
        layout.addWidget(duration_group)
        
        # Week-Specific Bonus Settings
        week_bonus_group = QtWidgets.QGroupBox("Week-Specific Bonus Settings")
        week_bonus_layout = QtWidgets.QFormLayout(week_bonus_group)
        
        # Use global bonus settings toggle
        self.use_global_bonus_cb = QtWidgets.QCheckBox("Use global bonus settings")
        self.use_global_bonus_cb.toggled.connect(self.toggle_week_bonus_controls)
        week_bonus_layout.addRow("", self.use_global_bonus_cb)
        
        # Week-specific bonus payrate
        self.week_bonus_payrate_spin = QtWidgets.QDoubleSpinBox()
        self.week_bonus_payrate_spin.setRange(0.0, 999.99)
        self.week_bonus_payrate_spin.setDecimals(2)
        self.week_bonus_payrate_spin.setSuffix(" $/hour")
        
        # Week-specific bonus time windows
        week_bonus_start_layout = QtWidgets.QHBoxLayout()
        self.week_bonus_start_day_combo = QtWidgets.QComboBox()
        self.week_bonus_start_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        
        self.week_bonus_start_time_edit = QtWidgets.QTimeEdit()
        self.week_bonus_start_time_edit.setDisplayFormat("HH:mm")
        
        week_bonus_start_layout.addWidget(self.week_bonus_start_day_combo)
        week_bonus_start_layout.addWidget(self.week_bonus_start_time_edit)
        
        week_bonus_end_layout = QtWidgets.QHBoxLayout()
        self.week_bonus_end_day_combo = QtWidgets.QComboBox()
        self.week_bonus_end_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        
        self.week_bonus_end_time_edit = QtWidgets.QTimeEdit()
        self.week_bonus_end_time_edit.setDisplayFormat("HH:mm")
        
        week_bonus_end_layout.addWidget(self.week_bonus_end_day_combo)
        week_bonus_end_layout.addWidget(self.week_bonus_end_time_edit)
        
        # Week-specific task bonus
        self.week_enable_task_bonus_cb = QtWidgets.QCheckBox("Enable task completion bonus for this week")
        
        self.week_task_threshold_spin = QtWidgets.QDoubleSpinBox()
        self.week_task_threshold_spin.setRange(1.0, 999.0)
        self.week_task_threshold_spin.setDecimals(0)
        self.week_task_threshold_spin.setSuffix(" tasks")
        
        self.week_additional_bonus_spin = QtWidgets.QDoubleSpinBox()
        self.week_additional_bonus_spin.setRange(0.0, 999.99)
        self.week_additional_bonus_spin.setDecimals(2)
        self.week_additional_bonus_spin.setPrefix("$")
        
        week_bonus_layout.addRow("Bonus Payrate:", self.week_bonus_payrate_spin)
        week_bonus_layout.addRow("Bonus Start:", week_bonus_start_layout)
        week_bonus_layout.addRow("Bonus End:", week_bonus_end_layout)
        week_bonus_layout.addRow("", self.week_enable_task_bonus_cb)
        week_bonus_layout.addRow("Task Threshold:", self.week_task_threshold_spin)
        week_bonus_layout.addRow("Additional Amount:", self.week_additional_bonus_spin)
        
        layout.addWidget(week_bonus_group)
        
        # Week-Specific Office Hours Settings
        office_hours_group = QtWidgets.QGroupBox("Week-Specific Office Hours Settings")
        office_hours_layout = QtWidgets.QFormLayout(office_hours_group)
        
        # Use global office hours settings toggle
        self.use_global_office_hours_cb = QtWidgets.QCheckBox("Use global office hours settings")
        self.use_global_office_hours_cb.toggled.connect(self.toggle_week_office_hours_controls)
        office_hours_layout.addRow("", self.use_global_office_hours_cb)
        
        # Week-specific office hour payrate
        self.week_office_hour_payrate_spin = QtWidgets.QDoubleSpinBox()
        self.week_office_hour_payrate_spin.setRange(0.0, 999.99)
        self.week_office_hour_payrate_spin.setDecimals(2)
        self.week_office_hour_payrate_spin.setSuffix(" $/hour")
        
        # Week-specific office hour session duration
        self.week_office_hour_session_duration_spin = QtWidgets.QDoubleSpinBox()
        self.week_office_hour_session_duration_spin.setRange(1.0, 1440.0) # 1 minute to 24 hours
        self.week_office_hour_session_duration_spin.setDecimals(0)
        self.week_office_hour_session_duration_spin.setSuffix(" minutes")
        
        office_hours_layout.addRow("Office Hour Payrate:", self.week_office_hour_payrate_spin)
        office_hours_layout.addRow("Session Duration:", self.week_office_hour_session_duration_spin)
        
        layout.addWidget(office_hours_group)
        
        # Store duration and bonus controls for toggling
        self.duration_controls = [
            self.week_start_day_combo, self.week_start_hour_spin,
            self.week_end_day_combo, self.week_end_hour_spin
        ]
        
        self.week_bonus_controls = [
            self.week_bonus_payrate_spin, self.week_bonus_start_day_combo, self.week_bonus_start_time_edit,
            self.week_bonus_end_day_combo, self.week_bonus_end_time_edit, self.week_enable_task_bonus_cb,
            self.week_task_threshold_spin, self.week_additional_bonus_spin
        ]
        
        self.week_office_hours_controls = [
            self.week_office_hour_payrate_spin,
            self.week_office_hour_session_duration_spin
        ]
        
        layout.addStretch()
        
    def toggle_duration_controls(self, enabled):
        """Enable/disable duration controls based on custom duration toggle"""
        for control in self.duration_controls:
            control.setEnabled(enabled)

    def toggle_week_bonus_controls(self, use_global):
        """Enable/disable week-specific bonus controls"""
        for control in self.week_bonus_controls:
            control.setEnabled(not use_global)
        
    def toggle_week_office_hours_controls(self, use_global):
        """Enable/disable week-specific office hours controls"""
        for control in self.week_office_hours_controls:
            control.setEnabled(not use_global)
        
    def load_settings(self):
        """Load week customization settings"""
        try:
            # Load weeks for customization
            self.load_weeks()
            
        except Exception as e:
            print(f"Error loading week customization settings: {e}")

    def load_weeks(self):
        """Load available weeks into the week combo box using Data Service Layer"""
        try:
            # Use Data Service Layer for week retrieval
            if self.week_dao:
                weeks_data = self.week_dao.get_all_weeks()
                weeks = [(week['week_label'],) for week in weeks_data]  # Convert to tuple format
            else:
                # Fallback to direct SQLite if Data Service Layer not available
                conn = sqlite3.connect('tasks.db')
                c = conn.cursor()
                c.execute("SELECT week_label FROM weeks ORDER BY id")
                weeks = c.fetchall()
                conn.close()
            
            self.week_combo.clear()
            for week in weeks:
                self.week_combo.addItem(week[0])
            
            if self.week_combo.count() > 0:
                self.load_week_settings()
                
        except (DataServiceError, Exception) as e:
            print(f"Error loading weeks: {e}")

    def load_week_settings(self):
        """Load settings for the selected week using Data Service Layer"""
        current_week = self.week_combo.currentText()
        if not current_week:
            return
            
        try:
            # Use Data Service Layer for week settings retrieval
            if self.week_dao:
                week_data = self.week_dao.get_week_by_label(self.week_combo.currentText())
                if week_data:
                    # Convert dict to tuple format for compatibility with existing logic
                    result = (
                        week_data.get('week_start_day'),
                        week_data.get('week_start_hour'),
                        week_data.get('week_end_day'),
                        week_data.get('week_end_hour'),
                        week_data.get('is_custom_duration'),
                        week_data.get('week_specific_bonus_payrate'),
                        week_data.get('week_specific_bonus_start_day'),
                        week_data.get('week_specific_bonus_start_time'),
                        week_data.get('week_specific_bonus_end_day'),
                        week_data.get('week_specific_bonus_end_time'),
                        week_data.get('week_specific_enable_task_bonus'),
                        week_data.get('week_specific_bonus_task_threshold'),
                        week_data.get('week_specific_bonus_additional_amount'),
                        week_data.get('use_global_bonus_settings'),
                        week_data.get('office_hour_count'),
                        week_data.get('office_hour_payrate'),
                        week_data.get('office_hour_session_duration_minutes'),
                        week_data.get('use_global_office_hours_settings')
                    )
                else:
                    result = None
            else:
                # Fallback to direct SQLite if Data Service Layer not available
                conn = sqlite3.connect('tasks.db')
                c = conn.cursor()
                
                c.execute("""
                    SELECT week_start_day, week_start_hour, week_end_day, week_end_hour, 
                           is_custom_duration, week_specific_bonus_payrate, 
                           week_specific_bonus_start_day, week_specific_bonus_start_time,
                           week_specific_bonus_end_day, week_specific_bonus_end_time,
                           week_specific_enable_task_bonus, week_specific_bonus_task_threshold,
                           week_specific_bonus_additional_amount, use_global_bonus_settings,
                           office_hour_count, office_hour_payrate, office_hour_session_duration_minutes, use_global_office_hours_settings
                    FROM weeks WHERE week_label = ?
                """, (self.week_combo.currentText(),))
                
                result = c.fetchone()
                conn.close()
            
            if result:
                # Duration settings
                self.custom_duration_cb.setChecked(bool(result[4]))
                self.week_start_day_combo.setCurrentIndex(result[0] - 1)  # Convert to 0-based
                self.week_start_hour_spin.setValue(result[1])
                self.week_end_day_combo.setCurrentIndex(result[2] - 1)  # Convert to 0-based
                self.week_end_hour_spin.setValue(result[3])
                
                # Bonus settings
                use_global = result[13] if result[13] is not None else 1
                self.use_global_bonus_cb.setChecked(bool(use_global))
                
                if result[5] is not None:
                    self.week_bonus_payrate_spin.setValue(result[5])
                if result[6] is not None:
                    self.week_bonus_start_day_combo.setCurrentIndex(result[6])
                if result[7] is not None:
                    self.week_bonus_start_time_edit.setTime(QtCore.QTime.fromString(result[7], "HH:mm"))
                if result[8] is not None:
                    self.week_bonus_end_day_combo.setCurrentIndex(result[8])
                if result[9] is not None:
                    self.week_bonus_end_time_edit.setTime(QtCore.QTime.fromString(result[9], "HH:mm"))
                if result[10] is not None:
                    self.week_enable_task_bonus_cb.setChecked(bool(result[10]))
                if result[11] is not None:
                    self.week_task_threshold_spin.setValue(result[11])
                if result[12] is not None:
                    self.week_additional_bonus_spin.setValue(result[12])
                
                # Office Hours settings
                use_global_oh = result[17] if result[17] is not None else 1
                self.use_global_office_hours_cb.setChecked(bool(use_global_oh))

                # Load office hour values - show global defaults if using global settings
                global_oh_settings = global_settings.get_default_office_hour_settings()
                
                if bool(use_global_oh) or result[15] is None:
                    # Use global defaults for display
                    self.week_office_hour_payrate_spin.setValue(global_oh_settings['payrate'])
                else:
                    self.week_office_hour_payrate_spin.setValue(result[15])
                    
                if bool(use_global_oh) or result[16] is None:
                    # Use global defaults for display
                    self.week_office_hour_session_duration_spin.setValue(global_oh_settings['session_duration_minutes'])
                else:
                    self.week_office_hour_session_duration_spin.setValue(result[16])
                
                # Apply toggles
                self.toggle_duration_controls(self.custom_duration_cb.isChecked())
                self.toggle_week_bonus_controls(self.use_global_bonus_cb.isChecked())
                self.toggle_week_office_hours_controls(self.use_global_office_hours_cb.isChecked())
                
        except (DataServiceError, Exception) as e:
            print(f"Error loading week settings: {e}")
            
    def save_settings(self):
        """Save week customization settings"""
        try:
            self.save_week_settings()
            return True
        except Exception as e:
            print(f"ERROR in WeekCustomizationPage.save_settings(): {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False

    def revert_to_global_defaults(self):
        """Revert the selected week's settings to global defaults using Data Service Layer"""
        current_week_label = self.week_combo.currentText()
        if not current_week_label:
            QtWidgets.QMessageBox.warning(self, "No Week Selected", "Please select a week to revert settings for.")
            return

        reply = QtWidgets.QMessageBox.question(self, "Confirm Revert",
                                               f"Are you sure you want to revert all custom settings for '{current_week_label}' to global defaults?",
                                               QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.No:
            return

        try:
            # Use Data Service Layer for week settings reset
            if self.week_dao:
                # Get the week ID first
                week_data = self.week_dao.get_week_by_label(current_week_label)
                if week_data:
                    week_id = week_data['id']
                    
                    # Update week settings to global defaults
                    update_data = {
                        'week_start_day': None,
                        'week_start_hour': None,
                        'week_end_day': None,
                        'week_end_hour': None,
                        'is_custom_duration': False,
                        'is_bonus_week': False,
                        'week_specific_bonus_payrate': None,
                        'week_specific_bonus_start_day': None,
                        'week_specific_bonus_start_time': None,
                        'week_specific_bonus_end_day': None,
                        'week_specific_bonus_end_time': None,
                        'week_specific_enable_task_bonus': False,
                        'week_specific_bonus_task_threshold': None,
                        'week_specific_bonus_additional_amount': None,
                        'use_global_bonus_settings': True,
                        'office_hour_count': None,
                        'office_hour_payrate': None,
                        'office_hour_session_duration_minutes': None,
                        'use_global_office_hours_settings': True
                    }
                    
                    success = self.week_dao.update_week(week_id, **update_data)
                    if success:
                        QtWidgets.QMessageBox.information(self, "Reverted", f"Custom settings for '{current_week_label}' reverted to global defaults.")
                    else:
                        QtWidgets.QMessageBox.critical(self, "Error", "Failed to revert settings.")
                else:
                    QtWidgets.QMessageBox.critical(self, "Error", f"Week '{current_week_label}' not found.")
            else:
                # Fallback to direct SQLite if Data Service Layer not available
                conn = sqlite3.connect('tasks.db')
                c = conn.cursor()

                # Update the weeks table to reflect global defaults for duration, bonus, and office hours
                c.execute("""
                    UPDATE weeks SET
                        week_start_day = NULL,
                        week_start_hour = NULL,
                        week_end_day = NULL,
                        week_end_hour = NULL,
                        is_custom_duration = FALSE,
                        is_bonus_week = FALSE,
                        week_specific_bonus_payrate = NULL,
                        week_specific_bonus_start_day = NULL,
                        week_specific_bonus_start_time = NULL,
                        week_specific_bonus_end_day = NULL,
                        week_specific_bonus_end_time = NULL,
                        week_specific_enable_task_bonus = FALSE,
                        week_specific_bonus_task_threshold = NULL,
                        week_specific_bonus_additional_amount = NULL,
                        use_global_bonus_settings = TRUE,
                        office_hour_count = NULL,
                        office_hour_payrate = NULL,
                        office_hour_session_duration_minutes = NULL,
                        use_global_office_hours_settings = TRUE
                    WHERE week_label = ?
                """, (current_week_label,))
                
                conn.commit()
                conn.close()
                QtWidgets.QMessageBox.information(self, "Reverted", f"Custom settings for '{current_week_label}' reverted to global defaults.")
            
            # Reload settings to update UI
            self.load_week_settings()

            # Notify analysis widget to refresh (assuming it can handle a signal or a direct call)
            if hasattr(self.parent(), 'refresh_analysis_widget'):
                self.parent().refresh_analysis_widget()

        except (DataServiceError, sqlite3.Error) as e:
            QtWidgets.QMessageBox.critical(self, "Database Error", f"Failed to revert settings: {e}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

    def save_week_settings(self):
        """Save settings for the selected week to the database using Data Service Layer"""
        if not self.week_combo.currentText():
            return
            
        try:
            week_label = self.week_combo.currentText()
            
            # Prepare values
            is_custom_duration = self.custom_duration_cb.isChecked()
            week_start_day = self.week_start_day_combo.currentIndex() + 1  # Convert to 1-based
            week_start_hour = int(self.week_start_hour_spin.value())
            week_end_day = self.week_end_day_combo.currentIndex() + 1  # Convert to 1-based
            week_end_hour = int(self.week_end_hour_spin.value())
            
            use_global_bonus = self.use_global_bonus_cb.isChecked()
            
            # Week-specific bonus values (NULL if using global)
            if use_global_bonus:
                bonus_values = {
                    'week_specific_bonus_payrate': None,
                    'week_specific_bonus_start_day': None,
                    'week_specific_bonus_start_time': None,
                    'week_specific_bonus_end_day': None,
                    'week_specific_bonus_end_time': None,
                    'week_specific_enable_task_bonus': None,
                    'week_specific_bonus_task_threshold': None,
                    'week_specific_bonus_additional_amount': None
                }
            else:
                bonus_values = {
                    'week_specific_bonus_payrate': self.week_bonus_payrate_spin.value(),
                    'week_specific_bonus_start_day': self.week_bonus_start_day_combo.currentIndex(),
                    'week_specific_bonus_start_time': self.week_bonus_start_time_edit.time().toString("HH:mm"),
                    'week_specific_bonus_end_day': self.week_bonus_end_day_combo.currentIndex(),
                    'week_specific_bonus_end_time': self.week_bonus_end_time_edit.time().toString("HH:mm"),
                    'week_specific_enable_task_bonus': self.week_enable_task_bonus_cb.isChecked(),
                    'week_specific_bonus_task_threshold': int(self.week_task_threshold_spin.value()),
                    'week_specific_bonus_additional_amount': self.week_additional_bonus_spin.value()
                }
            
            use_global_office_hours = self.use_global_office_hours_cb.isChecked()

            # Week-specific office hours values (NULL if using global)
            if use_global_office_hours:
                office_hours_values = {
                    'office_hour_payrate': None,
                    'office_hour_session_duration_minutes': None
                }
            else:
                office_hours_values = {
                    'office_hour_payrate': self.week_office_hour_payrate_spin.value(),
                    'office_hour_session_duration_minutes': self.week_office_hour_session_duration_spin.value()
                }

            # Use Data Service Layer for week settings update
            if self.week_dao:
                # Get the week ID first
                week_data = self.week_dao.get_week_by_label(week_label)
                if week_data:
                    week_id = week_data['id']
                    
                    # Prepare update data
                    update_data = {
                        'week_start_day': week_start_day,
                        'week_start_hour': week_start_hour,
                        'week_end_day': week_end_day,
                        'week_end_hour': week_end_hour,
                        'is_custom_duration': is_custom_duration,
                        'use_global_bonus_settings': use_global_bonus,
                        'use_global_office_hours_settings': use_global_office_hours,
                        **bonus_values,
                        **office_hours_values
                    }
                    
                    success = self.week_dao.update_week(week_id, **update_data)
                    if not success:
                        raise DataServiceError("Failed to update week settings")
                else:
                    raise DataServiceError(f"Week '{week_label}' not found")
            else:
                # Fallback to direct SQLite if Data Service Layer not available
                conn = sqlite3.connect('tasks.db')
                c = conn.cursor()
                
                # Convert bonus and office hours values back to list format for SQL
                bonus_list = list(bonus_values.values())
                office_hours_list = list(office_hours_values.values())
                
                c.execute("""
                    UPDATE weeks SET 
                        week_start_day = ?, week_start_hour = ?, week_end_day = ?, week_end_hour = ?,
                        is_custom_duration = ?, week_specific_bonus_payrate = ?,
                        week_specific_bonus_start_day = ?, week_specific_bonus_start_time = ?,
                        week_specific_bonus_end_day = ?, week_specific_bonus_end_time = ?,
                        week_specific_enable_task_bonus = ?, week_specific_bonus_task_threshold = ?,
                        week_specific_bonus_additional_amount = ?, use_global_bonus_settings = ?,
                        office_hour_payrate = ?, office_hour_session_duration_minutes = ?, use_global_office_hours_settings = ?
                    WHERE week_label = ?
                """, (week_start_day, week_start_hour, week_end_day, week_end_hour, is_custom_duration,
                      *bonus_list, use_global_bonus, *office_hours_list, use_global_office_hours, week_label))
                
                conn.commit()
                conn.close()
            
        except (DataServiceError, Exception) as e:
            print(f"Error saving week settings: {e}")
            raise 