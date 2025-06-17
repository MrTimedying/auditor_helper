from PySide6.QtCharts import QChart, QChartView, QLineSeries, QBarSeries, QBarSet, QScatterSeries, QPieSeries, QPieSlice, QValueAxis, QBarCategoryAxis
from PySide6 import QtCore, QtGui
from enum import Enum
from typing import List, Tuple, Dict, Any, Optional
import math

# Import from dedicated modules
from .chart_validation import ValidationIssue, ChartValidationEngine
from .chart_styling import ChartStyleManager, ResponsiveChartManager
from .statistical_analysis import StatisticalAnalysis
from .chart_interaction_manager import ChartInteractionManager
from .chart_animations import ChartAnimationManager
from .heatmap_widget import QtHeatmapWidget

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
        
        # NEW: Animation manager for smooth transitions and effects
        self.animation_manager = ChartAnimationManager(self.chart_view)
        
        # Toggle flags set by UI
        self.show_trend_line = False
        self.enable_animations = True  # Enable animations by default
        
        # Initialize with professional theme
        self.style_manager.set_theme("professional")
        
        # Configure advanced styling features
        self._setup_advanced_chart_styling()
        
    def set_chart_theme(self, theme_name: str):
        """Set the chart theme for styling"""
        self.style_manager.set_theme(theme_name)
        
    def get_available_themes(self) -> List[str]:
        """Get list of available chart themes"""
        return self.style_manager.get_available_themes()
    
    def _setup_advanced_chart_styling(self):
        """Configure advanced chart styling features"""
        try:
            # Enable chart animations by default
            if self.enable_animations:
                self.animation_manager.enable_all_animations(True)
            
            # Apply initial chart styling
            self._apply_final_chart_styling()
            
        except Exception as e:
            print(f"Warning: Failed to setup advanced chart styling: {e}")
    
    def set_animation_enabled(self, enabled: bool):
        """Enable or disable chart animations"""
        self.enable_animations = enabled
        self.animation_manager.enable_all_animations(enabled)
    
    def apply_modern_chart_styling(self, series, variable_name: str, series_index: int = 0):
        """Apply modern styling with gradients, shadows, and effects"""
        try:
            current_theme = self.style_manager.get_theme()
            
            # Apply Qt series styling with gradients
            style_config = self.style_manager.apply_qt_series_styling(series, variable_name, series_index)
            
            # Add shadow effects if theme supports it
            if current_theme.layout.get("shadow_effects", False):
                shadow_effect = self.style_manager.get_qt_shadow_effect()
                if shadow_effect and hasattr(series, 'setGraphicsEffect'):
                    series.setGraphicsEffect(shadow_effect)
            
            # Add glow effects for dark theme
            if current_theme.name == "Dark Mode" and current_theme.layout.get("glow_effects", False):
                # Add subtle glow effect for dark theme
                from PySide6.QtWidgets import QGraphicsDropShadowEffect
                glow_effect = QGraphicsDropShadowEffect()
                glow_effect.setBlurRadius(12)
                glow_effect.setColor(QtGui.QColor(64, 255, 218, 80))  # Cyan glow
                glow_effect.setOffset(0, 0)
                if hasattr(series, 'setGraphicsEffect'):
                    series.setGraphicsEffect(glow_effect)
            
            return style_config
            
        except Exception as e:
            print(f"Warning: Failed to apply modern chart styling: {e}")
            return {}

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
            elif chart_type == "Box Plot":
                self.create_box_plot(data, x_variable, y_variables)
            elif chart_type == "Heatmap":
                self.create_heatmap(data, x_variable, y_variables)
            else:
                # Fallback to bar chart for unsupported types
                print(f"Warning: Chart type '{chart_type}' not fully implemented, using bar chart")
                self.create_bar_chart(data, x_variable, y_variables)
            
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
            elif issue.severity == ValidationIssue.Severity.INFO:
                # Skip outlier detection info messages to avoid popups
                if "outliers detected" not in issue.message.lower():
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
        """Create line chart with enhanced modern styling"""
        try:
            x_var_name, x_var_type = x_variable
            
            # Get colors for all Y variables using new styling system
            y_var_names = [y[0] for y in y_variables]
            
            # Create series for each Y variable
            for i, (y_var_name, y_var_type) in enumerate(y_variables):
                series = QLineSeries()
                series.setName(y_var_name)
                
                # NEW: Apply modern Qt styling with gradients, shadows, and enhanced effects
                style_config = self.apply_modern_chart_styling(series, y_var_name, i)
                
                # Get color for both styling and trend line (always define color)
                color = self.style_manager.get_semantic_color(y_var_name)
                
                # Additional enhanced styling for line charts
                current_theme = self.style_manager.get_theme()
                if current_theme.layout.get("use_gradients", False):
                    # Use gradient colors for enhanced visual appeal
                    if "gradient" in style_config:
                        gradient_color = QtGui.QColor(style_config["gradient"][0])
                        series_pen = QtGui.QPen(gradient_color)
                    else:
                        series_pen = QtGui.QPen(QtGui.QColor(color))
                else:
                    # Fallback to semantic colors
                    series_pen = QtGui.QPen(QtGui.QColor(color))
                
                # Enhanced pen styling
                series_pen.setWidth(style_config.get("line_width", 3))
                if current_theme.layout.get("rounded_corners", False):
                    series_pen.setCapStyle(QtCore.Qt.RoundCap)
                    series_pen.setJoinStyle(QtCore.Qt.RoundJoin)
                
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
            
            # Add entrance animations if enabled
            if self.enable_animations:
                self.animation_manager.animate_chart_entrance(stagger_delay=150)
            
            # Set up hover tooltips with chart data and metadata
            self._setup_hover_tooltips(data, x_variable, y_variables)
            
        except Exception as e:
            raise Exception(f"Failed to create line chart: {str(e)}")
    
    def create_bar_chart(self, data, x_variable, y_variables):
        """Create bar chart with enhanced modern styling"""
        try:
            x_var_name, x_var_type = x_variable
            
            # Create bar series
            series = QBarSeries()
            
            # Get colors for all Y variables using new styling system
            y_var_names = [y[0] for y in y_variables]
            
            # Create bar sets for each Y variable
            for i, (y_var_name, y_var_type) in enumerate(y_variables):
                bar_set = QBarSet(y_var_name)
                
                # NEW: Apply modern styling with gradients
                current_theme = self.style_manager.get_theme()
                
                if current_theme.layout.get("use_gradients", False):
                    # Use gradient brushes for bars
                    gradient_brush = self.style_manager.get_qt_gradient_brush(
                        gradient_type="primary" if i == 0 else "secondary" if i == 1 else "accent",
                        direction="vertical"
                    )
                    bar_set.setBrush(gradient_brush)
                    
                    # Set border color to complement gradient
                    gradient_colors = current_theme.colors.get("gradients", {})
                    if "primary" in gradient_colors:
                        border_color = QtGui.QColor(gradient_colors["primary"][0])
                    else:
                        border_color = QtGui.QColor(self.style_manager.get_semantic_color(y_var_name))
                    bar_set.setBorderColor(border_color)
                else:
                    # Fallback to semantic colors with enhanced styling
                    color = self.style_manager.get_semantic_color(y_var_name)
                    bar_set.setColor(QtGui.QColor(color))
                
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
            
            # Add entrance animations if enabled
            if self.enable_animations:
                self.animation_manager.animate_chart_entrance(stagger_delay=100)
            
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
            
            # Apply modern styling with enhanced effects
            style_config = self.apply_modern_chart_styling(series, y_var_name, 0)
            
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
            
            # Add entrance animations if enabled
            if self.enable_animations:
                self.animation_manager.animate_chart_entrance(stagger_delay=50)
            
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
            
            # Get modern colors for pie slices with enhanced styling
            x_categories = [str(row[0]) for row in data]
            current_theme = self.style_manager.get_theme()
            
            for i, row in enumerate(data):
                try:
                    label = str(row[0]) if row[0] is not None else f"Category {i+1}"  # X variable as label
                    value = float(row[1]) if len(row) > 1 and row[1] is not None else 0  # First Y variable as value
                    
                    # Skip zero or negative values for pie charts
                    if value <= 0:
                        continue
                    
                    slice = QPieSlice(label, value)
                    
                    # NEW: Enhanced pie slice styling with gradients
                    if current_theme.layout.get("use_gradients", False):
                        # Use gradient brush for pie slices
                        gradient_types = ["primary", "secondary", "accent"]
                        gradient_type = gradient_types[i % len(gradient_types)]
                        gradient_brush = self.style_manager.get_qt_gradient_brush(
                            gradient_type=gradient_type, 
                            direction="radial"
                        )
                        slice.setBrush(gradient_brush)
                        
                        # Enhanced border styling
                        slice.setBorderWidth(2)
                        border_color = current_theme.colors.get("text_light", "#4C566A")
                        slice.setBorderColor(QtGui.QColor(border_color))
                    else:
                        # Fallback to semantic colors with modern palette
                        color = self.style_manager.get_semantic_color(label)
                        slice.setColor(QtGui.QColor(color))
                        slice.setBorderWidth(1)
                    
                    # Enhanced label styling
                    slice.setLabelVisible(True)
                    slice.setLabelColor(QtGui.QColor(current_theme.colors.get("text", "#2E3440")))
                    series.append(slice)
                    
                except Exception as e:
                    print(f"Warning: Skipped pie slice at row {i}: {e}")
                    continue
            
            if series.count() == 0:
                raise Exception("No valid data for pie chart (all values are zero or invalid)")
            
            self.chart.addSeries(series)
            
            # Apply final styling after series is set up
            self._apply_final_chart_styling()
            
            # Add entrance animations if enabled
            if self.enable_animations:
                self.animation_manager.animate_chart_entrance(stagger_delay=75)
            
            # Set up hover tooltips with chart data and metadata
            self._setup_hover_tooltips(data, x_variable, y_variables)
            
        except Exception as e:
            raise Exception(f"Failed to create pie chart: {str(e)}")

    def create_box_plot(self, data, x_variable, y_variables):
        """Create box plot using Qt Charts with custom components"""
        try:
            from .statistical_analysis import BoxPlotStats
            from PySide6.QtCharts import QBarSeries, QBarSet, QLineSeries, QScatterSeries
            from PySide6 import QtGui, QtCore
            
            x_var_name, x_var_type = x_variable
            
            if len(y_variables) != 1:
                raise Exception("Box plots require exactly one Y variable")
                
            y_var_name, y_var_type = y_variables[0]
            
            # Calculate box plot statistics
            box_stats = self.stats_engine.calculate_box_plot_stats(data, y_variables[0])
            if not box_stats:
                raise Exception("Insufficient data for box plot (minimum 5 data points required)")
            
            # Create the main box using QBarSeries
            box_series = QBarSeries()
            box_series.setName(f"{y_var_name} Distribution")
            
            # Create bar set for the box (Q1 to Q3)
            box_height = box_stats.q3 - box_stats.q1  # IQR
            box_set = QBarSet("Box")
            box_set.append(box_height)
            
            # Apply modern styling to the box
            current_theme = self.style_manager.get_theme()
            color = self.style_manager.get_semantic_color(y_var_name)
            
            if current_theme.layout.get("use_gradients", False):
                # Use gradient brush for the box
                gradient_brush = self.style_manager.get_qt_gradient_brush(
                    gradient_type="primary",
                    direction="vertical"
                )
                box_set.setBrush(gradient_brush)
                border_color = QtGui.QColor(color)
            else:
                # Use solid color with transparency
                box_color = QtGui.QColor(color)
                box_color.setAlpha(180)  # Semi-transparent
                box_set.setColor(box_color)
                border_color = QtGui.QColor(color)
            
            box_set.setBorderColor(border_color)
            box_series.append(box_set)
            self.chart.addSeries(box_series)
            
            # Create whiskers using QLineSeries
            whisker_color = QtGui.QColor(color).darker(120)
            
            # Lower whisker (from Q1 to lower_whisker)
            if box_stats.lower_whisker < box_stats.q1:
                lower_whisker_series = QLineSeries()
                lower_whisker_series.setName("Lower Whisker")
                lower_whisker_series.append(0, box_stats.lower_whisker)
                lower_whisker_series.append(0, box_stats.q1)
                
                whisker_pen = QtGui.QPen(whisker_color)
                whisker_pen.setWidth(2)
                lower_whisker_series.setPen(whisker_pen)
                self.chart.addSeries(lower_whisker_series)
            
            # Upper whisker (from Q3 to upper_whisker)
            if box_stats.upper_whisker > box_stats.q3:
                upper_whisker_series = QLineSeries()
                upper_whisker_series.setName("Upper Whisker")
                upper_whisker_series.append(0, box_stats.q3)
                upper_whisker_series.append(0, box_stats.upper_whisker)
                
                whisker_pen = QtGui.QPen(whisker_color)
                whisker_pen.setWidth(2)
                upper_whisker_series.setPen(whisker_pen)
                self.chart.addSeries(upper_whisker_series)
            
            # Create whisker caps (horizontal lines at whisker ends)
            cap_width = 0.1  # Width of the caps
            
            # Lower cap
            if box_stats.lower_whisker < box_stats.q1:
                lower_cap_series = QLineSeries()
                lower_cap_series.setName("Lower Cap")
                lower_cap_series.append(-cap_width, box_stats.lower_whisker)
                lower_cap_series.append(cap_width, box_stats.lower_whisker)
                
                cap_pen = QtGui.QPen(whisker_color)
                cap_pen.setWidth(2)
                lower_cap_series.setPen(cap_pen)
                self.chart.addSeries(lower_cap_series)
            
            # Upper cap
            if box_stats.upper_whisker > box_stats.q3:
                upper_cap_series = QLineSeries()
                upper_cap_series.setName("Upper Cap")
                upper_cap_series.append(-cap_width, box_stats.upper_whisker)
                upper_cap_series.append(cap_width, box_stats.upper_whisker)
                
                cap_pen = QtGui.QPen(whisker_color)
                cap_pen.setWidth(2)
                upper_cap_series.setPen(cap_pen)
                self.chart.addSeries(upper_cap_series)
            
            # Create median line across the box
            median_series = QLineSeries()
            median_series.setName(f"Median ({box_stats.median:.2f})")
            median_series.append(-0.4, box_stats.median)
            median_series.append(0.4, box_stats.median)
            
            median_pen = QtGui.QPen(QtGui.QColor("#2E3440"))  # Dark color for visibility
            median_pen.setWidth(3)
            median_series.setPen(median_pen)
            self.chart.addSeries(median_series)
            
            # Add outliers as scatter points
            if box_stats.outliers:
                outlier_series = QScatterSeries()
                outlier_series.setName(f"Outliers ({len(box_stats.outliers)})")
                
                for outlier_value in box_stats.outliers:
                    # Add some random horizontal jitter for visibility
                    import random
                    jitter = random.uniform(-0.1, 0.1)
                    outlier_series.append(jitter, outlier_value)
                
                # Style outliers
                outlier_color = QtGui.QColor(current_theme.colors.get('error', '#BF616A'))
                outlier_series.setColor(outlier_color)
                outlier_series.setMarkerSize(8)
                outlier_series.setMarkerShape(QScatterSeries.MarkerShapeCircle)
                
                self.chart.addSeries(outlier_series)
            
            # Create custom axes for box plot
            self._create_box_plot_axes(box_stats, x_variable, y_variables)
            
            # Apply final styling
            self._apply_final_chart_styling()
            
            # Add entrance animations if enabled
            if self.enable_animations:
                self.animation_manager.animate_chart_entrance(stagger_delay=200)
            
            # Set up hover tooltips with box plot statistics
            self._setup_box_plot_tooltips(box_stats, x_variable, y_variables)
            
        except Exception as e:
            raise Exception(f"Failed to create box plot: {str(e)}")
    
    def _create_box_plot_axes(self, box_stats, x_variable, y_variables):
        """Create specialized axes for box plot"""
        from PySide6.QtCharts import QBarCategoryAxis, QValueAxis
        from PySide6 import QtCore
        
        x_var_name, x_var_type = x_variable
        y_var_name, y_var_type = y_variables[0]
        
        # Create categorical X axis (single category for the box)
        x_axis = QBarCategoryAxis()
        x_axis.append(y_var_name)  # Use the Y variable name as the single category
        
        # Create Y axis with range based on box plot statistics
        y_axis = QValueAxis()
        
        # Set Y axis range with some padding
        data_range = box_stats.max_value - box_stats.min_value
        padding = data_range * 0.1  # 10% padding
        y_min = box_stats.min_value - padding
        y_max = box_stats.max_value + padding
        
        y_axis.setRange(y_min, y_max)
        y_axis.setTitleText(y_var_name)
        
        # Apply axis styling
        current_theme = self.style_manager.get_theme()
        axis_color = QtGui.QColor(current_theme.colors.get('text', '#2E3440'))
        
        x_axis.setLabelsColor(axis_color)
        x_axis.setTitleText("Distribution")
        
        y_axis.setLabelsColor(axis_color)
        
        # Add axes to chart
        self.chart.addAxis(x_axis, QtCore.Qt.AlignBottom)
        self.chart.addAxis(y_axis, QtCore.Qt.AlignLeft)
        
        # Attach all series to axes
        for series in self.chart.series():
            series.attachAxis(x_axis)
            series.attachAxis(y_axis)
    
    def _setup_box_plot_tooltips(self, box_stats, x_variable, y_variables):
        """Set up comprehensive tooltips for box plot"""
        try:
            y_var_name, y_var_type = y_variables[0]
            
            # Create comprehensive statistics for tooltips
            statistics = {
                'median': box_stats.median,
                'q1': box_stats.q1,
                'q3': box_stats.q3,
                'iqr': box_stats.iqr,
                'lower_whisker': box_stats.lower_whisker,
                'upper_whisker': box_stats.upper_whisker,
                'outliers_count': len(box_stats.outliers),
                'sample_size': box_stats.sample_size,
                'min_value': box_stats.min_value,
                'max_value': box_stats.max_value
            }
            
            # Prepare variable info
            y_variable_info = {
                'name': y_var_name,
                'type': y_var_type,
                'unit': self._get_variable_unit(y_var_name)
            }
            
            # Set up enhanced tooltips in the interaction manager
            self.interaction_manager.set_box_plot_data(
                box_stats=box_stats,
                variable_info=y_variable_info,
                statistics=statistics
            )
            
        except Exception as e:
            print(f"Warning: Error setting up box plot tooltips: {e}")
    
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
        """Apply modern chart-level styling with gradients and enhanced backgrounds"""
        try:
            current_theme = self.style_manager.get_theme()
            
            # NEW: Use enhanced background with gradients
            background_brush = self.style_manager.get_chart_background_brush()
            self.chart.setBackgroundBrush(background_brush)
            
            # Enhanced plot area background
            surface_color = current_theme.colors.get('surface', current_theme.colors.get('background', '#FFFFFF'))
            if current_theme.layout.get("use_gradients", False) and current_theme.name != "Minimal":
                # Subtle gradient for plot area
                surface_brush = self.style_manager.get_qt_gradient_brush(gradient_type="secondary", direction="diagonal")
                surface_brush.setColor(QtGui.QColor(surface_color))
                self.chart.setPlotAreaBackgroundBrush(surface_brush)
            else:
                self.chart.setPlotAreaBackgroundBrush(QtGui.QBrush(QtGui.QColor(surface_color)))
            
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
            
            # Extract values with proper handling for string X values (like dates)
            x_values = []
            y_values = []
            
            for i, point in enumerate(data):
                if len(point) >= 2:
                    x_val, y_val = point[0], point[1]
                    
                    # Handle X values: use index for strings (like dates), float for numbers
                    try:
                        if isinstance(x_val, str):
                            x_values.append(float(i))  # Use index for string-based X values
                        else:
                            x_values.append(float(x_val))
                    except (ValueError, TypeError):
                        x_values.append(float(i))  # Fallback to index
                    
                    # Handle Y values: convert to float
                    try:
                        y_values.append(float(y_val))
                    except (ValueError, TypeError):
                        continue  # Skip invalid Y values
            
            if not x_values or not y_values:
                return {}
            
            # Calculate comprehensive statistics
            stats = {
                'data_points': len(y_values),  # Use valid Y values count
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

    def create_heatmap(self, data, x_variable, y_variables):
        """Create correlation heatmap for multiple variables"""
        try:
            print(f"🎨 Creating heatmap for {len(y_variables)} variables...")
            
            # Clear existing chart
            self.clear_chart()
            
            # Validate minimum requirements
            if len(y_variables) < 2:
                self._show_chart_error("Insufficient Variables", 
                                     ["Heatmap requires at least 2 variables for correlation analysis"],
                                     ["Select at least 2 quantitative Y variables"])
                return
            
            if len(data) < 10:
                self._show_chart_error("Insufficient Data", 
                                     [f"Only {len(data)} data points available. Heatmap needs at least 10 for meaningful correlation"],
                                     ["Select a larger time period", "Add more data to your analysis"])
                return
            
            # Prepare data for correlation analysis
            correlation_data = self._prepare_heatmap_data(data, y_variables)
            
            if not correlation_data:
                self._show_chart_error("No Valid Data", 
                                     ["No valid numeric data found for correlation analysis"],
                                     ["Ensure selected variables contain numeric values", "Check for missing or invalid data"])
                return
            
            # Calculate correlation matrix
            correlation_matrix = self.stats_engine.calculate_correlation_matrix(
                correlation_data, 
                correlation_type='pearson',
                min_periods=5
            )
            
            # Replace chart view with heatmap widget
            self._setup_heatmap_widget(correlation_matrix)
            
            # Apply styling and animations
            self._apply_heatmap_styling()
            
            # Set up tooltips and interactions
            self._setup_heatmap_interactions(correlation_matrix, y_variables)
            
            # Apply chart title
            self._set_heatmap_title(len(y_variables), correlation_matrix.sample_size)
            
            # Enable animations
            if self.enable_animations:
                self.animation_manager.animate_heatmap_entrance()
            
            print(f"✅ Heatmap created successfully with {len(y_variables)} variables")
            
        except Exception as e:
            print(f"❌ Error creating heatmap: {e}")
            self._show_chart_error("Heatmap Creation Failed", 
                                 [f"Error: {str(e)}"],
                                 ["Try selecting different variables", "Check your data selection"])
    
    def _prepare_heatmap_data(self, data, y_variables) -> Dict[str, List[float]]:
        """Prepare data for correlation matrix calculation"""
        correlation_data = {}
        
        for i, (y_var_name, y_var_type) in enumerate(y_variables):
            values = []
            
            for row in data:
                # Y variables start from index 1 (index 0 is X variable)
                value_index = i + 1
                if len(row) > value_index:
                    try:
                        value = float(row[value_index])
                        if not math.isnan(value):
                            values.append(value)
                        else:
                            values.append(None)  # Keep None for missing data
                    except (ValueError, TypeError):
                        values.append(None)  # Invalid data becomes None
                else:
                    values.append(None)
            
            correlation_data[y_var_name] = values
        
        # Filter out variables with too few valid values
        min_valid_ratio = 0.5  # At least 50% valid data
        min_valid_count = max(5, len(data) * min_valid_ratio)
        
        filtered_data = {}
        for var_name, values in correlation_data.items():
            valid_count = sum(1 for v in values if v is not None)
            if valid_count >= min_valid_count:
                filtered_data[var_name] = values
            else:
                print(f"Warning: Variable '{var_name}' excluded from heatmap (only {valid_count} valid values)")
        
        return filtered_data
    
    def _setup_heatmap_widget(self, correlation_matrix):
        """Replace chart view with custom heatmap widget"""
        # Store reference to original chart view
        if not hasattr(self, '_original_chart_view'):
            self._original_chart_view = self.chart_view
        
        # Create heatmap widget
        self.heatmap_widget = QtHeatmapWidget()
        
        # Replace the chart view in its parent layout
        parent_widget = self.chart_view.parent()
        if parent_widget and hasattr(parent_widget, 'layout'):
            layout = parent_widget.layout()
            if layout:
                # Find and replace chart view
                for i in range(layout.count()):
                    item = layout.itemAt(i)
                    if item and item.widget() == self.chart_view:
                        layout.removeWidget(self.chart_view)
                        layout.insertWidget(i, self.heatmap_widget)
                        break
                else:
                    # If not found in layout, add directly
                    layout.addWidget(self.heatmap_widget)
            else:
                print("Warning: Could not find layout to replace chart view")
        
        # Hide original chart view
        self.chart_view.hide()
        
        # Create heatmap visualization
        self.heatmap_widget.create_heatmap(correlation_matrix)
        self.heatmap_widget.show()
    
    def _apply_heatmap_styling(self):
        """Apply theme styling to heatmap widget"""
        try:
            current_theme = self.style_manager.get_theme()
            
            # Apply theme-based styling to heatmap widget
            if hasattr(self, 'heatmap_widget'):
                # Set background color
                background_color = current_theme.colors.get('background', '#FFFFFF')
                self.heatmap_widget.setStyleSheet(f"""
                    QGraphicsView {{
                        background-color: {background_color};
                        border: none;
                    }}
                """)
                
        except Exception as e:
            print(f"Warning: Error applying heatmap styling: {e}")
    
    def _setup_heatmap_interactions(self, correlation_matrix, y_variables):
        """Set up interactions and tooltips for heatmap"""
        try:
            # Prepare variable info for tooltips
            variable_info = {}
            for y_var_name, y_var_type in y_variables:
                variable_info[y_var_name] = {
                    'name': y_var_name,
                    'type': y_var_type,
                    'unit': self._get_variable_unit(y_var_name)
                }
            
            # Create statistics for interaction manager
            statistics = {
                'correlation_type': correlation_matrix.correlation_type,
                'sample_size': correlation_matrix.sample_size,
                'variable_count': len(correlation_matrix.labels)
            }
            
            # Note: Heatmap interactions are handled internally by the widget
            # This could be extended to integrate with the existing interaction manager
            
        except Exception as e:
            print(f"Warning: Error setting up heatmap interactions: {e}")
    
    def _set_heatmap_title(self, variable_count: int, sample_size: int):
        """Set descriptive title for heatmap"""
        try:
            title = f"Correlation Analysis: {variable_count} Variables"
            if sample_size:
                title += f" (n={sample_size})"
            
            # The title is handled by the heatmap widget itself
            # This method could be extended to set additional titles
            
        except Exception as e:
            print(f"Warning: Error setting heatmap title: {e}")
    
    def restore_chart_view(self):
        """Restore original chart view (useful for switching back from heatmap)"""
        if hasattr(self, '_original_chart_view') and hasattr(self, 'heatmap_widget'):
            try:
                # Hide heatmap widget
                self.heatmap_widget.hide()
                
                # Show original chart view
                self._original_chart_view.show()
                
                # Replace in layout if needed
                parent_widget = self.heatmap_widget.parent()
                if parent_widget and hasattr(parent_widget, 'layout'):
                    layout = parent_widget.layout()
                    if layout:
                        for i in range(layout.count()):
                            item = layout.itemAt(i)
                            if item and item.widget() == self.heatmap_widget:
                                layout.removeWidget(self.heatmap_widget)
                                layout.insertWidget(i, self._original_chart_view)
                                break
                
                # Update references
                self.chart_view = self._original_chart_view
                
            except Exception as e:
                print(f"Warning: Error restoring chart view: {e}")
    
    def export_chart(self, file_path: str, format: str = "png", 
                    width: int = 1920, height: int = 1080, dpi: int = 300,
                    include_legend: bool = True, include_title: bool = True,
                    transparent_background: bool = False, preset: str = None) -> bool:
        """Enhanced chart export with professional quality options
        
        Args:
            file_path: Path to save the exported file
            format: Export format ('png', 'svg', 'pdf', 'jpg')
            width: Image width in pixels
            height: Image height in pixels  
            dpi: Dots per inch for print quality
            include_legend: Whether to include chart legend
            include_title: Whether to include chart title
            transparent_background: Use transparent background (PNG only)
            preset: Predefined export preset ('presentation', 'report', 'web', 'print')
            
        Returns:
            True if export successful, False otherwise
        """
        try:
            # Apply preset if specified
            if preset:
                width, height, dpi, format = self._get_export_preset(preset)
            
            print(f"📤 Exporting chart as {format.upper()} ({width}x{height}, {dpi} DPI)...")
            
            # Temporarily modify chart for export
            original_legend_visible = None
            original_title = None
            
            # Handle legend visibility
            if hasattr(self.chart, 'legend'):
                legend = self.chart.legend()
                if legend:
                    original_legend_visible = legend.isVisible()
                    legend.setVisible(include_legend)
            
            # Handle title visibility
            if not include_title:
                original_title = self.chart.title()
                self.chart.setTitle("")
            
            # Export based on format
            success = False
            if format.lower() == 'svg':
                success = self._export_svg(file_path, width, height)
            elif format.lower() == 'pdf':
                success = self._export_pdf(file_path, width, height, dpi)
            elif format.lower() in ['png', 'jpg', 'jpeg']:
                success = self._export_raster(file_path, format, width, height, dpi, transparent_background)
            else:
                print(f"❌ Unsupported export format: {format}")
                return False
            
            # Restore original chart settings
            if original_legend_visible is not None and hasattr(self.chart, 'legend'):
                legend = self.chart.legend()
                if legend:
                    legend.setVisible(original_legend_visible)
            
            if original_title is not None:
                self.chart.setTitle(original_title)
            
            if success:
                print(f"✅ Chart exported successfully to {file_path}")
            else:
                print(f"❌ Failed to export chart to {file_path}")
                
            return success
            
        except Exception as e:
            print(f"❌ Error exporting chart: {e}")
            return False
    
    def _get_export_preset(self, preset: str) -> Tuple[int, int, int, str]:
        """Get predefined export settings for common use cases"""
        presets = {
            'presentation': (1920, 1080, 150, 'png'),  # HD for presentations
            'report': (1200, 800, 300, 'png'),         # High quality for reports
            'web': (800, 600, 96, 'png'),              # Web optimized
            'print': (2400, 1800, 300, 'png'),        # Print quality
            'poster': (3840, 2160, 300, 'png'),       # 4K for posters
            'slide': (1280, 720, 150, 'png'),         # Standard slide format
            'thumbnail': (400, 300, 96, 'png')        # Small preview
        }
        
        return presets.get(preset.lower(), (1920, 1080, 300, 'png'))
    
    def _export_raster(self, file_path: str, format: str, width: int, height: int, 
                      dpi: int, transparent_background: bool) -> bool:
        """Export chart as raster image (PNG, JPG)"""
        try:
            # Calculate scale factor for high DPI
            scale_factor = dpi / 96.0
            scaled_width = int(width * scale_factor)
            scaled_height = int(height * scale_factor)
            
            # Create high-resolution image
            if transparent_background and format.lower() == 'png':
                image = QtGui.QImage(scaled_width, scaled_height, QtGui.QImage.Format_ARGB32)
                image.fill(QtCore.Qt.transparent)
            else:
                image = QtGui.QImage(scaled_width, scaled_height, QtGui.QImage.Format_RGB32)
                image.fill(QtCore.Qt.white)
            
            # Set image DPI
            image.setDotsPerMeterX(int(dpi * 39.3701))  # Convert DPI to dots per meter
            image.setDotsPerMeterY(int(dpi * 39.3701))
            
            # Create painter and render chart
            painter = QtGui.QPainter(image)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            painter.setRenderHint(QtGui.QPainter.TextAntialiasing)
            painter.setRenderHint(QtGui.QPainter.SmoothPixmapTransform)
            
            # Render chart to image
            if hasattr(self, 'heatmap_widget') and hasattr(self.chart_view, 'heatmap_widget'):
                # Special handling for heatmap
                self.heatmap_widget.scene.render(painter)
            else:
                # Regular Qt Charts
                self.chart_view.render(painter)
            
            painter.end()
            
            # Save image
            return image.save(file_path, format.upper())
            
        except Exception as e:
            print(f"Error in raster export: {e}")
            return False
    
    def _export_svg(self, file_path: str, width: int, height: int) -> bool:
        """Export chart as SVG vector image"""
        try:
            from PySide6.QtSvg import QSvgGenerator
            
            # Create SVG generator
            svg_generator = QSvgGenerator()
            svg_generator.setFileName(file_path)
            svg_generator.setSize(QtCore.QSize(width, height))
            svg_generator.setViewBox(QtCore.QRect(0, 0, width, height))
            svg_generator.setTitle("Chart Export")
            svg_generator.setDescription("Exported from Auditor Helper")
            
            # Render chart to SVG
            painter = QtGui.QPainter(svg_generator)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            
            if hasattr(self, 'heatmap_widget') and hasattr(self.chart_view, 'heatmap_widget'):
                # Special handling for heatmap
                self.heatmap_widget.scene.render(painter)
            else:
                # Regular Qt Charts
                self.chart_view.render(painter)
            
            painter.end()
            return True
            
        except Exception as e:
            print(f"Error in SVG export: {e}")
            return False
    
    def _export_pdf(self, file_path: str, width: int, height: int, dpi: int) -> bool:
        """Export chart as PDF document"""
        try:
            from PySide6.QtPrintSupport import QPdfWriter
            from PySide6.QtGui import QPageLayout, QPageSize
            
            # Create PDF writer
            pdf_writer = QPdfWriter(file_path)
            pdf_writer.setResolution(dpi)
            
            # Set page size based on dimensions
            page_size = QPageSize(QtCore.QSizeF(width * 25.4 / dpi, height * 25.4 / dpi), 
                                 QPageSize.Unit.Millimeter)
            pdf_writer.setPageSize(page_size)
            pdf_writer.setPageMargins(QtCore.QMarginsF(0, 0, 0, 0))
            
            # Render chart to PDF
            painter = QtGui.QPainter(pdf_writer)
            painter.setRenderHint(QtGui.QPainter.Antialiasing)
            
            if hasattr(self, 'heatmap_widget') and hasattr(self.chart_view, 'heatmap_widget'):
                # Special handling for heatmap  
                self.heatmap_widget.scene.render(painter)
            else:
                # Regular Qt Charts
                self.chart_view.render(painter)
            
            painter.end()
            return True
            
        except Exception as e:
            print(f"Error in PDF export: {e}")
            return False
    
    def get_available_export_formats(self) -> List[str]:
        """Get list of supported export formats"""
        return ['PNG', 'JPG', 'SVG', 'PDF']
    
    def get_available_export_presets(self) -> Dict[str, Dict[str, Any]]:
        """Get available export presets with their settings"""
        presets = {
            'presentation': {
                'name': 'Presentation (HD)',
                'description': '1920×1080 at 150 DPI, optimized for presentations',
                'width': 1920, 'height': 1080, 'dpi': 150, 'format': 'PNG'
            },
            'report': {
                'name': 'Report Quality',
                'description': '1200×800 at 300 DPI, high quality for documents',
                'width': 1200, 'height': 800, 'dpi': 300, 'format': 'PNG'
            },
            'web': {
                'name': 'Web Optimized',
                'description': '800×600 at 96 DPI, smaller file size',
                'width': 800, 'height': 600, 'dpi': 96, 'format': 'PNG'
            },
            'print': {
                'name': 'Print Quality',
                'description': '2400×1800 at 300 DPI, publication ready',
                'width': 2400, 'height': 1800, 'dpi': 300, 'format': 'PNG'
            }
        }
        return presets 