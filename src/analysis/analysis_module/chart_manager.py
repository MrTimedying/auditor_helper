from PySide6.QtCharts import QChart, QChartView, QLineSeries, QBarSeries, QBarSet, QScatterSeries, QPieSeries, QPieSlice, QValueAxis, QBarCategoryAxis
from PySide6 import QtCore, QtGui
from enum import Enum
from typing import List, Tuple, Dict, Any, Optional

# Import from dedicated modules
from .chart_validation import ValidationIssue, ChartValidationEngine
from .chart_styling import ChartStyleManager, ResponsiveChartManager
from .statistical_analysis import StatisticalAnalysis
from .chart_interaction_manager import ChartInteractionManager

# Legacy validation class removed - now using dedicated chart_validation module

class SemanticColorManager:
    """Manages consistent, semantic color assignment for chart variables"""
    
    # Semantic color mappings for specific variable types
    SEMANTIC_COLORS = {
        # Performance metrics (negative indicators)
        "fail_rate": "#E74C3C",           # Red for failure rates
        "error_rate": "#E74C3C",          # Red for error rates
        "failure_count": "#E74C3C",       # Red for failure counts
        
        # Financial metrics (positive indicators)
        "total_earnings": "#27AE60",      # Green for earnings
        "earnings": "#27AE60",            # Green for earnings
        "revenue": "#27AE60",             # Green for revenue
        "profit": "#27AE60",              # Green for profit
        "income": "#27AE60",              # Green for income
        
        # Time-related metrics
        "duration": "#3498DB",            # Blue for time/duration
        "time": "#3498DB",                # Blue for time
        "total_time": "#3498DB",          # Blue for total time
        "average_time": "#3498DB",        # Blue for average time
        "elapsed_time": "#3498DB",        # Blue for elapsed time
        
        # Performance/Score metrics
        "score": "#F39C12",               # Orange for scores
        "rating": "#F39C12",              # Orange for ratings
        "performance": "#F39C12",         # Orange for performance
        "efficiency": "#F39C12",          # Orange for efficiency
        
        # Count/Quantity metrics
        "count": "#9B59B6",               # Purple for counts
        "total_count": "#9B59B6",         # Purple for total counts
        "quantity": "#9B59B6",            # Purple for quantities
        
        # Percentage metrics
        "percentage": "#E67E22",          # Dark orange for percentages
        "percent": "#E67E22",             # Dark orange for percentages
        "rate": "#E67E22",                # Dark orange for rates
    }
    
    # Accessibility-friendly palette for general variables
    # Colors chosen for good contrast and color-blind accessibility
    ACCESSIBLE_PALETTE = [
        "#1f77b4",  # Blue
        "#ff7f0e",  # Orange  
        "#2ca02c",  # Green
        "#d62728",  # Red
        "#9467bd",  # Purple
        "#8c564b",  # Brown
        "#e377c2",  # Pink
        "#7f7f7f",  # Gray
        "#bcbd22",  # Olive
        "#17becf",  # Cyan
        "#aec7e8",  # Light blue
        "#ffbb78",  # Light orange
        "#98df8a",  # Light green
        "#ff9896",  # Light red
        "#c5b0d5",  # Light purple
    ]
    
    def __init__(self):
        self.variable_color_registry = {}
        self.next_palette_index = 0
    
    def get_variable_color(self, variable_name: str) -> str:
        """Get consistent color for a variable based on semantic meaning or registry"""
        # Normalize variable name for comparison
        var_name_lower = variable_name.lower().replace(" ", "_")
        
        # Check if we already assigned a color to this variable
        if variable_name in self.variable_color_registry:
            return self.variable_color_registry[variable_name]
        
        # Check semantic mapping first
        for semantic_key, color in self.SEMANTIC_COLORS.items():
            if semantic_key in var_name_lower:
                self.variable_color_registry[variable_name] = color
                return color
        
        # Fallback to palette assignment
        color = self.ACCESSIBLE_PALETTE[self.next_palette_index % len(self.ACCESSIBLE_PALETTE)]
        self.variable_color_registry[variable_name] = color
        self.next_palette_index += 1
        
        return color
    
    def get_variable_colors(self, variable_names: list) -> list:
        """Get colors for multiple variables"""
        return [self.get_variable_color(name) for name in variable_names]
    
    def reset_registry(self):
        """Reset the color registry (useful for testing or new sessions)"""
        self.variable_color_registry.clear()
        self.next_palette_index = 0

class ChartManager:
    def __init__(self, chart_view: QChartView):
        self.chart_view = chart_view
        self.chart = chart_view.chart()
        self.color_manager = SemanticColorManager()
        self.validation_engine = ChartValidationEngine()
        self.style_manager = ChartStyleManager()
        self.responsive_manager = ResponsiveChartManager(self.style_manager)
        
        # NEW: Statistical analysis & interactive manager
        self.stats_engine = StatisticalAnalysis()
        self.interaction_manager = ChartInteractionManager(self.chart_view)
        
        # Toggle flags set by UI
        self.show_trend_line = False
        
        # Initialize with professional theme
        self.style_manager.set_theme("professional")
        
    def set_chart_theme(self, theme_name: str):
        """Set the chart theme for styling"""
        self.style_manager.set_theme(theme_name)
        
    def get_available_themes(self) -> List[str]:
        """Get list of available chart themes"""
        return self.style_manager.get_available_themes()

    def create_chart(self, data, x_variable, y_variables, chart_type):
        """Create QtChart based on data and configuration with comprehensive validation"""
        try:
            # Validate the chart request
            validation_issues = self.validation_engine.validate_chart_request(
                data, x_variable, y_variables, chart_type
            )
            
            # Check for critical errors that prevent chart creation
            critical_issues = [issue for issue in validation_issues 
                             if issue.severity == ValidationIssue.Severity.ERROR or 
                                issue.severity == ValidationIssue.Severity.CRITICAL]
            
            if critical_issues:
                # Show critical error and abort
                error_messages = [issue.message for issue in critical_issues]
                self._show_chart_error("Chart Creation Failed", error_messages, critical_issues[0].suggestions)
                return
            
            # Show warnings and info messages but continue with chart creation
            warning_issues = [issue for issue in validation_issues 
                            if issue.severity in [ValidationIssue.Severity.WARNING, ValidationIssue.Severity.INFO]]
            
            if warning_issues:
                self._show_chart_warnings(warning_issues)
            
            # Clear previous chart
            self.chart.removeAllSeries()
            for axis in self.chart.axes():
                self.chart.removeAxis(axis)
            
            # Set chart title
            x_var_name, x_var_type = x_variable
            chart_title = f"{chart_type}: {x_var_name} vs {', '.join([y[0] for y in y_variables])}"
            self.chart.setTitle(chart_title)
            
            # Create chart based on type
            if chart_type == "Line Chart":
                self.create_line_chart(data, x_variable, y_variables)
            elif chart_type == "Bar Chart":
                self.create_bar_chart(data, x_variable, y_variables)
            elif chart_type == "Scatter Plot":
                self.create_scatter_chart(data, x_variable, y_variables)
            elif chart_type == "Pie Chart":
                self.create_pie_chart(data, x_variable, y_variables)
            else:
                self._show_chart_error("Unsupported Chart Type", [f"Chart type '{chart_type}' is not supported."], 
                                     ["Select a supported chart type: Line Chart, Bar Chart, Scatter Plot, or Pie Chart"])
                
        except Exception as e:
            # Handle unexpected errors gracefully
            self._show_chart_error("Unexpected Error", [f"An unexpected error occurred: {str(e)}"], 
                                 ["Try again with different variables", "Contact support if the problem persists"])
            print(f"Error in create_chart: {e}")  # Log for debugging
    
    def _show_chart_error(self, title: str, messages: List[str], suggestions: List[str]):
        """Show chart error with detailed message and suggestions"""
        from PySide6 import QtWidgets
        
        error_text = "\n".join(messages)
        if suggestions:
            error_text += "\n\nSuggestions:\n" + "\n".join(f"• {suggestion}" for suggestion in suggestions)
        
        msg_box = QtWidgets.QMessageBox()
        msg_box.setIcon(QtWidgets.QMessageBox.Critical)
        msg_box.setWindowTitle(title)
        msg_box.setText(error_text)
        msg_box.exec()
        
        # Show helpful message in chart area
        self.chart.removeAllSeries()
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)
        self.chart.setTitle(f"Error: {messages[0]}")
    
    def _show_chart_warnings(self, warning_issues: List[ValidationIssue]):
        """Show chart warnings and info messages"""
        from PySide6 import QtWidgets
        
        warning_messages = []
        info_messages = []
        
        for issue in warning_issues:
            if issue.severity == ValidationIssue.Severity.WARNING:
                warning_messages.append(issue.message)
            else:  # INFO
                info_messages.append(issue.message)
        
        if warning_messages:
            warning_text = "⚠️ Warnings:\n" + "\n".join(f"• {msg}" for msg in warning_messages)
            if info_messages:
                warning_text += "\n\nℹ️ Information:\n" + "\n".join(f"• {msg}" for msg in info_messages)
            
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Warning)
            msg_box.setWindowTitle("Chart Generation Warnings")
            msg_box.setText(warning_text)
            msg_box.exec()
        elif info_messages:
            info_text = "ℹ️ Information:\n" + "\n".join(f"• {msg}" for msg in info_messages)
            
            msg_box = QtWidgets.QMessageBox()
            msg_box.setIcon(QtWidgets.QMessageBox.Information)
            msg_box.setWindowTitle("Chart Information")
            msg_box.setText(info_text)
            msg_box.exec()
    
    def create_line_chart(self, data, x_variable, y_variables):
        """Create line chart with error handling"""
        try:
            x_var_name, x_var_type = x_variable
            
            # Get colors for all Y variables using new styling system
            y_var_names = [y[0] for y in y_variables]
            colors = [self.style_manager.get_semantic_color(name) for name in y_var_names]
            
            # Create series for each Y variable
            for i, (y_var_name, y_var_type) in enumerate(y_variables):
                series = QLineSeries()
                series.setName(y_var_name)
                
                # Apply semantic color
                color = QtGui.QColor(colors[i])
                series_pen = QtGui.QPen(color)
                series_pen.setWidth(2)
                series.setPen(series_pen)
                
                x_values = []
                y_values = []
                
                # Iterate over data rows
                for row in data:
                    try:
                        x_val = row[0]
                        y_val = row[i + 1] if len(row) > i + 1 else None
                        if x_val is None or y_val is None:
                            continue
                        # Convert categorical x to index for plotting
                        if x_var_type == "categorical":
                            x_numeric = len(x_values)
                        else:
                            x_numeric = float(x_val)
                        y_numeric = float(y_val)
                        series.append(x_numeric, y_numeric)
                        x_values.append(x_numeric)
                        y_values.append(y_numeric)
                    except Exception as e:
                        print(f"Warning: Skipped point due to error: {e}")
                        continue
                self.chart.addSeries(series)

                # NEW: add trend line overlay
                if self.show_trend_line and x_values and len(y_variables) == 1:
                    try:
                        trend_points = self.stats_engine.generate_trend_points(x_values, y_values)
                        if trend_points:
                            trend_series = QLineSeries()
                            trend_series.setName(f"{y_var_name} (Trend)")
                            trend_pen = QtGui.QPen(QtGui.QColor(color).lighter(120))
                            trend_pen.setWidth(2)
                            trend_pen.setStyle(QtCore.Qt.DashLine)
                            trend_series.setPen(trend_pen)
                            for x, y in trend_points:
                                trend_series.append(x, y)
                            self.chart.addSeries(trend_series)
                    except Exception as e:
                        print(f"Warning: Trend line generation failed: {e}")
            
            # Create axes with error handling
            self._create_axes(data, x_variable, y_variables, "line")
            
            # Apply final styling after series and axes are set up
            self._apply_final_chart_styling()
            
            # Set up hover tooltips with chart data and metadata
            self._setup_hover_tooltips(data, x_variable, y_variables)
            
        except Exception as e:
            raise Exception(f"Failed to create line chart: {str(e)}")
    
    def create_bar_chart(self, data, x_variable, y_variables):
        """Create bar chart with error handling"""
        try:
            x_var_name, x_var_type = x_variable
            
            # Create bar series
            series = QBarSeries()
            
            # Get colors for all Y variables using new styling system
            y_var_names = [y[0] for y in y_variables]
            colors = [self.style_manager.get_semantic_color(name) for name in y_var_names]
            
            # Create bar sets for each Y variable
            for i, (y_var_name, y_var_type) in enumerate(y_variables):
                bar_set = QBarSet(y_var_name)
                
                # Apply semantic color
                color = QtGui.QColor(colors[i])
                bar_set.setColor(color)
                
                for row in data:
                    try:
                        y_val = row[y_variables.index((y_var_name, y_var_type)) + 1] if len(row) > i + 1 else 0
                        bar_set.append(float(y_val) if y_val is not None else 0)
                    except (ValueError, TypeError, IndexError):
                        bar_set.append(0)  # Fallback for invalid data
                
                series.append(bar_set)
            
            self.chart.addSeries(series)
            
            # Create axes
            self._create_axes(data, x_variable, y_variables, "bar")
            
            # Apply final styling after series and axes are set up
            self._apply_final_chart_styling()
            
            # Set up hover tooltips with chart data and metadata
            self._setup_hover_tooltips(data, x_variable, y_variables)
            
        except Exception as e:
            raise Exception(f"Failed to create bar chart: {str(e)}")
    
    def create_scatter_chart(self, data, x_variable, y_variables):
        """Create scatter plot with error handling"""
        try:
            if not y_variables:
                raise Exception("Scatter plot requires at least one Y variable")
                
            y_var_name, y_var_type = y_variables[0]
            
            series = QScatterSeries()
            series.setName(f"{x_variable[0]} vs {y_var_name}")
            series.setMarkerSize(8)
            
            # Apply semantic color using new styling system
            color = self.style_manager.get_semantic_color(y_var_name)
            series.setColor(QtGui.QColor(color))
            
            # Add data points
            for row_idx, row in enumerate(data):
                try:
                    x_val = row[0]
                    y_val = row[1] if len(row) > 1 else 0  # First Y variable
                    
                    # Convert values for plotting
                    x_var_name, x_var_type = x_variable
                    if x_var_type == "categorical":
                        x_plot = float(row_idx)
                    else:
                        try:
                            x_plot = float(x_val) if x_val is not None else float(row_idx)
                        except (ValueError, TypeError):
                            x_plot = float(row_idx)
                    
                    try:
                        y_plot = float(y_val) if y_val is not None else 0
                    except (ValueError, TypeError):
                        y_plot = 0
                    
                    series.append(x_plot, y_plot)
                    
                except Exception as e:
                    print(f"Warning: Skipped data point at row {row_idx}: {e}")
                    continue
            
            self.chart.addSeries(series)
            
            # Create axes
            self._create_axes(data, x_variable, [y_variables[0]], "scatter")
            
            # Apply final styling after series and axes are set up
            self._apply_final_chart_styling()
            
            # Set up hover tooltips with chart data and metadata
            self._setup_hover_tooltips(data, x_variable, y_variables)
            
        except Exception as e:
            raise Exception(f"Failed to create scatter plot: {str(e)}")
    
    def create_pie_chart(self, data, x_variable, y_variables):
        """Create pie chart with error handling"""
        try:
            if not y_variables:
                raise Exception("Pie chart requires exactly one Y variable")
                
            y_var_name, y_var_type = y_variables[0]
            
            series = QPieSeries()
            
            # Get colors for pie slices based on X variable categories using styling system
            x_categories = [str(row[0]) for row in data]
            colors = [self.style_manager.get_semantic_color(cat) for cat in x_categories]
            
            for i, row in enumerate(data):
                try:
                    label = str(row[0]) if row[0] is not None else f"Category {i+1}"  # X variable as label
                    value = float(row[1]) if len(row) > 1 and row[1] is not None else 0  # First Y variable as value
                    
                    # Skip zero or negative values for pie charts
                    if value <= 0:
                        continue
                    
                    slice = QPieSlice(label, value)
                    # Apply semantic color to each slice
                    slice.setColor(QtGui.QColor(colors[i % len(colors)]))
                    series.append(slice)
                    
                except Exception as e:
                    print(f"Warning: Skipped pie slice at row {i}: {e}")
                    continue
            
            if series.count() == 0:
                raise Exception("No valid data for pie chart (all values are zero or invalid)")
            
            self.chart.addSeries(series)
            
            # Set up hover tooltips with chart data and metadata
            self._setup_hover_tooltips(data, x_variable, y_variables)
            
        except Exception as e:
            raise Exception(f"Failed to create pie chart: {str(e)}")
    
    def _create_axes(self, data, x_variable, y_variables, chart_type):
        """Create chart axes with error handling and proper grid styling"""
        try:
            x_var_name, x_var_type = x_variable
            
            # Get current theme for styling
            current_theme = self.style_manager.get_theme()
            
            # Create X axis
            if x_var_type == "categorical":
                categories = [str(row[0]) if row[0] is not None else f"Item {i+1}" for i, row in enumerate(data)]
                axis_x = QBarCategoryAxis()
                axis_x.append(categories)
                axis_x.setTitleText(x_var_name)
            else:
                axis_x = QValueAxis()
                axis_x.setTitleText(x_var_name)
            
            # Style X axis with theme colors
            text_color = QtGui.QColor(current_theme.colors.get('text', '#D6D6D6'))
            axis_x.setTitleBrush(QtGui.QBrush(text_color))
            axis_x.setLabelsBrush(QtGui.QBrush(text_color))
            axis_x.setLinePenColor(text_color)
            
            # Configure X axis grid (dotted, thin, blended)
            if hasattr(axis_x, 'setGridLineVisible'):
                axis_x.setGridLineVisible(True)
                # Create dotted pen for grid lines
                grid_pen = QtGui.QPen(QtGui.QColor(current_theme.colors.get('grid', '#E5E7EB')))
                grid_pen.setStyle(QtCore.Qt.DotLine)  # Dotted style
                grid_pen.setWidth(1)  # Thin lines
                grid_pen.setColor(QtGui.QColor(current_theme.colors.get('grid', '#E5E7EB')))
                if hasattr(axis_x, 'setGridLinePen'):
                    axis_x.setGridLinePen(grid_pen)
            
            self.chart.addAxis(axis_x, QtCore.Qt.AlignBottom)
            
            # Create Y axis (skip for pie charts)
            if chart_type != "pie":
                axis_y = QValueAxis()
                if len(y_variables) == 1:
                    axis_y.setTitleText(y_variables[0][0])
                else:
                    axis_y.setTitleText("Values")
                
                # Style Y axis with theme colors
                axis_y.setTitleBrush(QtGui.QBrush(text_color))
                axis_y.setLabelsBrush(QtGui.QBrush(text_color))
                axis_y.setLinePenColor(text_color)
                
                # Configure Y axis grid (dotted, thin, blended)
                if hasattr(axis_y, 'setGridLineVisible'):
                    axis_y.setGridLineVisible(True)
                    # Create dotted pen for grid lines
                    grid_pen = QtGui.QPen(QtGui.QColor(current_theme.colors.get('grid', '#E5E7EB')))
                    grid_pen.setStyle(QtCore.Qt.DotLine)  # Dotted style
                    grid_pen.setWidth(1)  # Thin lines
                    # Make grid more blended by reducing opacity
                    grid_color = QtGui.QColor(current_theme.colors.get('grid', '#E5E7EB'))
                    grid_color.setAlpha(int(255 * current_theme.layout.get('grid_alpha', 0.3)))
                    grid_pen.setColor(grid_color)
                    if hasattr(axis_y, 'setGridLinePen'):
                        axis_y.setGridLinePen(grid_pen)
                
                self.chart.addAxis(axis_y, QtCore.Qt.AlignLeft)
                
                # Attach axes to series
                for series in self.chart.series():
                    series.attachAxis(axis_x)
                    series.attachAxis(axis_y)
            else:
                # For pie charts, only attach X axis if needed
                for series in self.chart.series():
                    if hasattr(series, 'attachAxis'):
                        series.attachAxis(axis_x)
            
            # Apply additional chart-level grid styling if available
            self._apply_chart_grid_styling()
                        
        except Exception as e:
            print(f"Warning: Error creating axes: {e}")

    def _apply_chart_grid_styling(self):
        """Apply chart-level grid styling for dotted, thin, blended grid lines"""
        try:
            current_theme = self.style_manager.get_theme()
            
            # Set overall chart background
            self.chart.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(current_theme.colors.get('background', '#FFFFFF'))))
            
            # Configure plot area background
            self.chart.setPlotAreaBackgroundBrush(QtGui.QBrush(QtGui.QColor(current_theme.colors.get('surface', '#FFFFFF'))))
            self.chart.setPlotAreaBackgroundVisible(True)
            
            # Set chart margins for better grid visibility
            margins = current_theme.layout.get('margins', {'left': 0.1, 'right': 0.95, 'top': 0.9, 'bottom': 0.1})
            
            # Apply theme-specific styling
            if current_theme.name == "Dark Mode":
                # Dark theme specific adjustments
                self.chart.setBackgroundBrush(QtGui.QBrush(QtGui.QColor("#121212")))
                self.chart.setPlotAreaBackgroundBrush(QtGui.QBrush(QtGui.QColor("#1E1E1E")))
                
                # Update title and text colors for dark theme
                title_brush = QtGui.QBrush(QtGui.QColor("#FFFFFF"))
                self.chart.setTitleBrush(title_brush)
            
            elif current_theme.name == "Minimal":
                # Minimal theme - very subtle grid
                self.chart.setBackgroundBrush(QtGui.QBrush(QtGui.QColor("#FFFFFF")))
                self.chart.setPlotAreaBackgroundBrush(QtGui.QBrush(QtGui.QColor("#FFFFFF")))
            
            elif current_theme.name == "High Contrast":
                # High contrast theme - more visible but still dotted grid
                self.chart.setBackgroundBrush(QtGui.QBrush(QtGui.QColor("#FFFFFF")))
                self.chart.setPlotAreaBackgroundBrush(QtGui.QBrush(QtGui.QColor("#FFFFFF")))
                
        except Exception as e:
            print(f"Warning: Error applying chart grid styling: {e}")

    def _apply_final_chart_styling(self):
        """Apply final styling touches to the chart after all elements are in place"""
        try:
            current_theme = self.style_manager.get_theme()
            
            # Apply title styling with theme colors
            title_color = QtGui.QColor(current_theme.colors.get('text', '#2E3440'))
            self.chart.setTitleBrush(QtGui.QBrush(title_color))
            
            # Set title font
            title_font = QtGui.QFont()
            title_font.setPointSize(current_theme.typography.get('title_size', 16))
            title_font.setWeight(QtGui.QFont.Bold if current_theme.typography.get('title_weight') == 'bold' else QtGui.QFont.Normal)
            self.chart.setTitleFont(title_font)
            
            # Apply legend styling if legend exists
            legend = self.chart.legend()
            if legend:
                # Position legend under the title (top center)
                legend.setAlignment(QtCore.Qt.AlignTop)
                
                # Set legend font
                legend_font = QtGui.QFont()
                legend_font.setPointSize(current_theme.typography.get('legend_size', 10))
                legend.setFont(legend_font)
                
                # Set legend text color
                legend.setColor(QtGui.QColor(current_theme.colors.get('text', '#2E3440')))
                
                # Make legend visible
                legend.setVisible(True)
            
        except Exception as e:
            print(f"Warning: Error applying final chart styling: {e}")

    def clear_chart(self):
        """Clear the chart completely when variables are modified"""
        try:
            self.chart.removeAllSeries()
            # Remove all axes
            for axis in self.chart.axes():
                self.chart.removeAxis(axis)
            self.chart.setTitle("Select variables and click 'Generate Chart'")
        except Exception as e:
            print(f"Warning: Error clearing chart: {e}")
    
    def get_validation_engine(self) -> ChartValidationEngine:
        """Get the validation engine for external use"""
        return self.validation_engine 

    def enable_trend_line(self, enabled: bool):
        """Toggle trend line overlay for line charts."""
        self.show_trend_line = enabled
    
    def add_moving_average_overlay(self, data: List[Tuple], window_size: int = 5, overlay_type: str = 'simple'):
        """Add moving average overlay to line charts.
        
        Args:
            data: Chart data as list of (x, y) tuples (x can be numeric or string)
            window_size: Window size for moving average calculation
            overlay_type: 'simple' or 'exponential'
        """
        try:
            if not data or len(data) < window_size:
                return
            
            # Extract y values for moving average calculation
            y_values = []
            x_values = []
            
            for x_val, y_val in data:
                try:
                    y_values.append(float(y_val))
                    x_values.append(x_val)  # Keep original X values (could be dates)
                except (ValueError, TypeError):
                    print(f"Warning: Skipping invalid Y value: {y_val}")
                    continue
            
            if len(y_values) < window_size:
                print(f"Warning: Not enough valid data points ({len(y_values)}) for moving average window ({window_size})")
                return
            
            if overlay_type == 'simple':
                ma_values = self.stats_engine.calculate_moving_average(y_values, window_size)
            else:  # exponential
                ma_values = self.stats_engine.calculate_exponential_moving_average(y_values)
            
            # Create moving average series
            ma_series = QLineSeries()
            ma_series.setName(f"Moving Average ({window_size})")
            
            # Add points where moving average is available
            for i, x_val in enumerate(x_values):
                if i < len(ma_values) and ma_values[i] is not None:
                    # For date-based X values, use the index as the X coordinate
                    if isinstance(x_val, str):
                        ma_series.append(float(i), ma_values[i])
                    else:
                        ma_series.append(float(x_val), ma_values[i])
            
            # Style the moving average line
            current_theme = self.style_manager.get_theme()
            ma_color = current_theme.colors.get('secondary', '#5E81AC')
            ma_pen = QtGui.QPen(QtGui.QColor(ma_color))
            ma_pen.setWidth(2)
            ma_pen.setStyle(QtCore.Qt.DashLine)  # Dashed line for distinction
            ma_series.setPen(ma_pen)
            
            self.chart.addSeries(ma_series)
            
            # Attach to existing axes
            for axis in self.chart.axes():
                ma_series.attachAxis(axis)
                
        except Exception as e:
            print(f"Warning: Error adding moving average overlay: {e}")
    
    def add_confidence_bands(self, data: List[Tuple], confidence_level: float = 0.95):
        """Add confidence interval bands to line charts.
        
        Args:
            data: Chart data as list of (x, y) tuples (x can be numeric or string)
            confidence_level: Confidence level (0.95 for 95%, 0.99 for 99%)
        """
        try:
            if not data or len(data) < 3:
                return
            
            # Extract and convert values for statistical analysis
            x_values = []
            y_values = []
            original_x_values = []
            
            for i, (x_val, y_val) in enumerate(data):
                try:
                    # For statistical calculations, use index for date-based X values
                    if isinstance(x_val, str):
                        x_values.append(float(i))
                    else:
                        x_values.append(float(x_val))
                    
                    y_values.append(float(y_val))
                    original_x_values.append(x_val)
                except (ValueError, TypeError):
                    print(f"Warning: Skipping invalid data point: ({x_val}, {y_val})")
                    continue
            
            if len(x_values) < 3:
                print("Warning: Not enough valid data points for confidence intervals")
                return
            
            # Calculate confidence intervals
            confidence_intervals, prediction_bands = self.stats_engine.calculate_confidence_intervals(
                x_values, y_values, confidence_level
            )
            
            if not confidence_intervals:
                return
            
            # Create confidence interval series (upper and lower bounds)
            ci_upper_series = QLineSeries()
            ci_lower_series = QLineSeries()
            ci_upper_series.setName(f"Confidence {int(confidence_level*100)}% (Upper)")
            ci_lower_series.setName(f"Confidence {int(confidence_level*100)}% (Lower)")
            
            # Add confidence interval points
            for i, original_x_val in enumerate(original_x_values):
                if i < len(confidence_intervals):
                    lower_bound, upper_bound = confidence_intervals[i]
                    
                    # Use appropriate X coordinate for chart positioning
                    if isinstance(original_x_val, str):
                        chart_x = float(i)
                    else:
                        chart_x = float(original_x_val)
                    
                    ci_lower_series.append(chart_x, lower_bound)
                    ci_upper_series.append(chart_x, upper_bound)
            
            # Style confidence bands
            current_theme = self.style_manager.get_theme()
            ci_color = QtGui.QColor(current_theme.colors.get('accent', '#88C0D0'))
            ci_color.setAlpha(100)  # Semi-transparent
            
            ci_pen = QtGui.QPen(ci_color)
            ci_pen.setWidth(1)
            ci_pen.setStyle(QtCore.Qt.DotLine)
            
            ci_upper_series.setPen(ci_pen)
            ci_lower_series.setPen(ci_pen)
            
            self.chart.addSeries(ci_upper_series)
            self.chart.addSeries(ci_lower_series)
            
            # Attach to existing axes
            for axis in self.chart.axes():
                ci_upper_series.attachAxis(axis)
                ci_lower_series.attachAxis(axis)
                
        except Exception as e:
            print(f"Warning: Error adding confidence bands: {e}")
    
    def add_statistical_annotations(self, data: List[Tuple]) -> Dict[str, float]:
        """Add statistical annotations (R-squared, correlation) to the chart.
        
        Args:
            data: Chart data as list of (x, y) tuples
            
        Returns:
            Dictionary with calculated statistics
        """
        try:
            if not data or len(data) < 2:
                return {}
            
            # Extract x and y values
            x_values = [float(point[0]) for point in data]
            y_values = [float(point[1]) for point in data]
            
            # Calculate statistics
            r_squared = self.stats_engine.calculate_r_squared(x_values, y_values)
            correlation_data = {'x': x_values, 'y': y_values}
            correlations = self.stats_engine.calculate_correlation(correlation_data)
            correlation = correlations.get(('x', 'y'), 0.0)
            
            # Calculate additional statistics
            y_summary = self.stats_engine.calculate_statistical_summary(y_values)
            
            stats = {
                'r_squared': r_squared,
                'correlation': correlation,
                'mean': y_summary.get('mean', 0),
                'std_dev': y_summary.get('std_dev', 0),
                'count': len(data)
            }
            
            # Update chart title with R-squared if significant
            if r_squared > 0.1:  # Only show if R-squared is meaningful
                current_title = self.chart.title()
                new_title = f"{current_title} (R² = {r_squared:.3f})"
                self.chart.setTitle(new_title)
            
            return stats
            
        except Exception as e:
            print(f"Warning: Error adding statistical annotations: {e}")
            return {}
    
    def add_outlier_highlighting(self, data: List[Tuple], method: str = 'iqr'):
        """Highlight outliers in the chart data.
        
        Args:
            data: Chart data as list of (x, y) tuples (x can be numeric or string)
            method: Outlier detection method ('iqr' or 'zscore')
        """
        try:
            if not data or len(data) < 4:
                return
            
            # Extract y values and original data for outlier detection
            y_values = []
            valid_data_points = []
            
            for i, (x_val, y_val) in enumerate(data):
                try:
                    y_values.append(float(y_val))
                    valid_data_points.append((i, x_val, y_val))
                except (ValueError, TypeError):
                    print(f"Warning: Skipping invalid Y value for outlier detection: {y_val}")
                    continue
            
            if len(y_values) < 4:
                print("Warning: Not enough valid data points for outlier detection")
                return
            
            outlier_indices = self.stats_engine.detect_outliers(y_values, method)
            
            if not outlier_indices:
                return
            
            # Create scatter series for outliers
            outlier_series = QScatterSeries()
            outlier_series.setName("Outliers")
            
            # Add outlier points
            for outlier_idx in outlier_indices:
                if outlier_idx < len(valid_data_points):
                    original_idx, x_val, y_val = valid_data_points[outlier_idx]
                    
                    # Use appropriate X coordinate for chart positioning
                    if isinstance(x_val, str):
                        chart_x = float(original_idx)
                    else:
                        chart_x = float(x_val)
                    
                    outlier_series.append(chart_x, float(y_val))
            
            # Style outliers
            current_theme = self.style_manager.get_theme()
            outlier_color = QtGui.QColor(current_theme.colors.get('error', '#BF616A'))
            outlier_series.setColor(outlier_color)
            outlier_series.setMarkerSize(8)
            outlier_series.setMarkerShape(QScatterSeries.MarkerShapeCircle)
            
            self.chart.addSeries(outlier_series)
            
            # Attach to existing axes
            for axis in self.chart.axes():
                outlier_series.attachAxis(axis)
                
        except Exception as e:
            print(f"Warning: Error highlighting outliers: {e}")
    
    def get_chart_statistics(self, data: List[Tuple]) -> Dict[str, any]:
        """Get comprehensive statistics for the current chart data.
        
        Args:
            data: Chart data as list of (x, y) tuples
            
        Returns:
            Dictionary with comprehensive statistics
        """
        try:
            if not data:
                return {}
            
            # Extract values
            x_values = [float(point[0]) for point in data]
            y_values = [float(point[1]) for point in data]
            
            # Calculate comprehensive statistics
            stats = {
                'data_points': len(data),
                'x_stats': self.stats_engine.calculate_statistical_summary(x_values),
                'y_stats': self.stats_engine.calculate_statistical_summary(y_values),
                'r_squared': self.stats_engine.calculate_r_squared(x_values, y_values),
                'correlation': self.stats_engine.calculate_correlation({'x': x_values, 'y': y_values}).get(('x', 'y'), 0.0),
                'outliers_iqr': len(self.stats_engine.detect_outliers(y_values, 'iqr')),
                'outliers_zscore': len(self.stats_engine.detect_outliers(y_values, 'zscore'))
            }
            
            return stats
            
        except Exception as e:
            print(f"Warning: Error calculating chart statistics: {e}")
            return {}

    def _setup_hover_tooltips(self, data, x_variable, y_variables):
        """Set up hover tooltips with chart data and metadata.
        
        Args:
            data: Raw chart data from the data manager
            x_variable: Tuple of (x_variable_name, x_variable_type)
            y_variables: List of tuples [(y_variable_name, y_variable_type), ...]
        """
        try:
            if not data or not x_variable or not y_variables:
                return
            
            # Convert data to format expected by interaction manager
            chart_data = []
            for row in data:
                if len(row) >= 2:
                    x_val = row[0]
                    y_val = row[1]  # Use first Y variable for tooltips
                    if x_val is not None and y_val is not None:
                        chart_data.append((x_val, y_val))
            
            if not chart_data:
                return
            
            # Prepare X variable metadata
            x_var_name, x_var_type = x_variable
            x_variable_info = {
                'name': x_var_name,
                'type': x_var_type,
                'unit': self._get_variable_unit(x_var_name)
            }
            
            # Prepare Y variable metadata (use first Y variable)
            y_var_name, y_var_type = y_variables[0]
            y_variable_info = {
                'name': y_var_name,
                'type': y_var_type,
                'unit': self._get_variable_unit(y_var_name)
            }
            
            # Calculate comprehensive statistics for tooltip context
            statistics = self.get_chart_statistics(chart_data)
            
            # Flatten statistics for easier access in tooltips
            flattened_stats = {}
            if 'y_stats' in statistics:
                y_stats = statistics['y_stats']
                flattened_stats.update({
                    'mean': y_stats.get('mean'),
                    'std_dev': y_stats.get('std_dev'),
                    'median': y_stats.get('median'),
                    'min': y_stats.get('min'),
                    'max': y_stats.get('max')
                })
            
            flattened_stats.update({
                'r_squared': statistics.get('r_squared'),
                'correlation': statistics.get('correlation'),
                'data_points': statistics.get('data_points')
            })
            
            # Set up hover tooltips in the interaction manager
            self.interaction_manager.set_chart_data(
                data=chart_data,
                x_variable_info=x_variable_info,
                y_variable_info=y_variable_info,
                statistics=flattened_stats
            )
            
        except Exception as e:
            print(f"Warning: Error setting up hover tooltips: {e}")
    
    def _get_variable_unit(self, variable_name: str) -> str:
        """Get the unit type for a variable based on its name.
        
        Args:
            variable_name: Name of the variable
            
        Returns:
            Unit type string ('currency', 'percent', 'hours', 'time', etc.)
        """
        variable_name_lower = variable_name.lower()
        
        # Financial variables
        if any(keyword in variable_name_lower for keyword in ['earnings', 'money', 'revenue', 'profit', 'income', 'cost']):
            return 'currency'
        
        # Percentage variables
        elif any(keyword in variable_name_lower for keyword in ['rate', 'percent', '%', 'ratio']):
            return 'percent'
        
        # Time duration variables
        elif any(keyword in variable_name_lower for keyword in ['duration', 'time', 'hours', 'minutes']):
            return 'hours'
        
        # Time of day variables
        elif any(keyword in variable_name_lower for keyword in ['claim_time', 'start_time', 'end_time']):
            return 'time'
        
        # Default to numeric
        else:
            return 'numeric' 