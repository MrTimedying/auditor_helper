from PySide6 import QtWidgets, QtCore, QtGui
import os
from ..theme_manager import ThemeManager
from ...updater.update_dialog import UpdateCheckWidget

basedir = os.path.dirname(__file__)

class OptionsDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, theme_manager=None, initial_dark_mode=True):
        super().__init__(parent)
        self.setWindowTitle("Preferences")
        self.setWindowIcon(QtGui.QIcon(os.path.join(basedir, "icons", "app_icon.ico")))
        self.resize(800, 600)

        self.theme_manager = theme_manager
        self.dark_mode = initial_dark_mode

        self.main_layout = QtWidgets.QHBoxLayout(self)

        # Sidebar for categories
        self.sidebar_list_widget = QtWidgets.QListWidget()
        self.sidebar_list_widget.setFixedWidth(180)
        self.sidebar_list_widget.setObjectName("OptionsSidebar")
        
        # Add categories
        categories = [
            ("General", "🔧"),
            ("Appearance", "🎨"), 
            ("Global Defaults", "🌐"),
            ("Week Customization", "📅"),
            ("Updates", "🔄")
        ]
        
        for name, icon in categories:
            item = QtWidgets.QListWidgetItem(f"{icon} {name}")
            item.setData(QtCore.Qt.UserRole, name)
            self.sidebar_list_widget.addItem(item)

        # Content area
        self.content_stack = QtWidgets.QStackedWidget()

        # Create pages
        self.create_general_page()
        self.create_appearance_page()
        self.create_global_defaults_page()
        self.create_week_customization_page()
        self.create_updates_page()

        # Connect sidebar selection
        self.sidebar_list_widget.currentRowChanged.connect(self.content_stack.setCurrentIndex)
        self.sidebar_list_widget.setCurrentRow(0)

        # Layout
        self.main_layout.addWidget(self.sidebar_list_widget)
        self.main_layout.addWidget(self.content_stack, 1)

        # Buttons
        self.button_layout = QtWidgets.QHBoxLayout()
        self.button_layout.addStretch()
        
        self.save_btn = QtWidgets.QPushButton("Save")
        self.cancel_btn = QtWidgets.QPushButton("Cancel")
        
        self.save_btn.clicked.connect(self.save_settings)
        self.cancel_btn.clicked.connect(self.reject)
        
        self.button_layout.addWidget(self.save_btn)
        self.button_layout.addWidget(self.cancel_btn)

        # Add buttons to main layout
        main_widget = QtWidgets.QWidget()
        main_widget.setLayout(self.main_layout)
        
        final_layout = QtWidgets.QVBoxLayout(self)
        final_layout.addWidget(main_widget, 1)
        final_layout.addLayout(self.button_layout)

        self.load_settings()

    def create_general_page(self):
        """General application settings"""
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        
        # Title
        title = QtWidgets.QLabel("General Settings")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Boundary warnings
        self.boundary_warnings_cb = QtWidgets.QCheckBox("Enable week boundary warnings")
        self.boundary_warnings_cb.setToolTip("Warn when tasks would fall outside current week boundaries")
        layout.addWidget(self.boundary_warnings_cb)
        
        # Auto suggestions
        self.auto_suggestions_cb = QtWidgets.QCheckBox("Enable automatic week suggestions")
        self.auto_suggestions_cb.setToolTip("Automatically suggest creating new weeks for out-of-boundary tasks")
        layout.addWidget(self.auto_suggestions_cb)
        
        layout.addStretch()
        self.content_stack.addWidget(page)

    def create_appearance_page(self):
        """Appearance and theme settings"""
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        
        # Title
        title = QtWidgets.QLabel("Appearance Settings")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Theme selection
        theme_group = QtWidgets.QGroupBox("Theme")
        theme_layout = QtWidgets.QVBoxLayout(theme_group)
        
        self.dark_mode_rb = QtWidgets.QRadioButton("Dark Mode")
        self.light_mode_rb = QtWidgets.QRadioButton("Light Mode")
        
        theme_layout.addWidget(self.dark_mode_rb)
        theme_layout.addWidget(self.light_mode_rb)
        
        layout.addWidget(theme_group)
        layout.addStretch()
        self.content_stack.addWidget(page)

    def create_global_defaults_page(self):
        """Global default settings"""
        page = QtWidgets.QWidget()
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(page)
        
        layout = QtWidgets.QVBoxLayout(page)
        
        # Title
        title = QtWidgets.QLabel("Global Default Settings")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
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
        
        self.task_threshold_spin = QtWidgets.QSpinBox()
        self.task_threshold_spin.setRange(1, 999)
        self.task_threshold_spin.setSuffix(" tasks")
        
        self.additional_bonus_spin = QtWidgets.QDoubleSpinBox()
        self.additional_bonus_spin.setRange(0.0, 999.99)
        self.additional_bonus_spin.setDecimals(2)
        self.additional_bonus_spin.setPrefix("$")
        
        task_bonus_layout.addRow("", self.enable_task_bonus_cb)
        task_bonus_layout.addRow("Task Threshold:", self.task_threshold_spin)
        task_bonus_layout.addRow("Additional Amount:", self.additional_bonus_spin)
        
        layout.addWidget(task_bonus_group)
        
        # Default Week Duration
        week_duration_group = QtWidgets.QGroupBox("Default Week Duration")
        week_duration_layout = QtWidgets.QFormLayout(week_duration_group)
        
        # Start day/hour
        start_week_layout = QtWidgets.QHBoxLayout()
        self.default_start_day_combo = QtWidgets.QComboBox()
        self.default_start_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        
        self.default_start_hour_spin = QtWidgets.QSpinBox()
        self.default_start_hour_spin.setRange(0, 23)
        self.default_start_hour_spin.setSuffix(":00")
        
        start_week_layout.addWidget(self.default_start_day_combo)
        start_week_layout.addWidget(self.default_start_hour_spin)
        
        # End day/hour
        end_week_layout = QtWidgets.QHBoxLayout()
        self.default_end_day_combo = QtWidgets.QComboBox()
        self.default_end_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        
        self.default_end_hour_spin = QtWidgets.QSpinBox()
        self.default_end_hour_spin.setRange(0, 23)
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
        self.content_stack.addWidget(scroll)

    def create_week_customization_page(self):
        """Week-specific customization settings"""
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        
        # Title
        title = QtWidgets.QLabel("Week Customization")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Week selection
        week_selection_layout = QtWidgets.QHBoxLayout()
        week_selection_layout.addWidget(QtWidgets.QLabel("Select Week:"))
        
        self.week_combo = QtWidgets.QComboBox()
        self.week_combo.currentTextChanged.connect(self.load_week_settings)
        week_selection_layout.addWidget(self.week_combo)
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
        
        self.week_start_hour_spin = QtWidgets.QSpinBox()
        self.week_start_hour_spin.setRange(0, 23)
        self.week_start_hour_spin.setSuffix(":00")
        
        start_layout.addWidget(self.week_start_day_combo)
        start_layout.addWidget(self.week_start_hour_spin)
        
        # End day/hour
        end_layout = QtWidgets.QHBoxLayout()
        self.week_end_day_combo = QtWidgets.QComboBox()
        self.week_end_day_combo.addItems(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"])
        
        self.week_end_hour_spin = QtWidgets.QSpinBox()
        self.week_end_hour_spin.setRange(0, 23)
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
        
        self.week_task_threshold_spin = QtWidgets.QSpinBox()
        self.week_task_threshold_spin.setRange(1, 999)
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
        
        layout.addStretch()
        self.content_stack.addWidget(page)

    def create_updates_page(self):
        """Updates and maintenance settings"""
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        
        # Title
        title = QtWidgets.QLabel("Updates")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Update check widget
        self.update_widget = UpdateCheckWidget()
        layout.addWidget(self.update_widget)
        
        layout.addStretch()
        self.content_stack.addWidget(page)

    def toggle_global_bonus_controls(self, enabled):
        """Enable/disable global bonus controls based on master toggle"""
        for control in self.global_bonus_controls:
            control.setEnabled(enabled)

    def toggle_duration_controls(self, enabled):
        """Enable/disable duration controls based on custom duration toggle"""
        for control in self.duration_controls:
            control.setEnabled(enabled)

    def toggle_week_bonus_controls(self, use_global):
        """Enable/disable week-specific bonus controls"""
        for control in self.week_bonus_controls:
            control.setEnabled(not use_global)

    def load_settings(self):
        """Load settings from global_settings and database"""
        try:
            from global_settings import GlobalSettings
            global_settings = GlobalSettings()
            
            # General settings
            self.boundary_warnings_cb.setChecked(global_settings.get_boundary_warnings_enabled())
            self.auto_suggestions_cb.setChecked(global_settings.get_auto_suggestions_enabled())
            
            # Appearance
            if self.dark_mode:
                self.dark_mode_rb.setChecked(True)
            else:
                self.light_mode_rb.setChecked(True)
            
            # Global defaults
            self.global_bonus_enabled_cb.setChecked(global_settings.is_global_bonus_enabled())
            self.regular_payrate_spin.setValue(global_settings.get_regular_payrate())
            self.bonus_payrate_spin.setValue(global_settings.get_bonus_payrate())
            
            # Bonus time windows
            self.bonus_start_day_combo.setCurrentIndex(global_settings.get_bonus_start_day())
            self.bonus_start_time_edit.setTime(QtCore.QTime.fromString(global_settings.get_bonus_start_time(), "HH:mm"))
            self.bonus_end_day_combo.setCurrentIndex(global_settings.get_bonus_end_day())
            self.bonus_end_time_edit.setTime(QtCore.QTime.fromString(global_settings.get_bonus_end_time(), "HH:mm"))
            
            # Task bonus
            self.enable_task_bonus_cb.setChecked(global_settings.get_enable_task_bonus())
            self.task_threshold_spin.setValue(global_settings.get_bonus_task_threshold())
            self.additional_bonus_spin.setValue(global_settings.get_bonus_additional_amount())
            
            # Default week duration
            self.default_start_day_combo.setCurrentIndex(global_settings.get_default_week_start_day())
            self.default_start_hour_spin.setValue(global_settings.get_default_week_start_hour())
            self.default_end_day_combo.setCurrentIndex(global_settings.get_default_week_end_day())
            self.default_end_hour_spin.setValue(global_settings.get_default_week_end_hour())
            
            # Load weeks for customization
            self.load_weeks()
            
            # Apply initial toggles
            self.toggle_global_bonus_controls(self.global_bonus_enabled_cb.isChecked())
            
        except Exception as e:
            print(f"Error loading settings: {e}")

    def load_weeks(self):
        """Load available weeks into the week combo box"""
        try:
            import sqlite3
            conn = sqlite3.connect('tasks.db')
            c = conn.cursor()
            
            c.execute("SELECT week_label FROM weeks ORDER BY id")
            weeks = c.fetchall()
            
            self.week_combo.clear()
            for week in weeks:
                self.week_combo.addItem(week[0])
            
            conn.close()
            
            if self.week_combo.count() > 0:
                self.load_week_settings()
                
        except Exception as e:
            print(f"Error loading weeks: {e}")

    def load_week_settings(self):
        """Load settings for the selected week"""
        if not self.week_combo.currentText():
            return
            
        try:
            import sqlite3
            conn = sqlite3.connect('tasks.db')
            c = conn.cursor()
            
            c.execute("""
                SELECT week_start_day, week_start_hour, week_end_day, week_end_hour, 
                       is_custom_duration, week_specific_bonus_payrate, 
                       week_specific_bonus_start_day, week_specific_bonus_start_time,
                       week_specific_bonus_end_day, week_specific_bonus_end_time,
                       week_specific_enable_task_bonus, week_specific_bonus_task_threshold,
                       week_specific_bonus_additional_amount, use_global_bonus_settings
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
                
                # Apply toggles
                self.toggle_duration_controls(self.custom_duration_cb.isChecked())
                self.toggle_week_bonus_controls(self.use_global_bonus_cb.isChecked())
                
        except Exception as e:
            print(f"Error loading week settings: {e}")

    def save_settings(self):
        """Save all settings"""
        try:
            from global_settings import GlobalSettings
            global_settings = GlobalSettings()
            
            # General settings
            global_settings.set_boundary_warnings_enabled(self.boundary_warnings_cb.isChecked())
            global_settings.set_auto_suggestions_enabled(self.auto_suggestions_cb.isChecked())
            
            # Global defaults
            global_settings.set_global_bonus_enabled(self.global_bonus_enabled_cb.isChecked())
            global_settings.set_regular_payrate(self.regular_payrate_spin.value())
            global_settings.set_bonus_payrate(self.bonus_payrate_spin.value())
            
            # Bonus time windows
            global_settings.set_bonus_start_day(self.bonus_start_day_combo.currentIndex())
            global_settings.set_bonus_start_time(self.bonus_start_time_edit.time().toString("HH:mm"))
            global_settings.set_bonus_end_day(self.bonus_end_day_combo.currentIndex())
            global_settings.set_bonus_end_time(self.bonus_end_time_edit.time().toString("HH:mm"))
            
            # Task bonus
            global_settings.set_enable_task_bonus(self.enable_task_bonus_cb.isChecked())
            global_settings.set_bonus_task_threshold(self.task_threshold_spin.value())
            global_settings.set_bonus_additional_amount(self.additional_bonus_spin.value())
            
            # Default week duration
            global_settings.set_default_week_start_day(self.default_start_day_combo.currentIndex())
            global_settings.set_default_week_start_hour(self.default_start_hour_spin.value())
            global_settings.set_default_week_end_day(self.default_end_day_combo.currentIndex())
            global_settings.set_default_week_end_hour(self.default_end_hour_spin.value())
            
            global_settings.save()
            
            # Save week-specific settings
            self.save_week_settings()
            
            # Apply theme change if needed
            if self.theme_manager:
                new_dark_mode = self.dark_mode_rb.isChecked()
                if new_dark_mode != self.dark_mode:
                    self.theme_manager.set_dark_mode(new_dark_mode)
            
            QtWidgets.QMessageBox.information(self, "Success", "Settings saved successfully!")
            self.accept()
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Failed to save settings: {e}")

    def save_week_settings(self):
        """Save week-specific settings"""
        if not self.week_combo.currentText():
            return
            
        try:
            import sqlite3
            conn = sqlite3.connect('tasks.db')
            c = conn.cursor()
            
            # Prepare values
            week_label = self.week_combo.currentText()
            is_custom_duration = 1 if self.custom_duration_cb.isChecked() else 0
            week_start_day = self.week_start_day_combo.currentIndex() + 1  # Convert to 1-based
            week_start_hour = self.week_start_hour_spin.value()
            week_end_day = self.week_end_day_combo.currentIndex() + 1  # Convert to 1-based
            week_end_hour = self.week_end_hour_spin.value()
            
            use_global_bonus = 1 if self.use_global_bonus_cb.isChecked() else 0
            
            # Week-specific bonus values (NULL if using global)
            if use_global_bonus:
                bonus_values = [None] * 8  # All NULL
            else:
                bonus_values = [
                    self.week_bonus_payrate_spin.value(),
                    self.week_bonus_start_day_combo.currentIndex(),
                    self.week_bonus_start_time_edit.time().toString("HH:mm"),
                    self.week_bonus_end_day_combo.currentIndex(),
                    self.week_bonus_end_time_edit.time().toString("HH:mm"),
                    1 if self.week_enable_task_bonus_cb.isChecked() else 0,
                    self.week_task_threshold_spin.value(),
                    self.week_additional_bonus_spin.value()
                ]
            
            c.execute("""
                UPDATE weeks SET 
                    week_start_day = ?, week_start_hour = ?, week_end_day = ?, week_end_hour = ?,
                    is_custom_duration = ?, week_specific_bonus_payrate = ?,
                    week_specific_bonus_start_day = ?, week_specific_bonus_start_time = ?,
                    week_specific_bonus_end_day = ?, week_specific_bonus_end_time = ?,
                    week_specific_enable_task_bonus = ?, week_specific_bonus_task_threshold = ?,
                    week_specific_bonus_additional_amount = ?, use_global_bonus_settings = ?
                WHERE week_label = ?
            """, (week_start_day, week_start_hour, week_end_day, week_end_hour, is_custom_duration,
                  *bonus_values, use_global_bonus, week_label))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Error saving week settings: {e}")
            raise