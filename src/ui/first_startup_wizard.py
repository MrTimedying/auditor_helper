from PySide6 import QtWidgets, QtCore, QtGui
import os
from core.settings.global_settings import global_settings, DEFAULT_GLOBAL_SETTINGS, get_icon_path

basedir = os.path.dirname(__file__)

class FirstStartupWizard(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Welcome to Auditor Helper")
        self.setWindowIcon(QtGui.QIcon(get_icon_path("app_icon.ico")))
        self.setModal(True)
        self.setMinimumSize(600, 500)
        self.resize(700, 600)
        
        # Make dialog non-closable until completed
        self.setWindowFlags(QtCore.Qt.Dialog | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowTitleHint)
        
        self.setup_ui()
        self.load_default_values()
    
    def setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(30, 30, 30, 30)
        
        # Welcome header
        header_layout = QtWidgets.QVBoxLayout()
        
        welcome_label = QtWidgets.QLabel("Welcome to Auditor Helper")
        welcome_label.setStyleSheet("QLabel { font-size: 20px; font-weight: bold; color: #E0E0E0; }")
        welcome_label.setAlignment(QtCore.Qt.AlignCenter)
        header_layout.addWidget(welcome_label)
        
        subtitle_label = QtWidgets.QLabel("This wizard will guide you through the initial configuration of Auditor Helper. Please configure the following essential settings to begin.")
        subtitle_label.setStyleSheet("QLabel { font-size: 13px; color: #B0B0B0; margin-bottom: 10px; }")
        subtitle_label.setAlignment(QtCore.Qt.AlignCenter)
        subtitle_label.setWordWrap(True)
        header_layout.addWidget(subtitle_label)
        
        main_layout.addLayout(header_layout)
        
        # Create scroll area for settings
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        
        scroll_content = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_content)
        
        # Apply general styling to all QGroupBoxes and QLabels within them
        common_groupbox_style = """
            QGroupBox {
                font-weight: bold;
                border: 1px solid #3A3A3A;
                border-radius: 4px;
                margin-top: 1ex;
                padding: 8px;
                color: #E0E0E0;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 4px;
                color: #E0E0E0; /* Changed from accent color to neutral for consistency */
            }
        """
        common_label_style = "QLabel { color: #CCCCCC; margin-bottom: 3px; }" # Adjusted margin and color
        
        # Week Settings Section
        week_group = QtWidgets.QGroupBox("Default Week Configuration")
        week_group.setStyleSheet(common_groupbox_style)
        week_layout = QtWidgets.QVBoxLayout(week_group)
        
        week_description = QtWidgets.QLabel(
            "Please define the default start and end days/times for your working weeks. This configuration will serve as the template for newly created weeks."
        )
        week_description.setWordWrap(True)
        week_description.setStyleSheet("QLabel { color: #B0B0B0; margin-bottom: 8px; }") # Adjusted margin and color
        week_layout.addWidget(week_description)
        
        # Week duration settings
        duration_frame = QtWidgets.QFrame()
        duration_frame.setStyleSheet("QFrame { border: none; }")
        duration_layout = QtWidgets.QGridLayout(duration_frame)
        
        # Week start settings
        start_week_label = QtWidgets.QLabel("Week commences:")
        start_week_label.setStyleSheet(common_label_style)
        duration_layout.addWidget(start_week_label, 0, 0)
        self.start_day_combo = QtWidgets.QComboBox()
        self.start_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        duration_layout.addWidget(self.start_day_combo, 0, 1)
        
        self.start_hour_spinbox = QtWidgets.QSpinBox()
        self.start_hour_spinbox.setRange(0, 23)
        self.start_hour_spinbox.setSuffix(":00")
        duration_layout.addWidget(self.start_hour_spinbox, 0, 2)
        
        # Week end settings
        end_week_label = QtWidgets.QLabel("Week concludes:")
        end_week_label.setStyleSheet(common_label_style)
        duration_layout.addWidget(end_week_label, 1, 0)
        self.end_day_combo = QtWidgets.QComboBox()
        self.end_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        duration_layout.addWidget(self.end_day_combo, 1, 1)
        
        self.end_hour_spinbox = QtWidgets.QSpinBox()
        self.end_hour_spinbox.setRange(0, 23)
        self.end_hour_spinbox.setSuffix(":00")
        duration_layout.addWidget(self.end_hour_spinbox, 1, 2)
        
        week_layout.addWidget(duration_frame)
        
        # Week validation checkbox
        self.enforce_week_duration = QtWidgets.QCheckBox("Strictly enforce a 7-day week duration for new week creations")
        self.enforce_week_duration.setChecked(True)
        self.enforce_week_duration.setStyleSheet("QCheckBox { color: #CCCCCC; }")
        week_layout.addWidget(self.enforce_week_duration)
        
        scroll_layout.addWidget(week_group)
        
        # Bonus Settings Section
        bonus_group = QtWidgets.QGroupBox("Default Bonus Configuration")
        bonus_group.setStyleSheet(common_groupbox_style)
        bonus_layout = QtWidgets.QVBoxLayout(bonus_group)
        
        bonus_description = QtWidgets.QLabel(
            "Specify the default bonus calculation parameters. These settings will be applied to weeks designated as 'bonus weeks'."
        )
        bonus_description.setWordWrap(True)
        bonus_description.setStyleSheet("QLabel { color: #B0B0B0; margin-bottom: 8px; }") # Adjusted margin and color
        bonus_layout.addWidget(bonus_description)
        
        # Bonus time range
        bonus_time_frame = QtWidgets.QFrame()
        bonus_time_frame.setStyleSheet("QFrame { border: none; }")
        bonus_time_layout = QtWidgets.QGridLayout(bonus_time_frame)
        
        # Start day and time
        bonus_start_label = QtWidgets.QLabel("Bonus period commences:")
        bonus_start_label.setStyleSheet(common_label_style)
        bonus_time_layout.addWidget(bonus_start_label, 0, 0)
        self.bonus_start_day_combo = QtWidgets.QComboBox()
        self.bonus_start_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        bonus_time_layout.addWidget(self.bonus_start_day_combo, 0, 1)
        
        self.bonus_start_time = QtWidgets.QTimeEdit()
        self.bonus_start_time.setDisplayFormat("HH:mm")
        bonus_time_layout.addWidget(self.bonus_start_time, 0, 2)
        
        # End day and time
        bonus_end_label = QtWidgets.QLabel("Bonus period concludes:")
        bonus_end_label.setStyleSheet(common_label_style)
        bonus_time_layout.addWidget(bonus_end_label, 1, 0)
        self.bonus_end_day_combo = QtWidgets.QComboBox()
        self.bonus_end_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        bonus_time_layout.addWidget(self.bonus_end_day_combo, 1, 1)
        
        self.bonus_end_time = QtWidgets.QTimeEdit()
        self.bonus_end_time.setDisplayFormat("HH:mm")
        bonus_time_layout.addWidget(self.bonus_end_time, 1, 2)
        
        bonus_layout.addWidget(bonus_time_frame)
        
        # Payrate settings
        payrate_frame = QtWidgets.QFrame()
        payrate_frame.setStyleSheet("QFrame { border: none; }")
        payrate_layout = QtWidgets.QGridLayout(payrate_frame)
        
        regular_payrate_label = QtWidgets.QLabel("Standard hourly payrate:")
        regular_payrate_label.setStyleSheet(common_label_style)
        payrate_layout.addWidget(regular_payrate_label, 0, 0)
        self.regular_payrate_spinbox = QtWidgets.QDoubleSpinBox()
        self.regular_payrate_spinbox.setRange(0.0, 999.99)
        self.regular_payrate_spinbox.setDecimals(2)
        self.regular_payrate_spinbox.setSuffix(" $/hour")
        payrate_layout.addWidget(self.regular_payrate_spinbox, 0, 1)
        
        bonus_payrate_label = QtWidgets.QLabel("Bonus hourly payrate:")
        bonus_payrate_label.setStyleSheet(common_label_style)
        payrate_layout.addWidget(bonus_payrate_label, 1, 0)
        self.bonus_payrate_spinbox = QtWidgets.QDoubleSpinBox()
        self.bonus_payrate_spinbox.setRange(0.0, 999.99)
        self.bonus_payrate_spinbox.setDecimals(2)
        self.bonus_payrate_spinbox.setSuffix(" $/hour")
        payrate_layout.addWidget(self.bonus_payrate_spinbox, 1, 1)
        
        bonus_layout.addWidget(payrate_frame)
        
        # Task-based bonus
        task_bonus_frame = QtWidgets.QFrame()
        task_bonus_frame.setStyleSheet("QFrame { border: none; }")
        task_bonus_layout = QtWidgets.QGridLayout(task_bonus_frame)
        
        self.enable_task_bonus = QtWidgets.QCheckBox("Activate task completion bonus")
        self.enable_task_bonus.setStyleSheet("QCheckBox { color: #CCCCCC; }")
        task_bonus_layout.addWidget(self.enable_task_bonus, 0, 0, 1, 2)
        
        task_threshold_label = QtWidgets.QLabel("Minimum tasks threshold:")
        task_threshold_label.setStyleSheet(common_label_style)
        task_bonus_layout.addWidget(task_threshold_label, 1, 0)
        self.task_threshold_spinbox = QtWidgets.QSpinBox()
        self.task_threshold_spinbox.setRange(1, 999)
        task_bonus_layout.addWidget(self.task_threshold_spinbox, 1, 1)
        
        additional_bonus_label = QtWidgets.QLabel("Supplemental bonus amount:")
        additional_bonus_label.setStyleSheet(common_label_style)
        task_bonus_layout.addWidget(additional_bonus_label, 2, 0)
        self.additional_bonus_spinbox = QtWidgets.QDoubleSpinBox()
        self.additional_bonus_spinbox.setRange(0.0, 9999.99)
        self.additional_bonus_spinbox.setDecimals(2)
        self.additional_bonus_spinbox.setSuffix(" $")
        task_bonus_layout.addWidget(self.additional_bonus_spinbox, 2, 1)
        
        bonus_layout.addWidget(task_bonus_frame)
        
        scroll_layout.addWidget(bonus_group)
        
        # UI Preferences Section
        ui_group = QtWidgets.QGroupBox("User Interface Preferences")
        ui_group.setStyleSheet(common_groupbox_style)
        ui_layout = QtWidgets.QVBoxLayout(ui_group)
        
        self.show_boundary_warnings = QtWidgets.QCheckBox("Display warnings for tasks outside defined week boundaries")
        self.show_boundary_warnings.setChecked(True)
        self.show_boundary_warnings.setStyleSheet("QCheckBox { color: #CCCCCC; }")
        ui_layout.addWidget(self.show_boundary_warnings)
        
        self.auto_suggest_weeks = QtWidgets.QCheckBox("Automatically suggest creation of new weeks for out-of-boundary tasks")
        self.auto_suggest_weeks.setChecked(True)
        self.auto_suggest_weeks.setStyleSheet("QCheckBox { color: #CCCCCC; }")
        ui_layout.addWidget(self.auto_suggest_weeks)
        
        scroll_layout.addWidget(ui_group)
        
        scroll_layout.addStretch()
        
        # Set scroll content
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        info_label = QtWidgets.QLabel("💡 These settings can be modified later via File > Preferences.")
        info_label.setStyleSheet("QLabel { color: #B0B0B0; font-style: italic; font-size: 12px; }") # Adjusted color and font size
        button_layout.addWidget(info_label)
        button_layout.addStretch()
        
        self.finish_btn = QtWidgets.QPushButton("Complete Setup")
        self.finish_btn.setStyleSheet("""
            QPushButton {
                background-color: #3A3A3A;
                color: #E0E0E0;
                font-weight: normal;
                padding: 2px 5px;
                border-radius: 3px;
                font-size: 11px;
                border: 1px solid #555555;
            }
            QPushButton:hover {
                background-color: #4A4A4A;
            }
            QPushButton:pressed {
                background-color: #2A2A2A;
            }
        """)
        self.finish_btn.clicked.connect(self.complete_setup)
        button_layout.addWidget(self.finish_btn)
        
        main_layout.addLayout(button_layout)
    
    def load_default_values(self):
        """Load default values into the form"""
        # Week settings
        self.start_day_combo.setCurrentIndex(DEFAULT_GLOBAL_SETTINGS["week_settings"]["default_week_start_day"] - 1)
        self.start_hour_spinbox.setValue(DEFAULT_GLOBAL_SETTINGS["week_settings"]["default_week_start_hour"])
        self.end_day_combo.setCurrentIndex(DEFAULT_GLOBAL_SETTINGS["week_settings"]["default_week_end_day"] - 1)
        self.end_hour_spinbox.setValue(DEFAULT_GLOBAL_SETTINGS["week_settings"]["default_week_end_hour"])
        self.enforce_week_duration.setChecked(DEFAULT_GLOBAL_SETTINGS["week_settings"]["enforce_exact_week_duration"])
        
        # Bonus settings
        self.bonus_start_day_combo.setCurrentIndex(DEFAULT_GLOBAL_SETTINGS["bonus_settings"]["default_bonus_start_day"] - 1)
        self.bonus_start_time.setTime(QtCore.QTime.fromString(DEFAULT_GLOBAL_SETTINGS["bonus_settings"]["default_bonus_start_time"], "HH:mm"))
        self.bonus_end_day_combo.setCurrentIndex(DEFAULT_GLOBAL_SETTINGS["bonus_settings"]["default_bonus_end_day"] - 1)
        self.bonus_end_time.setTime(QtCore.QTime.fromString(DEFAULT_GLOBAL_SETTINGS["bonus_settings"]["default_bonus_end_time"], "HH:mm"))
        
        # Payrates
        self.regular_payrate_spinbox.setValue(DEFAULT_GLOBAL_SETTINGS["ui_settings"]["default_payrate"])
        self.bonus_payrate_spinbox.setValue(DEFAULT_GLOBAL_SETTINGS["bonus_settings"]["default_bonus_payrate"])
        
        # Task bonus
        self.enable_task_bonus.setChecked(DEFAULT_GLOBAL_SETTINGS["bonus_settings"]["default_enable_task_bonus"])
        self.task_threshold_spinbox.setValue(DEFAULT_GLOBAL_SETTINGS["bonus_settings"]["default_bonus_task_threshold"])
        self.additional_bonus_spinbox.setValue(DEFAULT_GLOBAL_SETTINGS["bonus_settings"]["default_bonus_additional_amount"])

        # UI Preferences
        self.show_boundary_warnings.setChecked(DEFAULT_GLOBAL_SETTINGS["ui_settings"]["show_week_boundary_warnings"])
        self.auto_suggest_weeks.setChecked(DEFAULT_GLOBAL_SETTINGS["ui_settings"]["auto_suggest_new_week"])
    
    def complete_setup(self):
        """Save settings and complete first startup"""
        try:
            # Save week settings
            global_settings.set_setting("week_settings.default_week_start_day", self.start_day_combo.currentIndex() + 1)
            global_settings.set_setting("week_settings.default_week_start_hour", self.start_hour_spinbox.value())
            global_settings.set_setting("week_settings.default_week_end_day", self.end_day_combo.currentIndex() + 1)
            global_settings.set_setting("week_settings.default_week_end_hour", self.end_hour_spinbox.value())
            global_settings.set_setting("week_settings.enforce_exact_week_duration", self.enforce_week_duration.isChecked())
            
            # Save bonus settings
            global_settings.set_setting("bonus_settings.default_bonus_start_day", self.bonus_start_day_combo.currentIndex())
            global_settings.set_setting("bonus_settings.default_bonus_start_time", self.bonus_start_time.text())
            global_settings.set_setting("bonus_settings.default_bonus_end_day", self.bonus_end_day_combo.currentIndex())
            global_settings.set_setting("bonus_settings.default_bonus_end_time", self.bonus_end_time.text())
            global_settings.set_setting("bonus_settings.default_bonus_payrate", self.bonus_payrate_spinbox.value())
            global_settings.set_setting("bonus_settings.default_enable_task_bonus", self.enable_task_bonus.isChecked())
            global_settings.set_setting("bonus_settings.default_bonus_task_threshold", self.task_threshold_spinbox.value())
            global_settings.set_setting("bonus_settings.default_bonus_additional_amount", self.additional_bonus_spinbox.value())
            
            # Save UI settings
            global_settings.set_setting("ui_settings.default_payrate", self.regular_payrate_spinbox.value())
            global_settings.set_setting("ui_settings.show_week_boundary_warnings", self.show_boundary_warnings.isChecked())
            global_settings.set_setting("ui_settings.auto_suggest_new_week", self.auto_suggest_weeks.isChecked())
            
            # Mark first startup as completed
            global_settings.mark_first_startup_completed()
            
            # Show completion message
            QtWidgets.QMessageBox.information(
                self,
                "Setup Complete",
                "Your settings have been saved successfully!\n\nWelcome to Auditor Helper! 🚀"
            )
            
            self.accept()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Setup Error",
                f"An error occurred while saving your settings:\n{str(e)}\n\nPlease try again."
            )
    
    def closeEvent(self, event):
        """Prevent closing without completing setup"""
        reply = QtWidgets.QMessageBox.question(
            self,
            "Incomplete Setup",
            "You haven't completed the initial setup yet.\n\nAre you sure you want to exit? The application may not work properly without proper configuration.",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            # Use default settings if user insists on exiting
            global_settings.mark_first_startup_completed()
            event.accept()
        else:
            event.ignore() 