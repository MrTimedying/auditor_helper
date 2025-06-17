from PySide6 import QtCore, QtWidgets, QtGui
from typing import Dict, Any
import os # Added for path handling
import logging

from analysis.analysis_module.drag_drop_list_widget import DragDropListWidget
from analysis.analysis_module.data_manager import DataManager
from core.settings.global_settings import global_settings, get_icon_path
from ui.ui_components.collapsible_pane import CollapsiblePane

# Event Bus imports
from core.events import get_event_bus, EventType

# Conditional chart imports - graceful degradation for light version
try:
    from PySide6.QtCharts import QChart, QChartView
    from analysis.analysis_module.chart_manager import ChartManager
    from analysis.analysis_module.chart_constraints import (
        get_allowed_x_variables, get_allowed_y_variables, get_allowed_chart_types,
        get_compatible_chart_types, validate_variable_combination
    )
    CHARTS_AVAILABLE = True
    logging.info("Charts module loaded successfully - Full version")
except ImportError as e:
    logging.info(f"Charts module not available - Light version: {e}")
    CHARTS_AVAILABLE = False
    
    # Placeholder for chart-related functions when not available
    QChart = None
    QChartView = None
    ChartManager = None
    get_allowed_x_variables = None
    get_allowed_y_variables = None
    get_allowed_chart_types = None
    get_compatible_chart_types = None
    validate_variable_combination = None

basedir = os.path.dirname(__file__)

class AnalysisWidget(QtWidgets.QMainWindow):
    def __init__(self, parent=None): 
        super().__init__(parent)
        self.setWindowTitle("Data Analysis")
        self.setWindowFlags(QtCore.Qt.Window)
        self.resize(1200, 800)  # Set a reasonable default size
        self.setWindowIcon(QtGui.QIcon(get_icon_path("app_icon.ico"))) # Set app icon using utility function
        
        # Create a central widget to hold all existing content
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

        # Initialize Event Bus
        self.event_bus = get_event_bus()
        
        # Initialize DataManager
        self.data_manager = DataManager()
        
        # Create main scroll area
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        
        # Main content widget
        content_widget = QtWidgets.QWidget()
        scroll_area.setWidget(content_widget)

        main_layout = QtWidgets.QVBoxLayout(self.central_widget) # Apply layout to central widget
        main_layout.addWidget(scroll_area)
        
        content_layout = QtWidgets.QVBoxLayout(content_widget)
        content_layout.setSpacing(10)  # Reduced spacing
        content_layout.setContentsMargins(10, 10, 10, 10)  # Reduced margins
        
        # Data Selection Section
        self.create_data_selection_controls(content_layout)
        
        # Create tabs: Numerical Statistics and conditionally Graphs
        self.tabs = QtWidgets.QTabWidget()
        content_layout.addWidget(self.tabs)

        self.numerical_tab = QtWidgets.QWidget()
        self.tabs.addTab(self.numerical_tab, "Numerical Statistics")
        
        # Conditionally create graphs tab based on chart availability
        if CHARTS_AVAILABLE:
            self.graphs_tab = QtWidgets.QWidget()
            self.tabs.addTab(self.graphs_tab, "Graphs")
        else:
            self.graphs_tab = None
            self._add_light_version_info()

        # Setup tabs
        self.setup_numerical_statistics_tab()
        
        # Chart-related initialization only if charts are available
        if CHARTS_AVAILABLE:
            self.setup_graphs_tab()
            
            # Initialize ChartManager after chart_view is created
            self.chart_manager = ChartManager(self.chart_view)
            
            # Initialize intelligent suggestion system
            from analysis.analysis_module.variable_suggestions import IntelligentVariableSuggester
            self.suggestion_engine = IntelligentVariableSuggester()
            
            # Populate theme combo with available themes
            self.populate_theme_combo()
        else:
            # Light version - no chart components
            self.chart_manager = None
            self.suggestion_engine = None
        
        # Initialize data
        self.current_week_id = None
        self.current_start_date = None
        self.current_end_date = None
        
        # Setup event bus listeners
        self.setup_event_bus_listeners()

    def _add_light_version_info(self):
        """Add informational tab for light version explaining missing charting features"""
        info_tab = QtWidgets.QWidget()
        self.tabs.addTab(info_tab, "Charts (Upgrade Available)")
        
        info_layout = QtWidgets.QVBoxLayout(info_tab)
        info_layout.setSpacing(20)
        info_layout.setContentsMargins(40, 40, 40, 40)
        
        # Title
        title_label = QtWidgets.QLabel("📊 Advanced Charting Available in Full Version")
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #D6D6D6;
                margin-bottom: 10px;
            }
        """)
        title_label.setAlignment(QtCore.Qt.AlignCenter)
        info_layout.addWidget(title_label)
        
        # Description
        description_label = QtWidgets.QLabel("""
        <div style='text-align: center; line-height: 1.6;'>
        <p style='font-size: 14px; color: #B0B0B0; margin-bottom: 20px;'>
        You're using <strong>Auditor Helper Light</strong> - perfect for essential task tracking and numerical analysis.
        </p>
        
        <p style='font-size: 13px; color: #A0A0A0; margin-bottom: 15px;'>
        <strong>The Full Version includes advanced charting features:</strong>
        </p>
        
        <ul style='text-align: left; display: inline-block; font-size: 12px; color: #909090;'>
        <li>📈 Interactive line, bar, scatter, and pie charts</li>
        <li>📊 Statistical box plots and heatmaps</li>
        <li>🎨 15+ professional themes and gradient palettes</li>
        <li>✨ Smooth animations and visual effects</li>
        <li>📤 High-quality chart export (SVG, PDF, PNG)</li>
        <li>🔍 Advanced analytics with correlation analysis</li>
        <li>⚡ Background rendering for complex visualizations</li>
        </ul>
        
        <p style='font-size: 12px; color: #808080; margin-top: 20px;'>
        All numerical statistics and task management features are fully available in this version.
        </p>
        </div>
        """)
        description_label.setWordWrap(True)
        description_label.setAlignment(QtCore.Qt.AlignCenter)
        info_layout.addWidget(description_label)
        
        # Spacer
        info_layout.addStretch()
        
        # Version info
        version_label = QtWidgets.QLabel("Auditor Helper Light v0.18.3")
        version_label.setStyleSheet("""
            QLabel {
                font-size: 10px;
                color: #606060;
                margin-top: 20px;
            }
        """)
        version_label.setAlignment(QtCore.Qt.AlignCenter)
        info_layout.addWidget(version_label)

    def setup_event_bus_listeners(self):
        """Set up event bus listeners for analysis widget"""
        # Task-related events that should trigger analysis refresh
        self.event_bus.connect_handler(EventType.TASK_CREATED, self.on_task_event)
        self.event_bus.connect_handler(EventType.TASK_UPDATED, self.on_task_event)
        self.event_bus.connect_handler(EventType.TASK_DELETED, self.on_task_event)
        self.event_bus.connect_handler(EventType.TASKS_BULK_UPDATED, self.on_task_event)
        
        # Week-related events
        self.event_bus.connect_handler(EventType.WEEK_CREATED, self.on_week_event)
        self.event_bus.connect_handler(EventType.WEEK_DELETED, self.on_week_event)
        self.event_bus.connect_handler(EventType.WEEK_CHANGED, self.on_week_changed_event)
        
        # Timer events that might affect analysis
        self.event_bus.connect_handler(EventType.TIMER_STOPPED, self.on_timer_stopped_event)
        
        # Analysis-specific events
        self.event_bus.connect_handler(EventType.ANALYSIS_REFRESH_REQUESTED, self.on_analysis_refresh_requested_event)

    def on_task_event(self, event_data):
        """Handle task-related events that should trigger analysis refresh"""
        # Only refresh if we have an active analysis context
        if self.current_week_id or (self.current_start_date and self.current_end_date):
            # Emit analysis refresh event to notify other components
            self.event_bus.emit_event(
                EventType.ANALYSIS_REFRESH_REQUESTED,
                {
                    'reason': 'task_data_changed',
                    'source_event': event_data.event_type.value,
                    'week_id': self.current_week_id,
                    'start_date': self.current_start_date.isoformat() if self.current_start_date else None,
                    'end_date': self.current_end_date.isoformat() if self.current_end_date else None
                },
                'AnalysisWidget'
            )
            
            # Refresh the analysis
            if self.current_week_id:
                self.refresh_analysis_by_week(self.current_week_id)
            elif self.current_start_date and self.current_end_date:
                self.refresh_analysis_by_time_range(self.current_start_date, self.current_end_date)

    def on_week_event(self, event_data):
        """Handle week-related events"""
        # Refresh week combo to show new/updated weeks
        self.refresh_week_combo()
        
        # If the current week was deleted, clear the analysis
        if event_data.event_type == EventType.WEEK_DELETED:
            deleted_week_id = event_data.data.get('week_id')
            if deleted_week_id == self.current_week_id:
                self.clear_all_data()
                self.current_week_id = None

    def on_week_changed_event(self, event_data):
        """Handle week changed events from other components"""
        week_id = event_data.data.get('week_id')
        
        # Update our week combo selection to match
        if week_id:
            for i in range(self.week_combo.count()):
                if self.week_combo.itemData(i) == week_id:
                    self.week_combo.setCurrentIndex(i)
                    break

    def on_timer_stopped_event(self, event_data):
        """Handle timer stopped events that might affect analysis"""
        # Only refresh if the timer was for a task in our current analysis context
        task_id = event_data.data.get('task_id')
        duration_changed = event_data.data.get('duration_changed', False)
        
        if duration_changed and (self.current_week_id or (self.current_start_date and self.current_end_date)):
            # Refresh analysis to reflect updated task durations
            if self.current_week_id:
                self.refresh_analysis_by_week(self.current_week_id)
            elif self.current_start_date and self.current_end_date:
                self.refresh_analysis_by_time_range(self.current_start_date, self.current_end_date)

    def on_analysis_refresh_requested_event(self, event_data):
        """Handle analysis refresh requests from other components"""
        # Only respond to external requests (not our own)
        if event_data.source != 'AnalysisWidget':
            reason = event_data.data.get('reason')
            week_id = event_data.data.get('week_id')
            
            # Refresh based on the request
            if week_id and week_id == self.current_week_id:
                self.refresh_analysis_by_week(week_id)
            elif self.current_start_date and self.current_end_date:
                self.refresh_analysis_by_time_range(self.current_start_date, self.current_end_date)

    def create_data_selection_controls(self, main_layout):
        """Create the data selection controls for time range and week selection"""
        selection_group = QtWidgets.QGroupBox("Data Selection & Analysis Context")
        # Note: Styling handled by main stylesheet
        selection_layout = QtWidgets.QHBoxLayout(selection_group)
        selection_layout.setSpacing(20)  # More spacing between left and right sections
        selection_layout.setContentsMargins(10, 10, 10, 10)
        
        # === LEFT SIDE: Time Selectors (Stacked Vertically) ===
        left_panel = QtWidgets.QWidget()
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setSpacing(10)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Time Range Selection
        time_range_group = QtWidgets.QGroupBox("Time Range Selection")
        time_range_layout = QtWidgets.QHBoxLayout(time_range_group)
        time_range_layout.setSpacing(8)
        time_range_layout.setContentsMargins(8, 8, 8, 8)
        
        from_label = QtWidgets.QLabel("From:")
        from_label.setMinimumWidth(40)
        time_range_layout.addWidget(from_label)
        
        self.start_date_edit = QtWidgets.QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QtCore.QDate.currentDate().addDays(-30))
        self.start_date_edit.setMinimumWidth(120)
        time_range_layout.addWidget(self.start_date_edit)
        
        to_label = QtWidgets.QLabel("To:")
        to_label.setMinimumWidth(25)
        time_range_layout.addWidget(to_label)
        
        self.end_date_edit = QtWidgets.QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QtCore.QDate.currentDate())
        self.end_date_edit.setMinimumWidth(120)
        time_range_layout.addWidget(self.end_date_edit)
        
        self.apply_time_range_btn = QtWidgets.QPushButton("Apply Time Range")
        self.apply_time_range_btn.setMinimumWidth(120)
        self.apply_time_range_btn.clicked.connect(self.apply_time_range_selection)
        time_range_layout.addWidget(self.apply_time_range_btn)
        
        left_layout.addWidget(time_range_group)
        
        # Week Selection (Below Time Range)
        week_group = QtWidgets.QGroupBox("Specific Week Selection")
        week_layout = QtWidgets.QHBoxLayout(week_group)
        week_layout.setSpacing(8)
        week_layout.setContentsMargins(8, 8, 8, 8)
        
        week_label = QtWidgets.QLabel("Week:")
        week_label.setMinimumWidth(40)
        week_layout.addWidget(week_label)
        
        self.week_combo = QtWidgets.QComboBox()
        self.week_combo.addItem("Select a week...", None)
        self.week_combo.setMinimumWidth(200)  # Wider for better readability
        self.populate_week_combo()
        week_layout.addWidget(self.week_combo)
        
        self.apply_week_btn = QtWidgets.QPushButton("Apply Week")
        self.apply_week_btn.setMinimumWidth(100)
        self.apply_week_btn.clicked.connect(self.apply_week_selection)
        week_layout.addWidget(self.apply_week_btn)
        
        left_layout.addWidget(week_group)
        left_layout.addStretch()  # Push content to top
        
        selection_layout.addWidget(left_panel)
        
        # === RIGHT SIDE: Analysis Context (More Informative) ===
        context_group = QtWidgets.QGroupBox("Analysis Context & Settings")
        context_layout = QtWidgets.QVBoxLayout(context_group)
        context_layout.setSpacing(8)
        context_layout.setContentsMargins(12, 12, 12, 12)
        
        # Current Selection Status
        self.current_selection_label = QtWidgets.QLabel("Selection: No data selected")
        self.current_selection_label.setStyleSheet("font-weight: bold; color: #e2e8f0; font-size: 12px;")
        self.current_selection_label.setWordWrap(True)
        context_layout.addWidget(self.current_selection_label)
        
        # Selection Details
        self.selection_details_label = QtWidgets.QLabel("Select a time range or specific week to begin analysis")
        self.selection_details_label.setStyleSheet("color: #94a3b8; font-size: 10px; margin-top: 4px;")
        self.selection_details_label.setWordWrap(True)
        context_layout.addWidget(self.selection_details_label)
        
        # Separator
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setStyleSheet("QFrame { color: #3a3b3a; margin: 4px 0px; }")
        context_layout.addWidget(separator)
        
        # Global Settings Info
        self.global_settings_label = QtWidgets.QLabel("Global Settings: Loading...")
        self.global_settings_label.setStyleSheet("color: #94a3b8; font-size: 10px;")
        self.global_settings_label.setWordWrap(True)
        context_layout.addWidget(self.global_settings_label)
        
        # Week-specific Custom Settings (initially hidden)
        self.week_custom_settings_label = QtWidgets.QLabel("")
        self.week_custom_settings_label.setStyleSheet("color: #fbbf24; font-size: 9px; margin-top: 4px;")
        self.week_custom_settings_label.setWordWrap(True)
        self.week_custom_settings_label.setVisible(False)
        context_layout.addWidget(self.week_custom_settings_label)
        
        context_layout.addStretch()  # Push content to top
        
        selection_layout.addWidget(context_group)
        
        main_layout.addWidget(selection_group)

    def create_bonus_status_indicator(self, main_layout):
        """This method is now integrated into create_data_selection_controls"""
        # Initialize bonus settings display
        self.update_bonus_settings_display()
    
    def update_bonus_settings_display(self):
        """Update the display of current bonus settings"""
        try:
            # Get global bonus settings
            bonus_settings = global_settings.get_default_bonus_settings()
            payrate = global_settings.get_default_payrate()
            
            # Check if global bonus is enabled
            if not bonus_settings['global_bonus_enabled']:
                self.global_settings_label.setText("Global Settings: Bonus System DISABLED")
                self.global_settings_label.setStyleSheet("color: #f87171; font-size: 10px;")  # Red for disabled
                return
            
            # Format bonus settings display
            if bonus_settings['bonus_payrate'] > payrate:
                bonus_text = f"Bonus Rate: ${bonus_settings['bonus_payrate']:.2f}/hr"
            else:
                bonus_text = "No bonus configured"
            
            if bonus_settings['enable_task_bonus']:
                task_bonus_text = f" | Task Bonus: ${bonus_settings['bonus_additional_amount']:.2f} for {bonus_settings['bonus_task_threshold']}+ tasks"
            else:
                task_bonus_text = ""
            
            self.global_settings_label.setText(f"Global Settings: ${payrate:.2f}/hr base rate | {bonus_text}{task_bonus_text}")
            self.global_settings_label.setStyleSheet("color: #94a3b8; font-size: 10px;")  # Neutral gray
        except Exception as e:
            self.global_settings_label.setText(f"Global Settings: Error loading - {str(e)}")
            self.global_settings_label.setStyleSheet("color: #f87171; font-size: 10px;")  # Red for error
    
    def update_current_status_display(self, week_id=None):
        """Update the current selection status display with more detailed information"""
        try:
            # Check if global bonus is disabled first
            bonus_settings = global_settings.get_default_bonus_settings()
            if not bonus_settings['global_bonus_enabled']:
                self.current_selection_label.setText("Selection: Bonus System Disabled")
                self.current_selection_label.setStyleSheet("font-weight: bold; color: #f87171; font-size: 12px;")
                self.selection_details_label.setText("The bonus system is currently disabled in global settings")
                self.selection_details_label.setStyleSheet("color: #f87171; font-size: 10px; margin-top: 4px;")
                self.week_custom_settings_label.setVisible(False)
                return
            
            if week_id:
                # Get all week-specific settings
                week_settings = self.data_manager.get_week_settings(week_id)
                
                # Format week display
                week_display = f"Week {week_id}"
                if 'week_start_date' in week_settings and week_settings['week_start_date']:
                    start_date = week_settings['week_start_date']
                    end_date = week_settings.get('week_end_date', start_date)
                    week_display += f" ({start_date} to {end_date})"
                
                self.current_selection_label.setText(f"Selection: {week_display}")
                self.current_selection_label.setStyleSheet("font-weight: bold; color: #22d3ee; font-size: 12px;")  # Cyan for week
                
                # Build detailed information
                details_parts = []
                
                # Duration details
                if week_settings['is_custom_duration']:
                    day_names = {1: "Monday", 2: "Tuesday", 3: "Wednesday", 4: "Thursday", 5: "Friday", 6: "Saturday", 7: "Sunday"}
                    start_day = day_names.get(week_settings['week_start_day'], "?")
                    end_day = day_names.get(week_settings['week_end_day'], "?")
                    details_parts.append(f"Custom Duration: {start_day} {week_settings['week_start_hour']}:00 - {end_day} {week_settings['week_end_hour']}:00")
                else:
                    details_parts.append("Duration: Using global week settings")

                # Bonus details
                if week_settings['is_bonus_week']:
                    if not week_settings['use_global_bonus_settings']:
                        bonus_detail = f"Custom Bonus: ${week_settings['bonus_payrate']:.2f}/hr"
                        if week_settings['enable_task_bonus']:
                            bonus_detail += f" + ${week_settings['bonus_additional_amount']:.2f} task bonus (≥{week_settings['bonus_task_threshold']} tasks)"
                        
                        # Add bonus window
                        day_names = {1: "Mon", 2: "Tue", 3: "Wed", 4: "Thu", 5: "Fri", 6: "Sat", 7: "Sun"}
                        start_day = day_names.get(week_settings['bonus_start_day'], "?")
                        end_day = day_names.get(week_settings['bonus_end_day'], "?")
                        bonus_detail += f" (Active: {start_day} {week_settings['bonus_start_time']} - {end_day} {week_settings['bonus_end_time']})"
                        details_parts.append(bonus_detail)
                    else:
                        details_parts.append("Bonus: Using global bonus settings")
                else:
                    details_parts.append("Bonus: No bonus for this week")

                # Office hours
                office_hour_count = week_settings.get('office_hour_count', 0)
                if office_hour_count > 0:
                    if not week_settings['use_global_office_hours_settings']:
                        details_parts.append(f"Office Hours: {office_hour_count} custom sessions (${week_settings['office_hour_payrate']:.2f}/hr, {week_settings['office_hour_session_duration_minutes']:.0f} min each)")
                    else:
                        details_parts.append(f"Office Hours: {office_hour_count} sessions (global settings)")
                
                self.selection_details_label.setText(" • ".join(details_parts))
                self.selection_details_label.setStyleSheet("color: #94a3b8; font-size: 10px; margin-top: 4px;")
                
                # Show custom settings warning if applicable
                has_custom = (not week_settings['use_global_bonus_settings'] and week_settings['is_bonus_week']) or \
                           week_settings['is_custom_duration'] or \
                           (office_hour_count > 0 and not week_settings['use_global_office_hours_settings'])
                
                if has_custom:
                    self.week_custom_settings_label.setText("⚠ This week has custom settings that override global defaults")
                    self.week_custom_settings_label.setVisible(True)
                else:
                    self.week_custom_settings_label.setVisible(False)
            else:
                # Time range selection or no selection
                if hasattr(self, 'start_date_edit') and hasattr(self, 'end_date_edit'):
                    start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
                    end_date = self.end_date_edit.date().toString("yyyy-MM-dd")

                    if start_date == end_date:
                        date_display = f"Single Day: {start_date}"
                    else:
                        # Calculate days
                        start_qdate = self.start_date_edit.date()
                        end_qdate = self.end_date_edit.date()
                        days_diff = start_qdate.daysTo(end_qdate) + 1
                        date_display = f"Time Range: {start_date} to {end_date} ({days_diff} days)"
                    
                    self.current_selection_label.setText(f"Selection: {date_display}")
                    self.current_selection_label.setStyleSheet("font-weight: bold; color: #a78bfa; font-size: 12px;")  # Purple for time range
                    self.selection_details_label.setText("Using global bonus settings for all tasks in this time range")
                    self.selection_details_label.setStyleSheet("color: #94a3b8; font-size: 10px; margin-top: 4px;")
                else:
                    self.current_selection_label.setText("Selection: No data selected")
                    self.current_selection_label.setStyleSheet("font-weight: bold; color: #6b7280; font-size: 12px;")
                    self.selection_details_label.setText("Select a time range or specific week to begin analysis")
                    self.selection_details_label.setStyleSheet("color: #94a3b8; font-size: 10px; margin-top: 4px;")
                
                self.week_custom_settings_label.setVisible(False)
        except Exception as e:
            self.current_selection_label.setText(f"Error: {str(e)}")
            self.current_selection_label.setStyleSheet("font-weight: bold; color: #f87171; font-size: 12px;")
            self.selection_details_label.setText("An error occurred while updating the selection details")
            self.selection_details_label.setStyleSheet("color: #f87171; font-size: 10px; margin-top: 4px;")
            self.week_custom_settings_label.setVisible(False)

    def setup_numerical_statistics_tab(self):
        """Setup the Numerical Statistics tab with data grids"""
        tab_layout = QtWidgets.QVBoxLayout(self.numerical_tab)
        tab_layout.setSpacing(10)  # Reduced spacing
        tab_layout.setContentsMargins(10, 10, 10, 10)  # Reduced margins
        
        # First Row: Time Range Aggregate and Daily Data Grids
        first_row_layout = QtWidgets.QHBoxLayout()
        first_row_layout.setSpacing(10)  # Reduced spacing
        
        # Time Range Aggregate Data Grid
        aggregate_group = QtWidgets.QGroupBox("Time Range Aggregate Data")
        # Note: Styling handled by main stylesheet
        aggregate_layout = QtWidgets.QVBoxLayout(aggregate_group)
        aggregate_layout.setContentsMargins(8, 8, 8, 8)  # Reduced margins
        
        self.aggregate_table = QtWidgets.QTableWidget()
        self.aggregate_table.setRowCount(1)
        self.aggregate_table.setMinimumHeight(80)
        self.aggregate_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  # Make completely non-editable
        aggregate_columns = ["Total Time", "Average Time", "Time Limit Usage", "Fail Rate", "Bonus Tasks", "Total Earnings"]
        self.aggregate_table.setColumnCount(len(aggregate_columns))
        self.aggregate_table.setHorizontalHeaderLabels(aggregate_columns)
        self.aggregate_table.setVerticalHeaderLabels(["Aggregate"])
        self.aggregate_table.horizontalHeader().setStretchLastSection(True)
        self.aggregate_table.setObjectName("AnalysisTable") # Set object name
        # Note: Styling handled by main stylesheet
        aggregate_layout.addWidget(self.aggregate_table)
        
        first_row_layout.addWidget(aggregate_group)
        
        # Daily Data Grid
        daily_group = QtWidgets.QGroupBox("Daily Data")
        # Note: Styling handled by main stylesheet
        daily_layout = QtWidgets.QVBoxLayout(daily_group)
        daily_layout.setContentsMargins(8, 8, 8, 8)  # Reduced margins
        
        self.daily_table = QtWidgets.QTableWidget()
        self.daily_table.setMinimumHeight(200)
        self.daily_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  # Make completely non-editable
        daily_columns = ["Date", "Total Time", "Average Time", "Time Limit Usage", "Fail Rate", "Bonus Tasks", "Total Earnings"]
        self.daily_table.setColumnCount(len(daily_columns))
        self.daily_table.setHorizontalHeaderLabels(daily_columns)
        self.daily_table.horizontalHeader().setStretchLastSection(True)
        self.daily_table.setObjectName("AnalysisTable") # Set object name
        # Note: Styling handled by main stylesheet
        daily_layout.addWidget(self.daily_table)
        
        first_row_layout.addWidget(daily_group)
        
        tab_layout.addLayout(first_row_layout)
        
        # Section B: Project-Based Breakdown
        project_group = QtWidgets.QGroupBox("Project-Based Breakdown")
        # Note: Styling handled by main stylesheet
        
        # Create a horizontal layout to hold the two project tables side by side
        project_horizontal_layout = QtWidgets.QHBoxLayout(project_group)
        project_horizontal_layout.setSpacing(10)
        project_horizontal_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left side: Time Range Aggregate Project Data
        project_aggregate_sub_group = QtWidgets.QGroupBox("Time Range Aggregate Project Data")
        project_aggregate_layout = QtWidgets.QVBoxLayout(project_aggregate_sub_group)
        project_aggregate_layout.setContentsMargins(8, 8, 8, 8)
        
        self.project_aggregate_table = QtWidgets.QTableWidget()
        self.project_aggregate_table.setMinimumHeight(150)
        self.project_aggregate_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  # Make completely non-editable
        self.project_aggregate_table.setObjectName("AnalysisTable") # Set object name
        # Note: Styling handled by main stylesheet
        project_aggregate_layout.addWidget(self.project_aggregate_table)
        
        project_horizontal_layout.addWidget(project_aggregate_sub_group)
        
        # Right side: Daily Project Data
        daily_project_sub_group = QtWidgets.QGroupBox("Daily Project Data")
        daily_project_layout = QtWidgets.QVBoxLayout(daily_project_sub_group)
        daily_project_layout.setContentsMargins(8, 8, 8, 8)
        daily_project_layout.setSpacing(8) # Reduced spacing
        
        daily_project_header = QtWidgets.QHBoxLayout()
        daily_project_header.setSpacing(8)  # Reduced spacing
        daily_project_header.setContentsMargins(0, 0, 0, 4) # Reduced margins for inner header
        
        select_day_label = QtWidgets.QLabel("Select Day:")
        select_day_label.setMinimumWidth(70)
        daily_project_header.addWidget(select_day_label)
        
        self.daily_project_combo = QtWidgets.QComboBox()
        self.daily_project_combo.addItem("Select a day...", None)
        self.daily_project_combo.setMinimumWidth(150)
        self.daily_project_combo.currentTextChanged.connect(self.update_daily_project_data)
        daily_project_header.addWidget(self.daily_project_combo)
        daily_project_header.addStretch() # Push combo to left
        
        daily_project_layout.addLayout(daily_project_header)
        
        self.daily_project_table = QtWidgets.QTableWidget()
        self.daily_project_table.setMinimumHeight(150)
        self.daily_project_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)  # Make completely non-editable
        self.daily_project_table.setObjectName("AnalysisTable") # Set object name
        # Note: Styling handled by main stylesheet
        daily_project_layout.addWidget(self.daily_project_table)
        
        project_horizontal_layout.addWidget(daily_project_sub_group)
        
        tab_layout.addWidget(project_group)

    def setup_graphs_tab(self):
        """Setup the Graphs tab with flexible charting system"""
        tab_layout = QtWidgets.QHBoxLayout(self.graphs_tab)  # Changed to horizontal layout
        tab_layout.setSpacing(10)
        tab_layout.setContentsMargins(10, 10, 10, 10)
        
        # Left side: Controls (stacked vertically, compact)
        left_panel = QtWidgets.QWidget()
        left_panel.setMaximumWidth(350)  # Limit width to save space
        left_layout = QtWidgets.QVBoxLayout(left_panel)
        left_layout.setSpacing(8)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # --- 1. Variable Selection Collapsible Pane ---
        variable_layout = QtWidgets.QVBoxLayout() # Create a new layout for the content of this pane
        variable_layout.setContentsMargins(0, 0, 0, 0) # Adjust internal margins for collapsible pane
        variable_layout.setSpacing(8)
        
        # Instructions
        instructions_label = QtWidgets.QLabel("Select exactly 1 X-axis and 1 Y-axis variable:")
        instructions_label.setStyleSheet("QLabel { color: #D6D6D6; font-size: 11px; /* Removed italic */ }")
        instructions_label.setWordWrap(True)
        variable_layout.addWidget(instructions_label)
        
        # X Variable Selection
        x_label = QtWidgets.QLabel("X-axis Variable (Categories/Time):")
        x_label.setStyleSheet("QLabel { /* Removed bold */ color: #D6D6D6; font-size: 12px; }")
        variable_layout.addWidget(x_label)
        
        self.x_variable_combo = QtWidgets.QComboBox()
        self.x_variable_combo.addItem("Select X variable...", None)
        self.x_variable_combo.currentIndexChanged.connect(self.on_x_variable_changed)
        variable_layout.addWidget(self.x_variable_combo)
        
        # Y Variable Selection
        y_label = QtWidgets.QLabel("Y-axis Variable (Quantitative Metrics):")
        y_label.setStyleSheet("QLabel { /* Removed bold */ color: #D6D6D6; font-size: 12px; }")
        variable_layout.addWidget(y_label)
        
        self.y_variable_combo = QtWidgets.QComboBox()
        self.y_variable_combo.addItem("Select Y variable...", None)
        self.y_variable_combo.currentIndexChanged.connect(self.on_y_variable_changed)
        variable_layout.addWidget(self.y_variable_combo)
        
        self.variable_pane = CollapsiblePane("Variable Selection")
        self.variable_pane.setContentLayout(variable_layout)
        # Apply darker background to the header
        self.variable_pane.header_widget.setStyleSheet("""
            QWidget {
                background-color: #222222; /* Much darker background */
                border: 1px solid transparent;
            }
            QWidget:hover {
                background-color: #333333; /* Subtle hover effect */
            }
        """)
        left_layout.addWidget(self.variable_pane)
        
        # --- 2. Chart Configuration Collapsible Pane ---
        chart_config_inner_layout = QtWidgets.QVBoxLayout() # New layout for its content
        chart_config_inner_layout.setContentsMargins(0, 0, 0, 0) # Adjust internal margins
        chart_config_inner_layout.setSpacing(6)
        
        # === BASIC CHART SETTINGS ===
        basic_settings_label = QtWidgets.QLabel("Basic Settings")
        basic_settings_label.setStyleSheet("QLabel { /* Removed bold */ color: #D6D6D6; font-size: 11px; margin-bottom: 4px; }")
        chart_config_inner_layout.addWidget(basic_settings_label)
        
        # Chart Type Selection
        chart_config_inner_layout.addWidget(QtWidgets.QLabel("Chart Type:"))
        self.chart_type_combo = QtWidgets.QComboBox()
        self.chart_type_combo.addItem("Select chart type...", None)
        self.chart_type_combo.currentIndexChanged.connect(self.on_chart_type_changed)
        chart_config_inner_layout.addWidget(self.chart_type_combo)
        
        # Theme Selection
        chart_config_inner_layout.addWidget(QtWidgets.QLabel("Theme:"))
        self.theme_combo = QtWidgets.QComboBox()
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        chart_config_inner_layout.addWidget(self.theme_combo)
        
        # Trend Line Option (for line charts)
        self.trendline_checkbox = QtWidgets.QCheckBox("Show Trend Line")
        self.trendline_checkbox.setVisible(False)  # Initially hidden, shown only for line charts
        self.trendline_checkbox.stateChanged.connect(self.on_trendline_toggled)
        chart_config_inner_layout.addWidget(self.trendline_checkbox)
        
        # Generate Chart Button
        self.generate_chart_btn = QtWidgets.QPushButton("Generate Chart")
        self.generate_chart_btn.setMinimumHeight(30) # Slightly reduced height for better spacing
        self.generate_chart_btn.setStyleSheet("QPushButton { /* Removed bold */ }")
        self.generate_chart_btn.clicked.connect(self.generate_chart)
        chart_config_inner_layout.addWidget(self.generate_chart_btn)
        
        # Create chart export button
        self.export_chart_btn = QtWidgets.QPushButton("Export Chart")
        self.export_chart_btn.setIcon(QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_DialogSaveButton))
        self.export_chart_btn.setMinimumHeight(30)
        self.export_chart_btn.setEnabled(False)  # Disabled until chart is generated
        self.export_chart_btn.clicked.connect(self.open_export_dialog)
        chart_config_inner_layout.addWidget(self.export_chart_btn)
        
        # Chart Compatibility Status
        self.chart_compatibility_label = QtWidgets.QLabel("Select variables and chart type")
        self.chart_compatibility_label.setStyleSheet("QLabel { color: #A0A0A0; font-size: 9px; }")
        self.chart_compatibility_label.setWordWrap(True)
        chart_config_inner_layout.addWidget(self.chart_compatibility_label)
        
        # Separator
        separator1 = QtWidgets.QFrame()
        separator1.setFrameShape(QtWidgets.QFrame.HLine)
        separator1.setStyleSheet("QFrame { color: #3a3b3a; }")
        chart_config_inner_layout.addWidget(separator1)
        
        self.chart_config_pane = CollapsiblePane("Chart Configuration")
        self.chart_config_pane.setContentLayout(chart_config_inner_layout)
        # Apply darker background to the header
        self.chart_config_pane.header_widget.setStyleSheet("""
            QWidget {
                background-color: #222222; /* Much darker background */
                border: 1px solid transparent;
            }
            QWidget:hover {
                background-color: #333333; /* Subtle hover effect */
            }
        """)
        left_layout.addWidget(self.chart_config_pane)
        
        # --- 3. Advanced Analytics Collapsible Pane (Moved to sibling level) ---
        self.analytics_pane = CollapsiblePane("Advanced Analytics")
        # Apply darker background to the header
        self.analytics_pane.header_widget.setStyleSheet("""
            QWidget {
                background-color: #222222; /* Much darker background */
                border: 1px solid transparent;
            }
            QWidget:hover {
                background-color: #333333; /* Subtle hover effect */
            }
        """)
        self.analytics_pane.toggle_button.toggled.connect(self.on_analytics_pane_toggled)

        # Container for analytics controls (existing content remains)
        self.analytics_content_layout = QtWidgets.QVBoxLayout()
        self.analytics_content_layout.setContentsMargins(4, 4, 4, 4)
        self.analytics_content_layout.setSpacing(6)

        # Build analytics controls below and add to layout
        # Moving Average Section
        ma_layout = QtWidgets.QFormLayout()
        ma_layout.setContentsMargins(0, 0, 0, 0)
        ma_layout.setVerticalSpacing(2)

        self.moving_avg_checkbox = QtWidgets.QCheckBox("Moving Average")
        self.moving_avg_checkbox.stateChanged.connect(self.on_moving_average_toggled)
        ma_layout.addRow(self.moving_avg_checkbox)

        # Moving Average Window Size (indented)
        ma_window_label = QtWidgets.QLabel("Window:")
        ma_window_label.setStyleSheet("QLabel { color: #A0A0A0; font-size: 10px; }") # Keep smaller for descriptive label
        
        self.ma_window_spinbox = QtWidgets.QDoubleSpinBox()
        self.ma_window_spinbox.setRange(2, 20)
        self.ma_window_spinbox.setDecimals(0)
        self.ma_window_spinbox.setValue(5)
        self.ma_window_spinbox.setMaximumWidth(70)
        self.ma_window_spinbox.valueChanged.connect(self.on_ma_window_changed)
        ma_layout.addRow(ma_window_label, self.ma_window_spinbox)
        
        self.analytics_content_layout.addLayout(ma_layout)

        # Confidence Intervals Section
        ci_layout = QtWidgets.QFormLayout()
        ci_layout.setContentsMargins(0, 0, 0, 0)
        ci_layout.setVerticalSpacing(2)

        self.confidence_checkbox = QtWidgets.QCheckBox("Confidence Bands")
        self.confidence_checkbox.stateChanged.connect(self.on_confidence_toggled)
        ci_layout.addRow(self.confidence_checkbox)

        # Confidence Level Controls (indented)
        ci_level_label = QtWidgets.QLabel("Level:")
        ci_level_label.setStyleSheet("QLabel { color: #A0A0A0; font-size: 10px; }") # Keep smaller for descriptive label

        self.confidence_combo = QtWidgets.QComboBox()
        self.confidence_combo.addItem("95%", 0.95)
        self.confidence_combo.addItem("99%", 0.99)
        self.confidence_combo.setMaximumWidth(70)
        self.confidence_combo.currentIndexChanged.connect(self.on_confidence_level_changed)
        ci_layout.addRow(ci_level_label, self.confidence_combo)
        
        self.analytics_content_layout.addLayout(ci_layout)

        # Other Analytics Options
        self.stats_annotations_checkbox = QtWidgets.QCheckBox("Show R² & Correlation")
        self.stats_annotations_checkbox.stateChanged.connect(self.on_stats_annotations_toggled)
        self.analytics_content_layout.addWidget(self.stats_annotations_checkbox)
        
        self.outliers_checkbox = QtWidgets.QCheckBox("Highlight Outliers")
        self.outliers_checkbox.stateChanged.connect(self.on_outliers_toggled)
        self.analytics_content_layout.addWidget(self.outliers_checkbox)
        
        # Interactive Features
        self.hover_tooltips_checkbox = QtWidgets.QCheckBox("Hover Tooltips")
        self.hover_tooltips_checkbox.setChecked(True)  # Enabled by default
        self.hover_tooltips_checkbox.stateChanged.connect(self.on_hover_tooltips_toggled)
        self.analytics_content_layout.addWidget(self.hover_tooltips_checkbox)
        
        self.click_drill_checkbox = QtWidgets.QCheckBox("Click-to-Drill-Down")
        self.click_drill_checkbox.setChecked(True)  # Enabled by default
        self.click_drill_checkbox.stateChanged.connect(self.on_click_drill_toggled)
        self.analytics_content_layout.addWidget(self.click_drill_checkbox)
        
        self.data_selection_checkbox = QtWidgets.QCheckBox("Data Point Selection")
        self.data_selection_checkbox.setChecked(True)  # Enabled by default
        self.data_selection_checkbox.stateChanged.connect(self.on_data_selection_toggled)
        self.analytics_content_layout.addWidget(self.data_selection_checkbox)
        
        # Selection controls (indented)
        selection_controls_layout = QtWidgets.QHBoxLayout()
        selection_controls_layout.setContentsMargins(15, 0, 0, 0)  # Indent
        
        self.clear_selection_btn = QtWidgets.QPushButton("Clear Selection")
        self.clear_selection_btn.setMaximumWidth(100)
        self.clear_selection_btn.clicked.connect(self.on_clear_selection)
        selection_controls_layout.addWidget(self.clear_selection_btn)
        
        self.analyze_selection_btn = QtWidgets.QPushButton("Analyze Selected")
        self.analyze_selection_btn.setMaximumWidth(110)
        self.analyze_selection_btn.clicked.connect(self.on_analyze_selection)
        selection_controls_layout.addWidget(self.analyze_selection_btn)
        
        selection_controls_layout.addStretch()
        self.analytics_content_layout.addLayout(selection_controls_layout)
        
        self.brush_selection_checkbox = QtWidgets.QCheckBox("Brush Selection (Shift+Drag)")
        self.brush_selection_checkbox.setChecked(True)  # Enabled by default
        self.brush_selection_checkbox.stateChanged.connect(self.on_brush_selection_toggled)
        self.analytics_content_layout.addWidget(self.brush_selection_checkbox)

        # === STATISTICS SUMMARY (Moved inside Advanced Analytics) ===
        stats_summary_label = QtWidgets.QLabel("Statistics Summary")
        stats_summary_label.setStyleSheet("QLabel { /* Removed bold */ color: #D6D6D6; font-size: 11px; margin-top: 8px; margin-bottom: 4px; }")
        self.analytics_content_layout.addWidget(stats_summary_label)
        
        self.stats_summary_label = QtWidgets.QLabel("Generate a chart to see statistics")
        self.stats_summary_label.setStyleSheet("""
            QLabel { 
                color: #A0A0A0; 
                font-size: 9px; 
                padding: 6px; 
                border: 1px solid #3a3b3a;
            }
        """)
        self.stats_summary_label.setWordWrap(True)
        self.stats_summary_label.setMinimumHeight(50)
        self.analytics_content_layout.addWidget(self.stats_summary_label)

        
        self.analytics_pane.setContentLayout(self.analytics_content_layout)
        left_layout.addWidget(self.analytics_pane) # Add as sibling, not child

        # --- Chart Type Suggestions (Moved inside Chart Configuration) ---
        suggestions_label = QtWidgets.QLabel("Chart Suggestions")
        suggestions_label.setStyleSheet("QLabel { /* Removed bold */ color: #D6D6D6; font-size: 11px; margin-top: 8px; margin-bottom: 4px; }")
        chart_config_inner_layout.addWidget(suggestions_label)
        
        self.chart_suggestions_text = QtWidgets.QLabel("Select variables to see recommendations")
        self.chart_suggestions_text.setStyleSheet("""
            QLabel { 
                color: #A0A0A0; 
                font-size: 9px;
                padding: 6px; 
                border: 1px solid #3a3b3a;
            }
        """)
        self.chart_suggestions_text.setWordWrap(True)
        self.chart_suggestions_text.setMinimumHeight(40)
        chart_config_inner_layout.addWidget(self.chart_suggestions_text)
        
        left_layout.addStretch()  # Push everything to top
        
        tab_layout.addWidget(left_panel)
        
        # Right side: Chart area (takes up remaining space)
        chart_group = QtWidgets.QGroupBox("Chart")
        chart_layout = QtWidgets.QVBoxLayout(chart_group)
        chart_layout.setContentsMargins(6, 6, 6, 6)  # Smaller margins
        
        # Create chart view
        self.chart = QChart()
        self.chart.setBackgroundBrush(QtGui.QBrush(QtGui.QColor("#2a2b2a")))  # Set chart background to match theme
        self.chart.setPlotAreaBackgroundBrush(QtGui.QBrush(QtGui.QColor("#2a2b2a")))  # Set plot area background
        self.chart.setTitleBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set title color
        self.chart.setTitle("Select variables and click 'Generate Chart'")  # Initial message
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QtGui.QPainter.Antialiasing)
        self.chart_view.setMinimumHeight(300)  # Smaller minimum height
        self.chart_view.setBackgroundBrush(QtGui.QBrush(QtGui.QColor("#2a2b2a")))  # Set chart view background
        chart_layout.addWidget(self.chart_view)
        
        tab_layout.addWidget(chart_group)  # Chart takes remaining horizontal space
        
        # Initialize dropdown variables
        self.populate_variable_dropdowns()
    
    def populate_theme_combo(self):
        """Populate the theme combo with available chart themes"""
        if not CHARTS_AVAILABLE:
            return
            
        if hasattr(self, 'chart_manager') and self.chart_manager:
            themes = self.chart_manager.get_available_themes()
            self.theme_combo.clear()
            
            # Add theme names with nice display names
            theme_display_names = {
                "professional": "Professional (Default)",
                "dark": "Dark Mode", 
                "minimal": "Minimal Clean",
                "accessible": "High Contrast"
            }
            
            for theme in themes:
                display_name = theme_display_names.get(theme, theme.title())
                self.theme_combo.addItem(display_name, theme)  # Store actual theme name in data
            
            # Set default to professional
            for i in range(self.theme_combo.count()):
                if self.theme_combo.itemData(i) == "professional":
                    self.theme_combo.setCurrentIndex(i)
                    break
    
    def on_theme_changed(self):
        """Handle theme selection change"""
        if not CHARTS_AVAILABLE:
            return
            
        if hasattr(self, 'chart_manager') and self.chart_manager:
            current_index = self.theme_combo.currentIndex()
            if current_index >= 0:
                theme_name = self.theme_combo.itemData(current_index)
                if theme_name:
                    self.chart_manager.set_chart_theme(theme_name)
                    
                    # Regenerate chart if there's a current chart
                    if (hasattr(self, 'chart') and 
                        self.chart.series() and 
                        len(self.chart.series()) > 0):
                        # Get current selections and regenerate
                        self.generate_chart()

    def populate_variable_dropdowns(self):
        """Populate the X and Y variable dropdown menus with constrained options"""
        if not CHARTS_AVAILABLE:
            return
            
        # Clear existing items (keep default "Select..." items)
        self.x_variable_combo.clear()
        self.y_variable_combo.clear()
        
        # Add default selection items
        self.x_variable_combo.addItem("Select X variable...", None)
        self.y_variable_combo.addItem("Select Y variable...", None)
        
        # Get allowed variables from constraints
        allowed_x = get_allowed_x_variables()
        allowed_y = get_allowed_y_variables()
        
        # Populate X variables (categorical/temporal)
        for var_key, var_config in allowed_x.items():
            display_name = var_config['display_name']
            description = var_config['description']
            tooltip_text = f"{display_name}: {description}"
            
            # Add icon based on data type
            if var_config['data_type'] == 'categorical':
                icon = "📊"
            else:  # date/time
                icon = "📅"
            
            display_text = f"{icon} {display_name}"
            self.x_variable_combo.addItem(display_text, var_key)
            # Set tooltip for better UX
            self.x_variable_combo.setItemData(self.x_variable_combo.count() - 1, tooltip_text, QtCore.Qt.ToolTipRole)
        
        # Populate Y variables (quantitative metrics)
        for var_key, var_config in allowed_y.items():
            display_name = var_config['display_name']
            description = var_config['description']
            unit = var_config['unit']
            tooltip_text = f"{display_name}: {description} (Unit: {unit})"
            
            # Add icon based on unit type
            if unit == 'currency':
                icon = "💰"
            elif unit == 'percent':
                icon = "📊"
            elif unit == 'hours':
                icon = "⏱️"
            elif unit == 'time':
                icon = "🕐"
            else:
                icon = "📈"
            
            display_text = f"{icon} {display_name}"
            self.y_variable_combo.addItem(display_text, var_key)
            # Set tooltip for better UX
            self.y_variable_combo.setItemData(self.y_variable_combo.count() - 1, tooltip_text, QtCore.Qt.ToolTipRole)
        

    
    def _get_current_selection_context(self) -> Dict[str, Any]:
        """Get the current variable selection context"""
        context = {
            "x_variable": None,
            "y_variable": None,
            "chart_type": None
        }
        
        # Get X variable from dropdown
        x_index = self.x_variable_combo.currentIndex()
        if x_index > 0:
            context["x_variable"] = self.x_variable_combo.itemData(x_index)
        
        # Get Y variable from dropdown  
        y_index = self.y_variable_combo.currentIndex()
        if y_index > 0:
            context["y_variable"] = self.y_variable_combo.itemData(y_index)
        
        # Get chart type
        chart_index = self.chart_type_combo.currentIndex()
        if chart_index > 0:
            context["chart_type"] = self.chart_type_combo.itemData(chart_index)
        
        return context
    
    def update_variable_suggestions(self):
        """Update variable suggestions based on current selection"""
        if not CHARTS_AVAILABLE or not hasattr(self, 'suggestion_engine'):
            return
        
        # Get current context
        current_selection = self._get_current_selection_context()
        
        # Get available variables (those not currently selected)
        available_vars = []
        for i in range(self.available_variables_list.count()):
            item = self.available_variables_list.item(i)
            var_name, var_type = item.data(QtCore.Qt.UserRole)
            available_vars.append((var_name, var_type))
        
        # Get new suggestions
        suggestions = self.suggestion_engine.get_variable_suggestions(
            current_selection, available_vars
        )
        
        # Update suggestion indicators
        suggestion_map = {}
        for suggestion in suggestions:
            if suggestion.variable_name not in suggestion_map:
                suggestion_map[suggestion.variable_name] = []
            suggestion_map[suggestion.variable_name].append(suggestion)
        
        # Update each item in available variables list
        for i in range(self.available_variables_list.count()):
            item = self.available_variables_list.item(i)
            var_name, _ = item.data(QtCore.Qt.UserRole)
            
            var_suggestions = suggestion_map.get(var_name, [])
            if var_suggestions:
                best_suggestion = max(var_suggestions, key=lambda s: s.confidence)
                suggestion_info = {
                    "type": best_suggestion.suggestion_type.value,
                    "reason": best_suggestion.reason,
                    "confidence": best_suggestion.confidence
                }
                if hasattr(item, 'suggestion_info'):
                    item.suggestion_info = suggestion_info
                    item._update_appearance()
        
        # Update chart type suggestions
        self._update_chart_type_suggestions()
    
    def _update_chart_type_suggestions(self):
        """Update the chart type suggestions panel"""
        if not hasattr(self, 'suggestion_engine') or not hasattr(self, 'chart_suggestions_text'):
            return
        
        current_selection = self._get_current_selection_context()
        x_variable = current_selection.get("x_variable")
        y_variables = current_selection.get("y_variables", [])
        
        if not x_variable or not y_variables:
            self.chart_suggestions_text.setText("Select X and Y variables to see chart type recommendations")
            return
        
        # Get chart type suggestions
        chart_suggestions = self.suggestion_engine.get_chart_type_suggestions(
            x_variable, y_variables
        )
        
        if not chart_suggestions:
            self.chart_suggestions_text.setText("No specific chart type recommendations for this selection")
            return
        
        # Format suggestions
        suggestion_text = []
        for suggestion in chart_suggestions[:3]:  # Show top 3 suggestions
            score_text = f"{suggestion.suitability_score:.0%}"
            chart_text = f"📊 {suggestion.chart_type} ({score_text})"
            if suggestion.reasons:
                chart_text += f": {suggestion.reasons[0]}"  # Show first reason
            suggestion_text.append(chart_text)
        
        self.chart_suggestions_text.setText("\n".join(suggestion_text))
    
    def return_variable_to_available(self, display_name, variable_data):
        """Return a variable to the available list"""
        variable_name, variable_type = variable_data
        
        # Check if it's already in available list
        for i in range(self.available_variables_list.count()):
            existing_item = self.available_variables_list.item(i)
            existing_var_name, _ = existing_item.data(QtCore.Qt.UserRole)
            if existing_var_name == variable_name:
                return  # Already exists
        
        # Add back to available
        item = QtWidgets.QListWidgetItem(display_name)
        item.setData(QtCore.Qt.UserRole, (variable_name, variable_type))
        self.available_variables_list.addItem(item)
    
    def generate_chart(self):
        """Generate chart based on selected variables and chart type with constrained flexibility"""
        if not CHARTS_AVAILABLE:
            return
            
        try:
            print("🔍 DEBUG: Starting chart generation...")
            
            # Get selected variables from dropdowns
            x_variable = None
            y_variable = None
            
            # Get X variable
            x_index = self.x_variable_combo.currentIndex()
            if x_index > 0:  # Not the default item
                x_variable = self.x_variable_combo.itemData(x_index)
            
            # Get Y variable (only one allowed)
            y_index = self.y_variable_combo.currentIndex()
            if y_index > 0:  # Not the default item
                y_variable = self.y_variable_combo.itemData(y_index)
            
            print(f"🔍 DEBUG: Selected variables - X: {x_variable}, Y: {y_variable}")
            
            # Validation
            if not x_variable:
                print("🔍 DEBUG: No X variable selected")
                self._show_selection_guidance("No X-axis Variable Selected", 
                    "Please select an X-axis variable to create a chart.",
                    ["Choose from categorical variables (Projects, Time ranges)",
                     "Or select time-based variables (Day, Week, Month) for trends"])
                return
            
            if not y_variable:
                print("🔍 DEBUG: No Y variable selected")
                self._show_selection_guidance("No Y-axis Variable Selected",
                    "Please select a Y-axis variable to create a chart.",
                    ["Choose from quantitative metrics (Duration, Money, Ratings)",
                     "Each metric provides different insights into your task performance"])
                return
            
            # Check for data selection
            if not self._has_valid_data_selection():
                print("🔍 DEBUG: No valid data selection")
                self._show_data_selection_guidance()
                return
            
            print(f"🔍 DEBUG: Data selection - Week: {self.current_week_id}, Dates: {self.current_start_date} to {self.current_end_date}")
            
            # Get chart type
            chart_type_index = self.chart_type_combo.currentIndex()
            if chart_type_index <= 0:
                print("🔍 DEBUG: No chart type selected")
                self._show_selection_guidance("No Chart Type Selected",
                    "Please select a chart type to create the visualization.",
                    ["Chart types are filtered based on your X variable selection",
                     "Line charts work best for time-series data",
                     "Bar charts work well for categorical comparisons"])
                return
            
            chart_type = self.chart_type_combo.itemData(chart_type_index)
            print(f"🔍 DEBUG: Selected chart type: {chart_type}")
            
            # Final validation using constraints
            is_valid, message = validate_variable_combination(x_variable, y_variable, chart_type)
            if not is_valid:
                self._show_selection_guidance("Invalid Variable Combination",
                    f"The selected combination is not allowed: {message}",
                    ["Try selecting a different chart type",
                     "Or choose different variables that are compatible"])
                return
            
            # Show loading state
            self._show_loading_state(True)
            
            # Get chart data using the new constrained system
            chart_data = self.data_manager.get_constrained_chart_data(
                x_variable, y_variable, chart_type,
                self.current_week_id, self.current_start_date, self.current_end_date
            )
            
            if not chart_data:
                self._show_data_guidance("No Data Available",
                    "No data was found for the selected variables and time period.",
                    ["Try selecting a different time period",
                     "Check if tasks exist for the chosen variables",
                     "Verify your data selection criteria"])
                return
            
            # Create chart data in format expected by ChartManager
            formatted_data = []
            for x_val, y_val in chart_data:
                formatted_data.append((x_val, y_val))
            
            # Map chart type to format expected by ChartManager
            chart_type_mapping = {
                'line': 'Line Chart',
                'bar': 'Bar Chart',
                'scatter': 'Scatter Plot',
                'pie': 'Pie Chart',
                'box_plot': 'Box Plot'
            }
            chart_type_display = chart_type_mapping.get(chart_type, chart_type)
            
            # Generate the chart
            self.chart_manager.create_chart(
                data=formatted_data,
                x_variable=(x_variable, "categorical"),  # Simplified type handling
                y_variables=[(y_variable, "quantitative")],  # Single Y variable in list
                chart_type=chart_type_display
            )
            
            # Store chart data for statistical overlays
            self.store_current_chart_data(formatted_data)
            
            # Enable trend line option for line charts
            self.trendline_checkbox.setVisible(chart_type == 'line')
            if chart_type == 'line' and self.trendline_checkbox.isChecked():
                self.chart_manager.enable_trend_line(True)
            
            # Apply any selected statistical overlays
            self.apply_statistical_overlays()
            
            # Enable export button after successful chart generation
            self.export_chart_btn.setEnabled(True)
                
        except Exception as e:
            # Handle unexpected errors gracefully
            self._show_unexpected_error(e)
        finally:
            # Always hide loading state
            self._show_loading_state(False)
    
    def _has_valid_data_selection(self):
        """Check if user has made a valid data selection (time range or week)"""
        return (self.current_week_id is not None or 
                (self.current_start_date is not None and self.current_end_date is not None))
    
    def _should_show_pre_generation_guidance(self, x_variable, y_variables, chart_type):
        """Determine if pre-generation guidance should be shown"""
        # Show guidance for potentially problematic combinations
        return (len(y_variables) > 5 or  # Many Y variables
                chart_type == "Pie Chart" or  # Pie charts have specific requirements
                x_variable[1] == "categorical" and chart_type == "Scatter Plot")  # Categorical X with scatter
    
    def _show_pre_generation_guidance(self, x_variable, y_variables, chart_type):
        """Show pre-generation guidance and return whether to continue"""
        guidance_messages = []
        
        if len(y_variables) > 5:
            guidance_messages.append(f"You've selected {len(y_variables)} Y variables. This may result in a cluttered chart.")
        
        if chart_type == "Pie Chart":
            if len(y_variables) > 1:
                guidance_messages.append("Pie charts work best with exactly one Y variable. Only the first will be used.")
            if x_variable[1] != "categorical":
                guidance_messages.append("Pie charts require categorical X variables (like Project Name, Locale).")
        
        if x_variable[1] == "categorical" and chart_type == "Scatter Plot":
            guidance_messages.append("Scatter plots work better with quantitative X variables. Consider using a Bar Chart instead.")
        
        if guidance_messages:
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Question)
            msg_box.setWindowTitle("Chart Generation Guidance")
            msg_box.setText("Before generating your chart:\n\n" + "\n".join(f"• {msg}" for msg in guidance_messages))
            msg_box.setInformativeText("Would you like to continue anyway?")
            msg_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msg_box.setDefaultButton(QtWidgets.QMessageBox.Yes)
            
            return msg_box.exec() == QtWidgets.QMessageBox.Yes
        
        return True
    
    def _show_selection_guidance(self, title, message, suggestions):
        """Show helpful guidance for variable selection issues"""
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if suggestions:
            suggestion_text = "How to fix this:\n" + "\n".join(f"• {suggestion}" for suggestion in suggestions)
            msg_box.setInformativeText(suggestion_text)
        
        msg_box.exec()
    
    def _show_data_selection_guidance(self):
        """Show guidance for data selection issues"""
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Information)
        msg_box.setWindowTitle("No Data Period Selected")
        msg_box.setText("Please select a time period to analyze before generating charts.")
        msg_box.setInformativeText(
            "You can either:\n"
            "• Select a specific week from the dropdown, OR\n"
            "• Choose a custom date range using the calendar controls\n\n"
            "This determines which data will be included in your chart."
        )
        msg_box.exec()
    
    def _show_data_guidance(self, title, message, suggestions):
        """Show helpful guidance for data availability issues"""
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Warning)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        
        if suggestions:
            suggestion_text = "Possible solutions:\n" + "\n".join(f"• {suggestion}" for suggestion in suggestions)
            msg_box.setInformativeText(suggestion_text)
        
        msg_box.exec()
    
    def _show_unexpected_error(self, error):
        """Show user-friendly error message for unexpected errors"""
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Critical)
        msg_box.setWindowTitle("Unexpected Error")
        msg_box.setText("An unexpected error occurred while generating the chart.")
        msg_box.setInformativeText(
            f"Error details: {str(error)}\n\n"
            "What you can try:\n"
            "• Try generating the chart again\n"
            "• Select different variables or chart type\n"
            "• Choose a different time range\n"
            "• Contact support if the problem persists"
        )
        msg_box.exec()
        
        # Also log the error for debugging
        print(f"Unexpected error in generate_chart: {error}")
    
    def _show_loading_state(self, show_loading):
        """Show/hide loading state for chart generation"""
        if show_loading:
            self.generate_chart_btn.setText("Generating Chart...")
            self.generate_chart_btn.setEnabled(False)
            self.chart.setTitle("Generating chart, please wait...")
        else:
            self.generate_chart_btn.setText("Generate Chart")
            self.generate_chart_btn.setEnabled(True)
    
    def get_chart_data(self, x_variable, y_variables):
        """Get data for charting based on selected variables"""
        return self.data_manager.get_chart_data(x_variable, y_variables, self.current_week_id, self.current_start_date, self.current_end_date)
    
    def populate_week_combo(self):
        """Populate the week selection combo with available weeks from the weeks table"""
        weeks = self.data_manager.populate_week_combo_data()
        
        for week_id, week_label in weeks:
            if week_id and week_label:
                self.week_combo.addItem(week_label, week_id)

    def apply_time_range_selection(self):
        """Apply time range selection and clear week selection"""
        self.current_start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        self.current_end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        self.current_week_id = None
        
        # Clear week combo selection visually
        self.week_combo.setCurrentIndex(0)
        
        self.refresh_analysis()

    def apply_week_selection(self):
        """Apply week selection and clear time range"""
        current_week_data = self.week_combo.currentData()
        if current_week_data is not None:
            self.current_week_id = current_week_data
            self.current_start_date = None
            self.current_end_date = None
            
            # Clear date range selection visually by setting to default values
            # Setting to min/max date or some other neutral value if applicable
            self.start_date_edit.setDate(QtCore.QDate.currentDate().addDays(-30)) # Example default
            self.end_date_edit.setDate(QtCore.QDate.currentDate()) # Example default
            
            self.refresh_analysis()

    def refresh_analysis(self, week_id=None):
        """Refresh all analysis data based on current selection or provided week_id for compatibility"""
        if week_id is not None:
            # Compatibility with old interface - set the week and clear time range
            self.current_week_id = week_id
            self.current_start_date = None
            self.current_end_date = None
            
            # Find the week in the combo and select it
            for i in range(self.week_combo.count()):
                if self.week_combo.itemData(i) == week_id:
                    self.week_combo.setCurrentIndex(i)
                    break
            
            self.refresh_analysis_by_week(week_id)
        elif self.current_week_id is not None:
            self.refresh_analysis_by_week(self.current_week_id)
        elif self.current_start_date and self.current_end_date:
            self.refresh_analysis_by_time_range(self.current_start_date, self.current_end_date)
        else:
            self.clear_all_data()

    def refresh_week_combo(self):
        """Refresh the week combo when weeks are added/deleted in week widget"""
        current_selection = self.week_combo.currentData()
        self.week_combo.clear()
        self.week_combo.addItem("Select a week...", None)
        self.populate_week_combo()
        
        # Restore selection if it still exists
        if current_selection is not None:
            for i in range(self.week_combo.count()):
                if self.week_combo.itemData(i) == current_selection:
                    self.week_combo.setCurrentIndex(i)
                    break

    def refresh_analysis_by_week(self, week_id):
        """Refresh analysis for a specific week"""
        tasks_data = self.data_manager.get_tasks_data_by_week(week_id)
        
        # Update status display
        self.update_current_status_display(week_id)

        if tasks_data:
            self.populate_numerical_statistics(tasks_data, week_id)

    def refresh_analysis_by_time_range(self, start_date, end_date):
        """Refresh analysis for a specific time range"""
        tasks_data = self.data_manager.get_tasks_data_by_time_range(start_date, end_date)
        
        # Update status display (no specific week_id for time ranges)
        self.update_current_status_display(None)
        
        if tasks_data:
            self.populate_numerical_statistics(tasks_data)

    def populate_numerical_statistics(self, tasks_data, week_id=None):
        """Populate the numerical statistics tables with calculated data"""
        if not tasks_data:
            self.clear_all_data()
            return

        # Calculate aggregate statistics (pass week_id for bonus calculations)
        aggregate_stats = self.data_manager.calculate_aggregate_statistics(tasks_data, week_id)
        
        # Populate aggregate table
        self.populate_aggregate_table(aggregate_stats)
        
        # Calculate daily statistics (pass week_id for bonus calculations)
        daily_stats = self.data_manager.calculate_daily_statistics(tasks_data, week_id)
        
        # Populate daily table
        self.populate_daily_table(daily_stats)
        
        # Update daily project dropdown
        self.update_daily_project_dropdown(daily_stats.keys())
        
        # Calculate and populate project breakdown (pass week_id for bonus calculations)
        project_stats = self.data_manager.calculate_project_statistics(tasks_data, week_id)
        self.populate_project_aggregate_table(project_stats)

    def populate_aggregate_table(self, stats):
        """Populate the aggregate statistics table"""
        columns = ["Total Time", "Average Time", "Time Limit Usage", "Fail Rate", "Bonus Tasks", "Total Earnings"]
        values = [stats['total_time'], stats['average_time'], stats['time_limit_usage'], 
                 stats['fail_rate'], stats['bonus_tasks'], stats['total_earnings']]
        
        for col, value in enumerate(values):
            item = QtWidgets.QTableWidgetItem(value)
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.aggregate_table.setItem(0, col, item)

    def populate_daily_table(self, daily_stats):
        """Populate the daily statistics table"""
        self.daily_table.setRowCount(len(daily_stats))
        
        sorted_days = sorted(daily_stats.keys())
        for row, day in enumerate(sorted_days):
            stats = daily_stats[day]
            values = [stats['date'], stats['total_time'], stats['average_time'], 
                     stats['time_limit_usage'], stats['fail_rate'], stats['bonus_tasks'], stats['total_earnings']]
            
            for col, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.daily_table.setItem(row, col, item)

    def populate_project_aggregate_table(self, project_data):
        """Populate the project aggregate statistics table"""
        # Flatten project data for display
        rows = []
        for project_name, locales in project_data.items():
            for locale, data in locales.items():
                rows.append({
                    'project': project_name,
                    'locale': locale,
                    'total_time': self.data_manager._format_time(data['total_seconds']),
                    'task_count': data['task_count'],
                    'bonus_count': data['bonus_count']
                })
        
        self.project_aggregate_table.setRowCount(len(rows))
        self.project_aggregate_table.setColumnCount(5)
        self.project_aggregate_table.setHorizontalHeaderLabels(
            ["Project", "Locale", "Total Time", "Task Count", "Bonus Count"])
        
        for row, data in enumerate(rows):
            values = [data['project'], data['locale'], data['total_time'], 
                     str(data['task_count']), str(data['bonus_count'])]
            
            for col, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.project_aggregate_table.setItem(row, col, item)

    def update_daily_project_dropdown(self, available_days):
        """Update the daily project dropdown with available days"""
        self.daily_project_combo.clear()
        self.daily_project_combo.addItem("Select a day...", None)
        
        for day in sorted(available_days):
            self.daily_project_combo.addItem(day, day)

    def update_daily_project_data(self):
        """Update daily project data based on selected day"""
        selected_day = self.daily_project_combo.currentData()
        if selected_day is None:
            self.daily_project_table.setRowCount(0)
            return
        
        # Get tasks for the selected day
        if self.current_week_id is not None:
            tasks_data = self.data_manager.get_tasks_data_for_daily_project(
                "week", self.current_week_id, selected_day, None, None
            )
        elif self.current_start_date and self.current_end_date:
            tasks_data = self.data_manager.get_tasks_data_for_daily_project(
                "time_range", None, selected_day, self.current_start_date, self.current_end_date
            )
        else:
            tasks_data = []
        
        # Calculate daily project breakdown (pass week_id for bonus calculations)
        project_data = self.data_manager.calculate_project_statistics(tasks_data, self.current_week_id)

        # Populate daily project table
        rows = []
        for project_name, locales in project_data.items():
            for locale, data in locales.items():
                rows.append({
                    'project': project_name,
                    'locale': locale,
                    'total_time': self.data_manager._format_time(data['total_seconds']),
                    'task_count': data['task_count'],
                    'bonus_count': data['bonus_count']
                })
        
        self.daily_project_table.setRowCount(len(rows))
        self.daily_project_table.setColumnCount(5)
        self.daily_project_table.setHorizontalHeaderLabels(
            ["Project", "Locale", "Total Time", "Task Count", "Bonus Count"])
        
        for row, data in enumerate(rows):
            values = [data['project'], data['locale'], data['total_time'], 
                     str(data['task_count']), str(data['bonus_count'])]
            
            for col, value in enumerate(values):
                item = QtWidgets.QTableWidgetItem(value)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
                self.daily_project_table.setItem(row, col, item)

    
    def clear_all_data(self):
        """Clear all data and charts"""
        # Clear chart view
        if hasattr(self, 'chart_manager'):
            self.chart_manager.clear_chart()
        
        # Disable export button when clearing
        if hasattr(self, 'export_chart_btn'):
            self.export_chart_btn.setEnabled(False)
        
        # Clear tables
        self.aggregate_table.setRowCount(0)
        self.daily_table.setRowCount(0)
        self.project_aggregate_table.setRowCount(0)
        
        # Clear dropdowns
        self.daily_project_combo.clear()
        self.daily_project_combo.addItem("Select a day to see project data...")
        
        # Clear status
        self.current_week_id = None
        self.current_start_date = None
        self.current_end_date = None
        
        # Update status
        self.update_current_status_display()

    def on_chart_type_changed(self):
        """Handle chart type change"""
        # Check if we can enable chart generation with the new selection
        self.check_chart_generation_readiness()

    def on_trendline_toggled(self):
        """Handle trend line toggle"""
        if hasattr(self, 'chart_manager'):
            enabled = self.trendline_checkbox.isChecked()
            self.chart_manager.enable_trend_line(enabled)
            # If chart already drawn, update
            if self.chart.series() and len(self.chart.series()) > 0:
                self.generate_chart()

    def on_x_variable_changed(self):
        """Handle X variable selection change"""
        current_index = self.x_variable_combo.currentIndex()
        if current_index > 0:  # Not the default "Select..." item
            x_variable = self.x_variable_combo.itemData(current_index)
            if x_variable:
                # Update compatible chart types
                self.update_compatible_chart_types(x_variable)
                # Check if we can enable chart generation
                self.check_chart_generation_readiness()
        else:
            # Clear chart type options if no X variable selected
            self.chart_type_combo.clear()
            self.chart_type_combo.addItem("Select chart type...", None)
            self.chart_compatibility_label.setText("Select X variable to see compatible chart types")
    
    def on_y_variable_changed(self):
        """Handle Y variable selection change"""
        # Check if we can enable chart generation
        self.check_chart_generation_readiness()
    
    def update_compatible_chart_types(self, x_variable):
        """Update chart type dropdown based on selected X variable"""
        self.chart_type_combo.clear()
        self.chart_type_combo.addItem("Select chart type...", None)
        
        # Get compatible chart types
        compatible_types = get_compatible_chart_types(x_variable)
        chart_types = get_allowed_chart_types()
        
        for chart_type in compatible_types:
            if chart_type in chart_types:
                config = chart_types[chart_type]
                display_name = config['display_name']
                self.chart_type_combo.addItem(display_name, chart_type)
        
        # Update compatibility info
        type_names = [chart_types[ct]['display_name'] for ct in compatible_types if ct in chart_types]
        if type_names:
            self.chart_compatibility_label.setText(f"Compatible: {', '.join(type_names)}")
        else:
            self.chart_compatibility_label.setText("No compatible chart types")
    
    def check_chart_generation_readiness(self):
        """Enable/disable chart generation based on current selections"""
        x_selected = self.x_variable_combo.currentIndex() > 0
        y_selected = self.y_variable_combo.currentIndex() > 0 
        chart_selected = self.chart_type_combo.currentIndex() > 0
        
        ready = x_selected and y_selected and chart_selected
        self.generate_chart_btn.setEnabled(ready)
        
        if ready:
            # Validate the combination
            x_var = self.x_variable_combo.itemData(self.x_variable_combo.currentIndex())
            y_var = self.y_variable_combo.itemData(self.y_variable_combo.currentIndex())
            chart_type = self.chart_type_combo.itemData(self.chart_type_combo.currentIndex())
            
            is_valid, message = validate_variable_combination(x_var, y_var, chart_type)
            if not is_valid:
                self.generate_chart_btn.setEnabled(False)
                self.chart_compatibility_label.setText(f"⚠️ {message}")
            else:
                self.chart_compatibility_label.setText("✅ Valid combination - ready to generate chart")

    # Advanced Statistical Feature Event Handlers (Phase 4)
    
    def on_moving_average_toggled(self):
        """Handle moving average checkbox toggle"""
        if hasattr(self, 'chart_manager') and hasattr(self, 'current_chart_data'):
            if self.moving_avg_checkbox.isChecked():
                self.apply_statistical_overlays()
            else:
                self.regenerate_chart_without_overlays()
    
    def on_ma_window_changed(self):
        """Handle moving average window size change"""
        if hasattr(self, 'chart_manager') and hasattr(self, 'current_chart_data'):
            if self.moving_avg_checkbox.isChecked():
                self.apply_statistical_overlays()
    
    def on_confidence_toggled(self):
        """Handle confidence bands checkbox toggle"""
        if hasattr(self, 'chart_manager') and hasattr(self, 'current_chart_data'):
            if self.confidence_checkbox.isChecked():
                self.apply_statistical_overlays()
            else:
                self.regenerate_chart_without_overlays()
    
    def on_confidence_level_changed(self):
        """Handle confidence level change"""
        if hasattr(self, 'chart_manager') and hasattr(self, 'current_chart_data'):
            if self.confidence_checkbox.isChecked():
                self.apply_statistical_overlays()
    
    def on_stats_annotations_toggled(self):
        """Handle statistical annotations checkbox toggle"""
        if hasattr(self, 'chart_manager') and hasattr(self, 'current_chart_data'):
            self.apply_statistical_overlays()
    
    def on_outliers_toggled(self):
        """Handle outliers checkbox toggle"""
        if hasattr(self, 'chart_manager') and hasattr(self, 'current_chart_data'):
            if self.outliers_checkbox.isChecked():
                self.apply_statistical_overlays()
            else:
                self.regenerate_chart_without_overlays()
    
    def on_hover_tooltips_toggled(self):
        """Handle hover tooltips checkbox toggle"""
        if hasattr(self, 'chart_manager'):
            enabled = self.hover_tooltips_checkbox.isChecked()
            self.chart_manager.interaction_manager.enable_hover_tooltips(enabled)
    
    def on_click_drill_toggled(self):
        """Handle click-to-drill-down checkbox toggle"""
        if hasattr(self, 'chart_manager'):
            enabled = self.click_drill_checkbox.isChecked()
            self.chart_manager.interaction_manager.enable_click_drill_down(enabled)
    
    def on_data_selection_toggled(self):
        """Handle data point selection checkbox toggle"""
        if hasattr(self, 'chart_manager'):
            enabled = self.data_selection_checkbox.isChecked()
            self.chart_manager.interaction_manager.enable_data_point_selection(enabled)
    
    def on_clear_selection(self):
        """Handle clear selection button click"""
        if hasattr(self, 'chart_manager'):
            self.chart_manager.interaction_manager.clear_selection()
    
    def on_analyze_selection(self):
        """Handle analyze selection button click"""
        if hasattr(self, 'chart_manager'):
            self.chart_manager.interaction_manager.show_selection_analysis()
    
    def on_brush_selection_toggled(self):
        """Handle brush selection checkbox toggle"""
        if hasattr(self, 'chart_manager'):
            enabled = self.brush_selection_checkbox.isChecked()
            self.chart_manager.interaction_manager.enable_brush_selection(enabled)
    
    def apply_statistical_overlays(self):
        """Apply all selected statistical overlays to the current chart"""
        if not hasattr(self, 'current_chart_data') or not self.current_chart_data:
            return
        
        try:
            # Get current chart type to determine applicable overlays
            chart_type_index = self.chart_type_combo.currentIndex()
            if chart_type_index <= 0:
                return
            
            chart_type = self.chart_type_combo.itemData(chart_type_index)
            
            # Only apply certain overlays to line charts
            if chart_type == 'line':
                # Moving Average
                if self.moving_avg_checkbox.isChecked():
                    window_size = int(self.ma_window_spinbox.value())  # Convert to int
                    self.chart_manager.add_moving_average_overlay(self.current_chart_data, window_size)
                
                # Confidence Bands
                if self.confidence_checkbox.isChecked():
                    confidence_level = self.confidence_combo.currentData()
                    self.chart_manager.add_confidence_bands(self.current_chart_data, confidence_level)
            
            # Statistical Annotations (applicable to all chart types)
            if self.stats_annotations_checkbox.isChecked():
                # Convert to numeric data for statistical calculations
                numeric_data = []
                for i, (x_val, y_val) in enumerate(self.current_chart_data):
                    try:
                        # For time-based X variables, use index as numeric X value
                        if isinstance(x_val, str):
                            numeric_x = float(i)
                        else:
                            numeric_x = float(x_val)
                        
                        numeric_y = float(y_val)
                        numeric_data.append((numeric_x, numeric_y))
                    except (ValueError, TypeError):
                        continue
                
                if numeric_data:
                    stats = self.chart_manager.add_statistical_annotations(numeric_data)
                    self.update_statistics_display(stats)
            
            # Outlier Highlighting
            if self.outliers_checkbox.isChecked():
                self.chart_manager.add_outlier_highlighting(self.current_chart_data)
            
            # Update comprehensive statistics display
            # Convert to numeric data for comprehensive statistics
            numeric_data = []
            for i, (x_val, y_val) in enumerate(self.current_chart_data):
                try:
                    if isinstance(x_val, str):
                        numeric_x = float(i)
                    else:
                        numeric_x = float(x_val)
                    
                    numeric_y = float(y_val)
                    numeric_data.append((numeric_x, numeric_y))
                except (ValueError, TypeError):
                    continue
            
            if numeric_data:
                comprehensive_stats = self.chart_manager.get_chart_statistics(numeric_data)
                self.update_statistics_display(comprehensive_stats)
            
        except Exception as e:
            print(f"Warning: Error applying statistical overlays: {e}")
    
    def regenerate_chart_without_overlays(self):
        """Regenerate the base chart without statistical overlays"""
        # Clear the chart and regenerate the base chart
        self.chart_manager.clear_chart()
        self.generate_chart()
    
    def update_statistics_display(self, stats: Dict[str, any]):
        """Update the statistics summary display with calculated statistics"""
        if not stats:
            self.stats_summary_label.setText("No statistics available")
            return
        
        try:
            # Format statistics for display
            display_lines = []
            
            if 'data_points' in stats:
                display_lines.append(f"Data Points: {stats['data_points']}")
            
            if 'r_squared' in stats:
                display_lines.append(f"R²: {stats['r_squared']:.3f}")
            
            if 'correlation' in stats:
                display_lines.append(f"Correlation: {stats['correlation']:.3f}")
            
            if 'y_stats' in stats and stats['y_stats']:
                y_stats = stats['y_stats']
                if 'mean' in y_stats:
                    display_lines.append(f"Mean: {y_stats['mean']:.2f}")
                if 'std_dev' in y_stats:
                    display_lines.append(f"Std Dev: {y_stats['std_dev']:.2f}")
            
            if 'outliers_iqr' in stats:
                display_lines.append(f"Outliers (IQR): {stats['outliers_iqr']}")
            
            # Join lines and update display
            display_text = " | ".join(display_lines) if display_lines else "Statistics calculated"
            self.stats_summary_label.setText(display_text)
            
        except Exception as e:
            self.stats_summary_label.setText(f"Error displaying statistics: {str(e)}")
    
    def store_current_chart_data(self, data):
        """Store the current chart data for statistical overlay operations"""
        self.current_chart_data = data

    def on_analytics_pane_toggled(self, expanded: bool):
        """Handle analytics pane expand/collapse"""
        if not expanded:
            # Pane collapsed – clear overlays
            if hasattr(self, 'current_chart_data'):
                self.moving_avg_checkbox.setChecked(False)
                self.confidence_checkbox.setChecked(False)
                self.stats_annotations_checkbox.setChecked(False)
                self.outliers_checkbox.setChecked(False)
                # Note: Keep hover tooltips enabled even when pane is collapsed
                self.regenerate_chart_without_overlays()
    
    def open_export_dialog(self):
        """Open the chart export dialog"""
        if not CHARTS_AVAILABLE:
            return
        try:
            from ui.chart_export_dialog import ChartExportDialog
            
            if not hasattr(self, 'chart_manager') or not self.chart_manager:
                QtWidgets.QMessageBox.warning(self, "Export Error", 
                                            "No chart available to export. Please generate a chart first.")
                return
            
            # Open export dialog
            export_dialog = ChartExportDialog(self.chart_manager, self)
            export_dialog.exec()
            
        except ImportError as e:
            QtWidgets.QMessageBox.critical(self, "Export Error", 
                                         f"Export functionality not available: {e}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export Error", 
                                         f"Error opening export dialog: {e}")


