from PySide6.QtCharts import QChart, QChartView, QLineSeries, QBarSeries, QBarSet, QScatterSeries, QPieSeries, QPieSlice, QValueAxis, QBarCategoryAxis
from PySide6 import QtCore, QtGui
from enum import Enum
from typing import List, Tuple, Dict, Any, Optional

# Import from dedicated modules
from .chart_validation import ValidationIssue, ChartValidationEngine
from .chart_styling import ChartStyleManager, ResponsiveChartManager

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
                pen = series.pen()
                pen.setWidth(2)  # Slightly thicker for better visibility
                pen.setColor(color)
                series.setPen(pen)
                
                # Add data points with error handling
                for row_idx, row in enumerate(data):
                    try:
                        x_val = row[0]
                        y_val = row[i + 1] if len(row) > i + 1 else 0  # Y values start at index 1
                        
                        # Convert X value for plotting
                        if x_var_type == "categorical":
                            x_plot = float(row_idx)
                        else:
                            try:
                                x_plot = float(x_val) if x_val is not None else float(row_idx)
                            except (ValueError, TypeError):
                                x_plot = float(row_idx)  # Fallback to index
                        
                        # Convert Y value
                        try:
                            y_plot = float(y_val) if y_val is not None else 0
                        except (ValueError, TypeError):
                            y_plot = 0  # Fallback to 0
                        
                        series.append(x_plot, y_plot)
                        
                    except Exception as e:
                        print(f"Warning: Skipped data point at row {row_idx} for variable {y_var_name}: {e}")
                        continue
                
                self.chart.addSeries(series)
            
            # Create axes with error handling
            self._create_axes(data, x_variable, y_variables, "line")
            
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
            
        except Exception as e:
            raise Exception(f"Failed to create pie chart: {str(e)}")
    
    def _create_axes(self, data, x_variable, y_variables, chart_type):
        """Create chart axes with error handling"""
        try:
            x_var_name, x_var_type = x_variable
            
            # Create X axis
            if x_var_type == "categorical":
                categories = [str(row[0]) if row[0] is not None else f"Item {i+1}" for i, row in enumerate(data)]
                axis_x = QBarCategoryAxis()
                axis_x.append(categories)
                axis_x.setTitleText(x_var_name)
            else:
                axis_x = QValueAxis()
                axis_x.setTitleText(x_var_name)
            
            # Style X axis
            axis_x.setTitleBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))
            axis_x.setLabelsBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))
            axis_x.setLinePenColor(QtGui.QColor("#D6D6D6"))
            self.chart.addAxis(axis_x, QtCore.Qt.AlignBottom)
            
            # Create Y axis (skip for pie charts)
            if chart_type != "pie":
                axis_y = QValueAxis()
                if len(y_variables) == 1:
                    axis_y.setTitleText(y_variables[0][0])
                else:
                    axis_y.setTitleText("Values")
                
                # Style Y axis
                axis_y.setTitleBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))
                axis_y.setLabelsBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))
                axis_y.setLinePenColor(QtGui.QColor("#D6D6D6"))
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
                        
        except Exception as e:
            print(f"Warning: Error creating axes: {e}")

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