"""
Global defaults settings page for the options dialog
"""

from PySide6 import QtWidgets, QtCore
from .base_page import BasePage
from core.settings.global_settings import global_settings


class GlobalDefaultsPage(BasePage):
    """Global default settings page"""
    
    def setup_ui(self):
        """Setup the UI for the global defaults settings page"""
        # Create scrollable page
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        page = QtWidgets.QWidget()
        scroll.setWidget(page)
        
        layout = QtWidgets.QVBoxLayout(page)
        
        # Title
        title = self.create_title("Global Default Settings")
        layout.addWidget(title)
        
        # Master Bonus System Toggle
        bonus_system_group = QtWidgets.QGroupBox("Bonus System")
        bonus_system_layout = QtWidgets.QVBoxLayout(bonus_system_group)
        
        self.global_bonus_enabled_cb = QtWidgets.QCheckBox("Enable Global Bonus System")
        self.global_bonus_enabled_cb.setToolTip("Master toggle for the entire bonus system")
        self.global_bonus_enabled_cb.toggled.connect(self.toggle_global_bonus_controls)
        bonus_system_layout.addWidget(self.global_bonus_enabled_cb)
        
        layout.addWidget(bonus_system_group)
        
        # Payrates
        payrates_group = QtWidgets.QGroupBox("Payrates")
        payrates_layout = QtWidgets.QFormLayout(payrates_group)
        
        self.regular_payrate_spin = QtWidgets.QDoubleSpinBox()
        self.regular_payrate_spin.setRange(0.0, 999.99)
        self.regular_payrate_spin.setDecimals(2)
        self.regular_payrate_spin.setSuffix(" $/hour")
        
        self.bonus_payrate_spin = QtWidgets.QDoubleSpinBox()
        self.bonus_payrate_spin.setRange(0.0, 999.99)
        self.bonus_payrate_spin.setDecimals(2)
        self.bonus_payrate_spin.setSuffix(" $/hour")
        
        payrates_layout.addRow("Regular Payrate:", self.regular_payrate_spin)
        payrates_layout.addRow("Bonus Payrate:", self.bonus_payrate_spin)
        
        layout.addWidget(payrates_group)
        
        # Bonus Time Windows
        bonus_time_group = QtWidgets.QGroupBox("Bonus Time Windows")
        bonus_time_layout = QtWidgets.QFormLayout(bonus_time_group)
        
        # Start day/time
        start_layout = QtWidgets.QHBoxLayout()
        self.bonus_start_day_combo = QtWidgets.QComboBox()
        self.bonus_start_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        
        self.bonus_start_time_edit = QtWidgets.QTimeEdit()
        self.bonus_start_time_edit.setDisplayFormat("HH:mm")
        
        start_layout.addWidget(self.bonus_start_day_combo)
        start_layout.addWidget(self.bonus_start_time_edit)
        
        # End day/time
        end_layout = QtWidgets.QHBoxLayout()
        self.bonus_end_day_combo = QtWidgets.QComboBox()
        self.bonus_end_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        
        self.bonus_end_time_edit = QtWidgets.QTimeEdit()
        self.bonus_end_time_edit.setDisplayFormat("HH:mm")
        
        end_layout.addWidget(self.bonus_end_day_combo)
        end_layout.addWidget(self.bonus_end_time_edit)
        
        bonus_time_layout.addRow("Start:", start_layout)
        bonus_time_layout.addRow("End:", end_layout)
        
        layout.addWidget(bonus_time_group)
        
        # Task-based bonus
        task_bonus_group = QtWidgets.QGroupBox("Task-Based Bonus")
        task_bonus_layout = QtWidgets.QFormLayout(task_bonus_group)
        
        self.enable_task_bonus_cb = QtWidgets.QCheckBox("Enable task completion bonus")
        
        self.task_threshold_spin = QtWidgets.QDoubleSpinBox()
        self.task_threshold_spin.setRange(1.0, 999.0)
        self.task_threshold_spin.setDecimals(0)
        self.task_threshold_spin.setSuffix(" tasks")
        
        self.additional_bonus_spin = QtWidgets.QDoubleSpinBox()
        self.additional_bonus_spin.setRange(0.0, 999.99)
        self.additional_bonus_spin.setDecimals(2)
        self.additional_bonus_spin.setPrefix("$")
        
        task_bonus_layout.addRow("", self.enable_task_bonus_cb)
        task_bonus_layout.addRow("Task Threshold:", self.task_threshold_spin)
        task_bonus_layout.addRow("Additional Amount:", self.additional_bonus_spin)
        
        layout.addWidget(task_bonus_group)
        
        # Global Office Hour Defaults
        office_hours_group = QtWidgets.QGroupBox("Global Office Hour Defaults")
        office_hours_layout = QtWidgets.QFormLayout(office_hours_group)
        
        self.default_office_hour_payrate_spin = QtWidgets.QDoubleSpinBox()
        self.default_office_hour_payrate_spin.setRange(0.0, 999.99)
        self.default_office_hour_payrate_spin.setDecimals(2)
        self.default_office_hour_payrate_spin.setSuffix(" $/hour")
        
        self.default_office_hour_session_duration_spin = QtWidgets.QDoubleSpinBox()
        self.default_office_hour_session_duration_spin.setRange(1.0, 1440.0) # 1 minute to 24 hours
        self.default_office_hour_session_duration_spin.setDecimals(0)
        self.default_office_hour_session_duration_spin.setSuffix(" minutes")
        
        office_hours_layout.addRow("Default Payrate:", self.default_office_hour_payrate_spin)
        office_hours_layout.addRow("Default Session Duration:", self.default_office_hour_session_duration_spin)
        
        layout.addWidget(office_hours_group)
        
        # Default Week Duration
        week_duration_group = QtWidgets.QGroupBox("Default Week Duration")
        week_duration_layout = QtWidgets.QFormLayout(week_duration_group)
        
        # Enforce exact week duration checkbox
        self.enforce_exact_week_duration_cb = QtWidgets.QCheckBox("Strictly enforce 7-day week duration for new weeks")
        self.enforce_exact_week_duration_cb.setToolTip("When enabled, new weeks must be exactly 7 days long")
        week_duration_layout.addRow("", self.enforce_exact_week_duration_cb)
        
        # Start day/hour
        start_week_layout = QtWidgets.QHBoxLayout()
        self.default_start_day_combo = QtWidgets.QComboBox()
        self.default_start_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        
        self.default_start_hour_spin = QtWidgets.QDoubleSpinBox()
        self.default_start_hour_spin.setRange(0.0, 23.0)
        self.default_start_hour_spin.setDecimals(0)
        self.default_start_hour_spin.setSuffix(":00")
        
        start_week_layout.addWidget(self.default_start_day_combo)
        start_week_layout.addWidget(self.default_start_hour_spin)
        
        # End day/hour
        end_week_layout = QtWidgets.QHBoxLayout()
        self.default_end_day_combo = QtWidgets.QComboBox()
        self.default_end_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        
        self.default_end_hour_spin = QtWidgets.QDoubleSpinBox()
        self.default_end_hour_spin.setRange(0.0, 23.0)
        self.default_end_hour_spin.setDecimals(0)
        self.default_end_hour_spin.setSuffix(":00")
        
        end_week_layout.addWidget(self.default_end_day_combo)
        end_week_layout.addWidget(self.default_end_hour_spin)
        
        week_duration_layout.addRow("Start:", start_week_layout)
        week_duration_layout.addRow("End:", end_week_layout)
        
        layout.addWidget(week_duration_group)
        
        # Store bonus controls for toggling
        self.global_bonus_controls = [
            self.bonus_payrate_spin, bonus_time_group, task_bonus_group
        ]
        
        layout.addStretch()
        
        # Add scroll area to main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(scroll)
        
    def toggle_global_bonus_controls(self, enabled):
        """Enable/disable global bonus controls based on master toggle"""
        for control in self.global_bonus_controls:
            control.setEnabled(enabled)
        
    def load_settings(self):
        """Load global defaults settings"""
        try:
            # Global defaults
            bonus_settings = global_settings.get_default_bonus_settings()
            self.global_bonus_enabled_cb.setChecked(bonus_settings['global_bonus_enabled'])
            self.regular_payrate_spin.setValue(global_settings.get_default_payrate())
            self.bonus_payrate_spin.setValue(bonus_settings['bonus_payrate'])
            
            # Bonus time windows
            self.bonus_start_day_combo.setCurrentIndex(bonus_settings['bonus_start_day'] - 1)  # Convert to 0-based
            self.bonus_start_time_edit.setTime(QtCore.QTime.fromString(bonus_settings['bonus_start_time'], "HH:mm"))
            self.bonus_end_day_combo.setCurrentIndex(bonus_settings['bonus_end_day'] - 1)  # Convert to 0-based
            self.bonus_end_time_edit.setTime(QtCore.QTime.fromString(bonus_settings['bonus_end_time'], "HH:mm"))
            
            # Task bonus
            self.enable_task_bonus_cb.setChecked(bonus_settings['enable_task_bonus'])
            self.task_threshold_spin.setValue(bonus_settings['bonus_task_threshold'])
            self.additional_bonus_spin.setValue(bonus_settings['bonus_additional_amount'])
            
            # Office hours defaults
            office_hours_settings = global_settings.get_default_office_hour_settings()
            self.default_office_hour_payrate_spin.setValue(office_hours_settings['payrate'])
            self.default_office_hour_session_duration_spin.setValue(office_hours_settings['session_duration_minutes'])
            
            # Default week duration
            week_settings = global_settings.get_default_week_settings()
            self.default_start_day_combo.setCurrentIndex(week_settings['week_start_day'] - 1)  # Convert to 0-based
            self.default_start_hour_spin.setValue(week_settings['week_start_hour'])
            self.default_end_day_combo.setCurrentIndex(week_settings['week_end_day'] - 1)  # Convert to 0-based
            self.default_end_hour_spin.setValue(week_settings['week_end_hour'])
            
            # Enforce exact week duration
            self.enforce_exact_week_duration_cb.setChecked(global_settings.should_enforce_week_duration())
            
            # Apply initial toggles
            self.toggle_global_bonus_controls(self.global_bonus_enabled_cb.isChecked())
            
        except Exception as e:
            print(f"Error loading global defaults settings: {e}")
            
    def save_settings(self):
        """Save global defaults settings"""
        try:
            # Global defaults
            global_settings.set_setting("bonus_settings.global_bonus_enabled", self.global_bonus_enabled_cb.isChecked())
            global_settings.set_setting("ui_settings.default_payrate", self.regular_payrate_spin.value())
            global_settings.set_setting("bonus_settings.default_bonus_payrate", self.bonus_payrate_spin.value())
            
            # Bonus time windows
            global_settings.set_setting("bonus_settings.default_bonus_start_day", self.bonus_start_day_combo.currentIndex() + 1)  # Convert to 1-based
            global_settings.set_setting("bonus_settings.default_bonus_start_time", self.bonus_start_time_edit.time().toString("HH:mm"))
            global_settings.set_setting("bonus_settings.default_bonus_end_day", self.bonus_end_day_combo.currentIndex() + 1)  # Convert to 1-based
            global_settings.set_setting("bonus_settings.default_bonus_end_time", self.bonus_end_time_edit.time().toString("HH:mm"))
            
            # Task bonus
            global_settings.set_setting("bonus_settings.default_enable_task_bonus", self.enable_task_bonus_cb.isChecked())
            global_settings.set_setting("bonus_settings.default_bonus_task_threshold", int(self.task_threshold_spin.value()))
            global_settings.set_setting("bonus_settings.default_bonus_additional_amount", self.additional_bonus_spin.value())
            
            # Office hours defaults
            global_settings.set_setting("office_hours_settings.default_office_hour_payrate", self.default_office_hour_payrate_spin.value())
            global_settings.set_setting("office_hours_settings.default_office_hour_session_duration_minutes", self.default_office_hour_session_duration_spin.value())
            
            # Default week duration
            global_settings.set_setting("week_settings.default_week_start_day", self.default_start_day_combo.currentIndex() + 1)  # Convert to 1-based
            global_settings.set_setting("week_settings.default_week_start_hour", int(self.default_start_hour_spin.value()))
            global_settings.set_setting("week_settings.default_week_end_day", self.default_end_day_combo.currentIndex() + 1)  # Convert to 1-based
            global_settings.set_setting("week_settings.default_week_end_hour", int(self.default_end_hour_spin.value()))
            
            # Enforce exact week duration
            global_settings.set_setting("week_settings.enforce_exact_week_duration", self.enforce_exact_week_duration_cb.isChecked())
            
            return True
            
        except Exception as e:
            print(f"ERROR in GlobalDefaultsPage.save_settings(): {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return False 