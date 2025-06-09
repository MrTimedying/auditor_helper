from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtCharts import QChart, QChartView
from typing import Dict, Any
import os # Added for path handling

from analysis_module.drag_drop_list_widget import DragDropListWidget
from analysis_module.data_manager import DataManager
from analysis_module.chart_manager import ChartManager

basedir = os.path.dirname(__file__)

class AnalysisWidget(QtWidgets.QMainWindow):
    def __init__(self, parent=None): 
        super().__init__(parent)
        self.setWindowTitle("Data Analysis")
        self.setWindowFlags(QtCore.Qt.Window)
        self.resize(1200, 800)  # Set a reasonable default size
        self.setWindowIcon(QtGui.QIcon(os.path.join(basedir, "icons", "app_icon.ico"))) # Set app icon
        
        # Create a central widget to hold all existing content
        self.central_widget = QtWidgets.QWidget()
        self.setCentralWidget(self.central_widget)

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
        
        # Create tabs: Numerical Statistics and Graphs
        self.tabs = QtWidgets.QTabWidget()
        content_layout.addWidget(self.tabs)

        self.numerical_tab = QtWidgets.QWidget()
        self.graphs_tab = QtWidgets.QWidget()

        self.tabs.addTab(self.numerical_tab, "Numerical Statistics")
        self.tabs.addTab(self.graphs_tab, "Graphs")

        # Setup tabs
        self.setup_numerical_statistics_tab()
        self.setup_graphs_tab()
        
        # Initialize ChartManager after chart_view is created
        self.chart_manager = ChartManager(self.chart_view)
        
        # Initialize intelligent suggestion system
        from analysis_module.variable_suggestions import IntelligentVariableSuggester
        self.suggestion_engine = IntelligentVariableSuggester()
        
        # Populate theme combo with available themes
        self.populate_theme_combo()
        
        # Initialize data
        self.current_week_id = None
        self.current_start_date = None
        self.current_end_date = None

    def create_data_selection_controls(self, main_layout):
        """Create the data selection controls for time range and week selection"""
        selection_group = QtWidgets.QGroupBox("Data Selection")
        # Note: Styling handled by main stylesheet
        selection_layout = QtWidgets.QHBoxLayout(selection_group)
        selection_layout.setSpacing(15)  # Reduced spacing
        selection_layout.setContentsMargins(10, 10, 10, 10)  # Reduced margins
        
        # Time Range Selection
        time_range_group = QtWidgets.QGroupBox("Time Range Selection")
        # Note: Styling handled by main stylesheet
        time_range_layout = QtWidgets.QHBoxLayout(time_range_group)
        time_range_layout.setSpacing(8)  # Reduced spacing
        time_range_layout.setContentsMargins(8, 8, 8, 8)  # Reduced margins
        
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
        
        selection_layout.addWidget(time_range_group)
        
        # Week Selection
        week_group = QtWidgets.QGroupBox("Specific Week Selection")
        # Note: Styling handled by main stylesheet
        week_layout = QtWidgets.QHBoxLayout(week_group)
        week_layout.setSpacing(8)  # Reduced spacing
        week_layout.setContentsMargins(8, 8, 8, 8)  # Reduced margins
        
        week_label = QtWidgets.QLabel("Week:")
        week_label.setMinimumWidth(40)
        week_layout.addWidget(week_label)
        
        self.week_combo = QtWidgets.QComboBox()
        self.week_combo.addItem("Select a week...", None)
        self.week_combo.setMinimumWidth(150)
        self.populate_week_combo()
        week_layout.addWidget(self.week_combo)
        
        self.apply_week_btn = QtWidgets.QPushButton("Apply Week")
        self.apply_week_btn.setMinimumWidth(100)
        self.apply_week_btn.clicked.connect(self.apply_week_selection)
        week_layout.addWidget(self.apply_week_btn)
        
        selection_layout.addWidget(week_group)
        
        main_layout.addWidget(selection_group)

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
        
        # Variable Selection (more compact)
        variable_group = QtWidgets.QGroupBox("Variable Selection")
        variable_layout = QtWidgets.QVBoxLayout(variable_group)
        variable_layout.setContentsMargins(6, 6, 6, 6)  # Smaller margins
        variable_layout.setSpacing(4)  # Tighter spacing
        
        # Available Variables (more compact)
        available_label = QtWidgets.QLabel("Available Variables:")
        available_label.setStyleSheet("QLabel { font-weight: bold; color: #D6D6D6; font-size: 14px; }")
        variable_layout.addWidget(available_label)
        
        # Add helper text for data types (smaller)
        data_types_help = QtWidgets.QLabel("📊 = Categories  •  📈 = Numbers")
        data_types_help.setStyleSheet("QLabel { color: #D6D6D6; font-size: 9px; margin-bottom: 3px; }")
        data_types_help.setWordWrap(True)
        variable_layout.addWidget(data_types_help)
        
        # Add suggestion legend
        suggestion_help = QtWidgets.QLabel("⭐ = Highly Recommended  •  ✨ = Recommended  •  ⚠️ = Warning")
        suggestion_help.setStyleSheet("QLabel { color: #D6D6D6; font-size: 9px; margin-bottom: 3px; }")
        suggestion_help.setWordWrap(True)
        variable_layout.addWidget(suggestion_help)
        
        self.available_variables_list = DragDropListWidget("available", self)
        self.available_variables_list.setMinimumHeight(100)  # Smaller
        self.available_variables_list.setMaximumHeight(100)
        variable_layout.addWidget(self.available_variables_list)
        
        # Selected X Variable (more compact)
        x_label = QtWidgets.QLabel("X-axis Variable:")
        x_label.setStyleSheet("QLabel { font-weight: bold; color: #D6D6D6; font-size: 14px; }")
        variable_layout.addWidget(x_label)
        
        self.x_variable_list = DragDropListWidget("x_variable", self)
        self.x_variable_list.setMinimumHeight(30)  # Smaller
        self.x_variable_list.setMaximumHeight(30)
        variable_layout.addWidget(self.x_variable_list)
        
        # Selected Y Variables (more compact)
        y_label = QtWidgets.QLabel("Y-axis Variables:")
        y_label.setStyleSheet("QLabel { font-weight: bold; color: #D6D6D6; font-size: 14px; }")
        variable_layout.addWidget(y_label)
        
        self.y_variables_list = DragDropListWidget("y_variables", self)
        self.y_variables_list.setMinimumHeight(60)  # Smaller
        self.y_variables_list.setMaximumHeight(60)
        variable_layout.addWidget(self.y_variables_list)
        
        left_layout.addWidget(variable_group)
        
        # Chart Type Selection (more compact, stacked below variables)
        chart_type_group = QtWidgets.QGroupBox("Chart Type")
        chart_type_layout = QtWidgets.QVBoxLayout(chart_type_group)
        chart_type_layout.setContentsMargins(6, 6, 6, 6)  # Smaller margins
        chart_type_layout.setSpacing(4)  # Tighter spacing
        
        chart_type_label = QtWidgets.QLabel("Select Chart Type:")
        chart_type_label.setStyleSheet("QLabel { font-weight: bold; color: #D6D6D6; font-size: 14px; }")
        chart_type_layout.addWidget(chart_type_label)
        
        self.chart_type_combo = QtWidgets.QComboBox()
        self.chart_type_combo.addItems(["Line Chart", "Bar Chart", "Scatter Plot", "Pie Chart"])
        self.chart_type_combo.currentTextChanged.connect(self.on_chart_type_changed)
        chart_type_layout.addWidget(self.chart_type_combo)
        
        # Chart Theme Selection
        theme_label = QtWidgets.QLabel("Chart Theme:")
        theme_label.setStyleSheet("QLabel { font-weight: bold; color: #D6D6D6; font-size: 14px; margin-top: 8px; }")
        chart_type_layout.addWidget(theme_label)
        
        self.theme_combo = QtWidgets.QComboBox()
        # Populate with available themes after chart_manager is initialized
        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        chart_type_layout.addWidget(self.theme_combo)
        
        # Generate Chart Button (moved here)
        self.generate_chart_btn = QtWidgets.QPushButton("Generate Chart")
        self.generate_chart_btn.setMinimumHeight(30)  # Smaller
        self.generate_chart_btn.clicked.connect(self.generate_chart)
        chart_type_layout.addWidget(self.generate_chart_btn)
        
        # Chart Type Suggestions Panel
        suggestions_label = QtWidgets.QLabel("Chart Suggestions:")
        suggestions_label.setStyleSheet("QLabel { font-weight: bold; color: #D6D6D6; font-size: 12px; margin-top: 8px; }")
        chart_type_layout.addWidget(suggestions_label)
        
        self.chart_suggestions_text = QtWidgets.QLabel("Select variables to see chart type recommendations")
        self.chart_suggestions_text.setStyleSheet("QLabel { color: #A0A0A0; font-size: 9px; }")
        self.chart_suggestions_text.setWordWrap(True)
        self.chart_suggestions_text.setMinimumHeight(40)
        chart_type_layout.addWidget(self.chart_suggestions_text)
        
        left_layout.addWidget(chart_type_group)
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
        
        # Initialize available variables
        self.populate_available_variables()
    
    def populate_theme_combo(self):
        """Populate the theme combo with available chart themes"""
        if hasattr(self, 'chart_manager'):
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
        if hasattr(self, 'chart_manager'):
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

    def populate_available_variables(self):
        """Populate the available variables list with all chartable variables and suggestions"""
        variables = [
            # Raw Task Data - Categorical
            ("project_name", "categorical", "📊 Project Name (Categories)"),
            ("locale", "categorical", "📊 Locale (Categories)"),
            ("date_audited", "categorical", "📊 Date Audited (Categories)"),
            ("week_id", "categorical", "📊 Week ID (Categories)"),
            
            # Raw Task Data - Quantitative  
            ("duration", "quantitative", "📈 Duration (Seconds)"),
            ("time_limit", "quantitative", "📈 Time Limit (Seconds)"),
            ("score", "quantitative", "📈 Score (Number)"),
            ("bonus_paid", "quantitative", "📈 Bonus Paid (0/1)"),
            
            # Composite Metrics - Quantitative
            ("total_time", "quantitative", "📈 Total Time (Hours)"),
            ("average_time", "quantitative", "📈 Average Time (Hours)"),
            ("time_limit_usage", "quantitative", "📈 Time Limit Usage (%)"),
            ("fail_rate", "quantitative", "📈 Fail Rate (%)"),
            ("bonus_tasks_count", "quantitative", "📈 Bonus Tasks Count"),
            ("total_earnings", "quantitative", "📈 Total Earnings ($)"),
        ]
        
        self.available_variables_list.clear()
        
        # Get current selection context for suggestions
        current_selection = self._get_current_selection_context()
        
        # Get variable suggestions (if suggestion engine is available)
        suggestions = []
        if hasattr(self, 'suggestion_engine'):
            available_vars = [(var_name, var_type) for var_name, var_type, _ in variables]
            suggestions = self.suggestion_engine.get_variable_suggestions(
                current_selection, available_vars
            )
        
        # Create a mapping of variable names to suggestions
        suggestion_map = {}
        for suggestion in suggestions:
            if suggestion.variable_name not in suggestion_map:
                suggestion_map[suggestion.variable_name] = []
            suggestion_map[suggestion.variable_name].append(suggestion)
        
        # Add variables with suggestion indicators
        for var_name, var_type, display_name in variables:
            # Get the best suggestion for this variable
            var_suggestions = suggestion_map.get(var_name, [])
            suggestion_info = None
            
            if var_suggestions:
                # Use the highest confidence suggestion
                best_suggestion = max(var_suggestions, key=lambda s: s.confidence)
                suggestion_info = {
                    "type": best_suggestion.suggestion_type.value,
                    "reason": best_suggestion.reason,
                    "confidence": best_suggestion.confidence
                }
            
            self.available_variables_list.add_variable_with_suggestion(
                var_name, var_type, display_name, suggestion_info
            )
    
    def _get_current_selection_context(self) -> Dict[str, Any]:
        """Get the current variable selection context for suggestions"""
        context = {
            "x_variable": None,
            "y_variables": [],
            "chart_type": self.chart_type_combo.currentText() if hasattr(self, 'chart_type_combo') else None
        }
        
        # Get X variable
        if hasattr(self, 'x_variable_list') and self.x_variable_list.count() > 0:
            x_item = self.x_variable_list.item(0)
            context["x_variable"] = x_item.data(QtCore.Qt.UserRole)
        
        # Get Y variables
        if hasattr(self, 'y_variables_list'):
            for i in range(self.y_variables_list.count()):
                y_item = self.y_variables_list.item(i)
                context["y_variables"].append(y_item.data(QtCore.Qt.UserRole))
        
        return context
    
    def update_variable_suggestions(self):
        """Update variable suggestions based on current selection"""
        if not hasattr(self, 'suggestion_engine'):
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
        """Generate chart based on selected variables and chart type with enhanced error handling"""
        try:
            # Get selected variables
            x_variable = None
            y_variables = []
            
            if self.x_variable_list.count() > 0:
                x_item = self.x_variable_list.item(0)
                x_variable = x_item.data(QtCore.Qt.UserRole)
            
            for i in range(self.y_variables_list.count()):
                y_item = self.y_variables_list.item(i)
                y_variables.append(y_item.data(QtCore.Qt.UserRole))
            
            # Enhanced validation with better user guidance
            if not x_variable:
                self._show_selection_guidance("No X-axis Variable Selected", 
                    "Please drag a variable to the X-axis area to create a chart.",
                    ["Drag a variable from 'Available Variables' to 'X-Axis Variable'",
                     "Categorical variables (like Project Name, Locale) work well for X-axis",
                     "Time-based variables (like Date Audited) are good for trend analysis"])
                return
            
            if not y_variables:
                self._show_selection_guidance("No Y-axis Variables Selected",
                    "Please drag at least one variable to the Y-axis area to create a chart.",
                    ["Drag one or more variables from 'Available Variables' to 'Y-Axis Variables'",
                     "Quantitative variables (like Duration, Score, Earnings) work well for Y-axis",
                     "You can select multiple Y variables to compare them on the same chart"])
                return
            
            # Check for data selection
            if not self._has_valid_data_selection():
                self._show_data_selection_guidance()
                return
            
            # Get chart type
            chart_type = self.chart_type_combo.currentText()
            
            # Progressive disclosure: Show pre-generation guidance for complex scenarios
            if self._should_show_pre_generation_guidance(x_variable, y_variables, chart_type):
                if not self._show_pre_generation_guidance(x_variable, y_variables, chart_type):
                    return  # User chose to cancel
            
            # Show loading indicator for large datasets
            self._show_loading_state(True)
            
            # Get data based on current selection
            data = self.get_chart_data(x_variable, y_variables)
            
            if not data:
                self._show_data_guidance("No Data Available",
                    "No data was found for the selected variables and time range.",
                    ["Try selecting a different time range with more data",
                     "Check if tasks exist for the selected period",
                     "Verify that data import was successful",
                     "Some variable combinations may not have overlapping data"])
                return

            # Generate chart with enhanced error handling
            self.chart_manager.create_chart(data, x_variable, y_variables, chart_type)
            
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

        if tasks_data:
            self.populate_numerical_statistics(tasks_data)

    def refresh_analysis_by_time_range(self, start_date, end_date):
        """Refresh analysis for a specific time range"""
        tasks_data = self.data_manager.get_tasks_data_by_time_range(start_date, end_date)
        
        if tasks_data:
            self.populate_numerical_statistics(tasks_data)

    def populate_numerical_statistics(self, tasks_data):
        """Populate the numerical statistics tables with calculated data"""
        if not tasks_data:
            self.clear_all_data()
            return

        # Calculate aggregate statistics
        aggregate_stats = self.data_manager.calculate_aggregate_statistics(tasks_data)
        
        # Populate aggregate table
        self.populate_aggregate_table(aggregate_stats)
        
        # Calculate daily statistics
        daily_stats = self.data_manager.calculate_daily_statistics(tasks_data)
        
        # Populate daily table
        self.populate_daily_table(daily_stats)
        
        # Update daily project dropdown
        self.update_daily_project_dropdown(daily_stats.keys())
        
        # Calculate and populate project breakdown
        project_stats = self.data_manager.calculate_project_statistics(tasks_data)
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
        
        # Calculate daily project breakdown
        project_data = self.data_manager.calculate_project_statistics(tasks_data)

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
        """Clear all data from tables"""
        # Clear aggregate table
        for col in range(self.aggregate_table.columnCount()):
            item = QtWidgets.QTableWidgetItem("")
            item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEditable)
            self.aggregate_table.setItem(0, col, item)
        
        # Clear daily table
        self.daily_table.setRowCount(0)
        
        # Clear project tables
        self.project_aggregate_table.setRowCount(0)
        self.daily_project_table.setRowCount(0)
        
        # Clear daily project dropdown
        self.daily_project_combo.clear()
        self.daily_project_combo.addItem("Select a day...", None)

    def on_chart_type_changed(self):
        """Handle chart type change"""
        if hasattr(self, 'suggestion_engine'):
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


