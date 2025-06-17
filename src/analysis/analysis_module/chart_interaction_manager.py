from PySide6.QtCharts import QChartView, QLineSeries, QBarSeries, QScatterSeries, QPieSeries
from PySide6.QtCore import Qt, QObject, QEvent, QPointF, QRectF
from PySide6.QtWidgets import QToolTip, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QGroupBox, QGridLayout, QListWidget, QListWidgetItem, QGraphicsRectItem
from PySide6.QtGui import QCursor, QFont, QPen, QBrush, QColor
from typing import Optional, Dict, Any, List, Tuple, Set

class BrushSelectionDialog(QDialog):
    """Dialog for analyzing data points within a brush-selected region."""
    
    def __init__(self, region_points: List[Tuple[int, Any, float]], region_bounds: Dict[str, float], 
                 chart_statistics: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Region Analysis")
        self.setModal(True)
        self.resize(600, 450)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title_label = QLabel(f"📊 Analysis of Selected Region ({len(region_points)} points)")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Region bounds
        bounds_group = QGroupBox("Region Boundaries")
        bounds_layout = QGridLayout(bounds_group)
        
        bounds_layout.addWidget(QLabel("X Range:"), 0, 0)
        bounds_layout.addWidget(QLabel(f"{region_bounds['x_min']:.2f} to {region_bounds['x_max']:.2f}"), 0, 1)
        bounds_layout.addWidget(QLabel("Y Range:"), 1, 0)
        bounds_layout.addWidget(QLabel(f"{region_bounds['y_min']:.2f} to {region_bounds['y_max']:.2f}"), 1, 1)
        
        layout.addWidget(bounds_group)
        
        # Region statistics
        stats_group = QGroupBox("Region Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        stats_text = QTextEdit()
        stats_text.setReadOnly(True)
        stats_text.setMaximumHeight(120)
        
        y_values = [point[2] for point in region_points]
        region_stats = self._calculate_region_statistics(y_values, chart_statistics)
        stats_text.setPlainText(region_stats)
        
        stats_layout.addWidget(stats_text)
        layout.addWidget(stats_group)
        
        # Data points in region
        points_group = QGroupBox(f"Data Points in Region ({len(region_points)})")
        points_layout = QVBoxLayout(points_group)
        
        points_list = QListWidget()
        points_list.setMaximumHeight(100)
        
        for i, (index, x_val, y_val) in enumerate(region_points[:10]):  # Show first 10
            item_text = f"Point {index + 1}: {x_val} → {y_val:.2f}"
            item = QListWidgetItem(item_text)
            points_list.addItem(item)
        
        if len(region_points) > 10:
            item = QListWidgetItem(f"... and {len(region_points) - 10} more points")
            points_list.addItem(item)
        
        points_layout.addWidget(points_list)
        layout.addWidget(points_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def _calculate_region_statistics(self, y_values: List[float], chart_statistics: Dict[str, Any]) -> str:
        """Calculate statistics for the region data points."""
        if not y_values:
            return "No data points in region."
        
        # Basic statistics
        n = len(y_values)
        mean = sum(y_values) / n
        sorted_values = sorted(y_values)
        median = sorted_values[n // 2] if n % 2 == 1 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        min_val = min(y_values)
        max_val = max(y_values)
        range_val = max_val - min_val
        
        # Standard deviation
        variance = sum((y - mean) ** 2 for y in y_values) / n
        std_dev = variance ** 0.5
        
        stats_lines = [
            f"Count: {n} points",
            f"Mean: {mean:.2f}",
            f"Median: {median:.2f}",
            f"Standard Deviation: {std_dev:.2f}",
            f"Range: {range_val:.2f} (from {min_val:.2f} to {max_val:.2f})"
        ]
        
        # Compare with overall dataset
        if chart_statistics:
            overall_mean = chart_statistics.get('mean')
            overall_std = chart_statistics.get('std_dev')
            total_points = chart_statistics.get('data_points', 0)
            
            if overall_mean is not None:
                diff_from_overall = mean - overall_mean
                stats_lines.append("")
                stats_lines.append("Comparison with Overall Dataset:")
                stats_lines.append(f"Region mean vs. overall mean: {diff_from_overall:+.2f}")
                stats_lines.append(f"Region coverage: {(n / total_points * 100):.1f}% of total data" if total_points > 0 else "")
                
                if overall_std is not None and overall_std > 0:
                    z_score = diff_from_overall / overall_std
                    stats_lines.append(f"Region mean Z-score: {z_score:.2f}")
        
        return "\n".join(stats_lines)

class DataPointSelectionDialog(QDialog):
    """Dialog for analyzing selected data points with comparative statistics."""
    
    def __init__(self, selected_points: List[Tuple[int, Any, float]], chart_statistics: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Selected Data Points Analysis")
        self.setModal(True)
        self.resize(600, 500)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title_label = QLabel(f"📊 Analysis of {len(selected_points)} Selected Data Points")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Selected Points List
        points_group = QGroupBox("Selected Data Points")
        points_layout = QVBoxLayout(points_group)
        
        points_list = QListWidget()
        points_list.setMaximumHeight(120)
        
        for i, (index, x_val, y_val) in enumerate(selected_points):
            item_text = f"Point {index + 1}: {x_val} → {y_val:.2f}"
            item = QListWidgetItem(item_text)
            points_list.addItem(item)
        
        points_layout.addWidget(points_list)
        layout.addWidget(points_group)
        
        # Selection Statistics
        stats_group = QGroupBox("Selection Statistics")
        stats_layout = QVBoxLayout(stats_group)
        
        stats_text = QTextEdit()
        stats_text.setReadOnly(True)
        stats_text.setMaximumHeight(150)
        
        # Calculate selection statistics
        y_values = [point[2] for point in selected_points]
        selection_stats = self._calculate_selection_statistics(y_values, chart_statistics)
        stats_text.setPlainText(selection_stats)
        
        stats_layout.addWidget(stats_text)
        layout.addWidget(stats_group)
        
        # Outlier Analysis
        outlier_group = QGroupBox("Outlier Analysis")
        outlier_layout = QVBoxLayout(outlier_group)
        
        outlier_text = QTextEdit()
        outlier_text.setReadOnly(True)
        outlier_text.setMaximumHeight(100)
        
        outlier_analysis = self._analyze_outliers_in_selection(selected_points, chart_statistics)
        outlier_text.setPlainText(outlier_analysis)
        
        outlier_layout.addWidget(outlier_text)
        layout.addWidget(outlier_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
    
    def _calculate_selection_statistics(self, y_values: List[float], chart_statistics: Dict[str, Any]) -> str:
        """Calculate statistics for the selected data points."""
        if not y_values:
            return "No data points selected."
        
        # Basic statistics
        n = len(y_values)
        mean = sum(y_values) / n
        sorted_values = sorted(y_values)
        median = sorted_values[n // 2] if n % 2 == 1 else (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        min_val = min(y_values)
        max_val = max(y_values)
        range_val = max_val - min_val
        
        # Standard deviation
        variance = sum((y - mean) ** 2 for y in y_values) / n
        std_dev = variance ** 0.5
        
        stats_lines = [
            f"Count: {n} points",
            f"Mean: {mean:.2f}",
            f"Median: {median:.2f}",
            f"Standard Deviation: {std_dev:.2f}",
            f"Range: {range_val:.2f} (from {min_val:.2f} to {max_val:.2f})"
        ]
        
        # Compare with overall dataset
        if chart_statistics:
            overall_mean = chart_statistics.get('mean')
            overall_std = chart_statistics.get('std_dev')
            
            if overall_mean is not None:
                diff_from_overall = mean - overall_mean
                stats_lines.append("")
                stats_lines.append("Comparison with Overall Dataset:")
                stats_lines.append(f"Selection mean vs. overall mean: {diff_from_overall:+.2f}")
                
                if overall_std is not None and overall_std > 0:
                    z_score = diff_from_overall / overall_std
                    stats_lines.append(f"Selection mean Z-score: {z_score:.2f}")
        
        return "\n".join(stats_lines)
    
    def _analyze_outliers_in_selection(self, selected_points: List[Tuple[int, Any, float]], chart_statistics: Dict[str, Any]) -> str:
        """Analyze outliers within the selected data points."""
        if len(selected_points) < 4:
            return "Need at least 4 points for outlier analysis."
        
        y_values = [point[2] for point in selected_points]
        
        # IQR method
        sorted_values = sorted(y_values)
        n = len(sorted_values)
        q1 = sorted_values[n // 4]
        q3 = sorted_values[3 * n // 4]
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        iqr_outliers = [point for point in selected_points if point[2] < lower_bound or point[2] > upper_bound]
        
        # Z-score method (within selection)
        mean = sum(y_values) / len(y_values)
        std_dev = (sum((y - mean) ** 2 for y in y_values) / len(y_values)) ** 0.5
        
        z_outliers = []
        if std_dev > 0:
            z_outliers = [point for point in selected_points if abs((point[2] - mean) / std_dev) > 2]
        
        analysis_lines = [
            f"Outliers in Selection (IQR method): {len(iqr_outliers)} points",
            f"Outliers in Selection (Z-score method): {len(z_outliers)} points"
        ]
        
        if iqr_outliers:
            analysis_lines.append("")
            analysis_lines.append("IQR Outliers:")
            for point in iqr_outliers[:3]:  # Show first 3
                analysis_lines.append(f"  Point {point[0] + 1}: {point[1]} → {point[2]:.2f}")
            if len(iqr_outliers) > 3:
                analysis_lines.append(f"  ... and {len(iqr_outliers) - 3} more")
        
        return "\n".join(analysis_lines)

class DataPointDrillDownDialog(QDialog):
    """Dialog for detailed data point analysis and drill-down information."""
    
    def __init__(self, data_point_info: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.setWindowTitle("Data Point Analysis")
        self.setModal(True)
        self.resize(500, 400)
        
        # Main layout
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Title
        title_label = QLabel("📊 Detailed Data Point Analysis")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        layout.addWidget(title_label)
        
        # Data Point Information
        data_group = QGroupBox("Data Point Information")
        data_layout = QGridLayout(data_group)
        
        row = 0
        for key, value in data_point_info.get('basic_info', {}).items():
            label = QLabel(f"{key}:")
            label.setStyleSheet("font-weight: bold;")
            value_label = QLabel(str(value))
            data_layout.addWidget(label, row, 0)
            data_layout.addWidget(value_label, row, 1)
            row += 1
        
        layout.addWidget(data_group)
        
        # Statistical Context
        if 'statistical_context' in data_point_info:
            stats_group = QGroupBox("Statistical Context")
            stats_layout = QVBoxLayout(stats_group)
            
            stats_text = QTextEdit()
            stats_text.setReadOnly(True)
            stats_text.setMaximumHeight(120)
            stats_text.setPlainText(data_point_info['statistical_context'])
            stats_layout.addWidget(stats_text)
            
            layout.addWidget(stats_group)
        
        # Comparative Analysis
        if 'comparative_analysis' in data_point_info:
            comp_group = QGroupBox("Comparative Analysis")
            comp_layout = QVBoxLayout(comp_group)
            
            comp_text = QTextEdit()
            comp_text.setReadOnly(True)
            comp_text.setMaximumHeight(100)
            comp_text.setPlainText(data_point_info['comparative_analysis'])
            comp_layout.addWidget(comp_text)
            
            layout.addWidget(comp_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)

class ChartInteractionManager(QObject):
    """Attach interactive behaviours (zoom, pan, hover, click-to-drill, selection) to a QChartView."""

    def __init__(self, chart_view: QChartView):
        super().__init__(chart_view)
        self.chart_view = chart_view
        self.hover_enabled = True
        self.click_drill_enabled = True
        self.selection_enabled = True
        self.brush_enabled = True
        self.chart_data = []  # Store original chart data for tooltips
        self.x_variable_info = None  # Store X variable metadata
        self.y_variable_info = None  # Store Y variable metadata
        self.chart_statistics = {}  # Store chart statistics for context
        self.selected_points: Set[int] = set()  # Store indices of selected points
        self.selection_series = None  # Series for highlighting selected points
        self.brush_start_pos = None  # Start position for brush selection
        self.brush_active = False  # Whether brush selection is active
        self.brush_rect_item = None  # Graphics item for brush selection rectangle
        self._setup_default_interactions()

    # ---------------------------------------------------------------------
    # Public helpers
    # ---------------------------------------------------------------------
    def reset_zoom(self):
        """Reset zoom to the original state."""
        try:
            if self.chart_view and self.chart_view.chart():
                self.chart_view.chart().zoomReset()
        except RuntimeError:
            # Handle case where QChartView has been deleted during shutdown
            pass

    def enable_hover_tooltips(self, enabled: bool = True):
        """Enable or disable hover tooltips."""
        self.hover_enabled = enabled
        if not enabled:
            QToolTip.hideText()

    def enable_click_drill_down(self, enabled: bool = True):
        """Enable or disable click-to-drill-down functionality."""
        self.click_drill_enabled = enabled

    def enable_data_point_selection(self, enabled: bool = True):
        """Enable or disable data point selection functionality."""
        self.selection_enabled = enabled
        if not enabled:
            self.clear_selection()

    def enable_brush_selection(self, enabled: bool = True):
        """Enable or disable brush selection functionality."""
        self.brush_enabled = enabled

    def clear_selection(self):
        """Clear all selected data points."""
        self.selected_points.clear()
        self._update_selection_visualization()

    def get_selected_points(self) -> List[Tuple[int, Any, float]]:
        """Get list of selected data points."""
        return [(i, self.chart_data[i][0], self.chart_data[i][1]) for i in self.selected_points if i < len(self.chart_data)]

    def show_selection_analysis(self):
        """Show analysis dialog for selected data points."""
        if not self.selected_points:
            return
        
        selected_data = self.get_selected_points()
        dialog = DataPointSelectionDialog(selected_data, self.chart_statistics, self.chart_view)
        dialog.exec()

    def analyze_brush_region(self, start_pos: QPointF, end_pos: QPointF):
        """Analyze data points within a brush-selected rectangular region."""
        if not self.chart_data:
            return
        
        # Define region bounds
        x_min = min(start_pos.x(), end_pos.x())
        x_max = max(start_pos.x(), end_pos.x())
        y_min = min(start_pos.y(), end_pos.y())
        y_max = max(start_pos.y(), end_pos.y())
        
        # Find points within the region
        region_points = []
        for i, (x_val, y_val) in enumerate(self.chart_data):
            try:
                # Convert X value for comparison
                if isinstance(x_val, str):
                    chart_x = float(i)
                else:
                    chart_x = float(x_val)
                
                chart_y = float(y_val)
                
                # Check if point is within region bounds
                if x_min <= chart_x <= x_max and y_min <= chart_y <= y_max:
                    region_points.append((i, x_val, y_val))
                    
            except (ValueError, TypeError):
                continue
        
        if region_points:
            region_bounds = {
                'x_min': x_min,
                'x_max': x_max,
                'y_min': y_min,
                'y_max': y_max
            }
            
            dialog = BrushSelectionDialog(region_points, region_bounds, self.chart_statistics, self.chart_view)
            dialog.exec()
        else:
            # Show a simple message if no points in region
            from PySide6.QtWidgets import QMessageBox
            msg = QMessageBox(self.chart_view)
            msg.setWindowTitle("Region Analysis")
            msg.setText("No data points found in the selected region.")
            msg.setIcon(QMessageBox.Information)
            msg.exec()

    def set_chart_data(self, data: List[Tuple], x_variable_info: Dict[str, Any] = None, 
                      y_variable_info: Dict[str, Any] = None, statistics: Dict[str, Any] = None):
        """Set chart data and metadata for tooltip generation.
        
        Args:
            data: List of (x_value, y_value) tuples
            x_variable_info: Dictionary with X variable metadata (name, unit, description)
            y_variable_info: Dictionary with Y variable metadata (name, unit, description)
            statistics: Dictionary with chart statistics (mean, std_dev, r_squared, etc.)
        """
        self.chart_data = data or []
        self.x_variable_info = x_variable_info or {}
        self.y_variable_info = y_variable_info or {}
        self.chart_statistics = statistics or {}
        # Clear selection when new data is set
        self.clear_selection()

    def set_box_plot_data(self, box_stats, variable_info: Dict[str, Any] = None, statistics: Dict[str, Any] = None):
        """Set box plot data and metadata for tooltip generation.
        
        Args:
            box_stats: BoxPlotStats object with quartiles, outliers, etc.
            variable_info: Dictionary with variable metadata (name, unit, description)
            statistics: Dictionary with box plot statistics
        """
        # Store box plot specific data
        self.box_plot_stats = box_stats
        self.y_variable_info = variable_info or {}
        self.chart_statistics = statistics or {}
        
        # Convert box plot data to standard format for interaction
        # For box plots, we'll use a representative data point at the median
        if box_stats:
            self.chart_data = [(0, box_stats.median)]  # Single point at median
        else:
            self.chart_data = []
        
        # Clear selection when new data is set
        self.clear_selection()

    # ---------------------------------------------------------------------
    # Internal methods
    # ---------------------------------------------------------------------
    def _setup_default_interactions(self):
        """Enable rubber-band zooming, mouse wheel zoom, and panning."""
        # Rectangle rubber-band for zoom selection
        self.chart_view.setRubberBand(QChartView.RectangleRubberBand)
        # Enable mouse wheel zoom; QtCharts does this automatically when rubber band is enabled.
        # Enable panning via middle mouse button (or left while holding space)
        self.chart_view.setDragMode(QChartView.ScrollHandDrag)
        # Improve gesture smoothing for touch devices if available
        try:
            self.chart_view.viewport().setAttribute(Qt.WA_AcceptTouchEvents, True)
        except Exception:
            pass

        # Install event filter for double-click, hover, click, and selection
        self.chart_view.viewport().installEventFilter(self)
        # Enable mouse tracking for hover events
        self.chart_view.setMouseTracking(True)
        self.chart_view.viewport().setMouseTracking(True)

    def _find_nearest_data_point(self, chart_pos: QPointF) -> Optional[Tuple[int, float, float]]:
        """Find the nearest data point to the given chart position.
        
        Args:
            chart_pos: Position in chart coordinates
            
        Returns:
            Tuple of (index, x_value, y_value) or None if no data
        """
        if not self.chart_data:
            return None

        min_distance = float('inf')
        nearest_point = None
        
        for i, (x_val, y_val) in enumerate(self.chart_data):
            try:
                # Convert string X values to numeric for distance calculation
                if isinstance(x_val, str):
                    x_numeric = float(i)  # Use index for string-based X values
                else:
                    x_numeric = float(x_val)
                
                y_numeric = float(y_val)
                
                # Calculate distance to chart position
                distance = ((x_numeric - chart_pos.x()) ** 2 + (y_numeric - chart_pos.y()) ** 2) ** 0.5
                
                if distance < min_distance:
                    min_distance = distance
                    nearest_point = (i, x_val, y_val)
                    
            except (ValueError, TypeError):
                continue
        
        # Only return if reasonably close (within 10% of chart range)
        if min_distance < float('inf') and min_distance < 50:  # Adjust threshold as needed
            return nearest_point
        
        return None

    def _update_selection_visualization(self):
        """Update the visual representation of selected data points."""
        try:
            # Remove existing selection series
            if self.selection_series:
                self.chart_view.chart().removeSeries(self.selection_series)
                self.selection_series = None
            
            if not self.selected_points or not self.chart_data:
                return
            
            # Create new selection series
            self.selection_series = QScatterSeries()
            self.selection_series.setName("Selected Points")
            
            # Add selected points to the series
            for index in self.selected_points:
                if index < len(self.chart_data):
                    x_val, y_val = self.chart_data[index]
                    
                    # Convert X value for chart positioning
                    if isinstance(x_val, str):
                        chart_x = float(index)
                    else:
                        chart_x = float(x_val)
                    
                    self.selection_series.append(chart_x, float(y_val))
            
            # Style the selection series
            from PySide6 import QtGui
            selection_color = QtGui.QColor("#FF6B35")  # Orange color for selection
            self.selection_series.setColor(selection_color)
            self.selection_series.setMarkerSize(10)
            self.selection_series.setMarkerShape(QScatterSeries.MarkerShapeCircle)
            
            # Add to chart
            self.chart_view.chart().addSeries(self.selection_series)
            
            # Attach to existing axes
            for axis in self.chart_view.chart().axes():
                self.selection_series.attachAxis(axis)
                
        except Exception as e:
            print(f"Warning: Error updating selection visualization: {e}")

    def _create_brush_rectangle(self, start_pos: QPointF, current_pos: QPointF):
        """Create or update the visual brush selection rectangle."""
        try:
            # Remove existing rectangle if it exists
            self._remove_brush_rectangle()
            
            # Convert chart coordinates to scene coordinates
            start_scene = self.chart_view.chart().mapToPosition(start_pos)
            current_scene = self.chart_view.chart().mapToPosition(current_pos)
            
            # Create rectangle in scene coordinates
            rect = QRectF(start_scene, current_scene).normalized()
            
            # Create graphics rectangle item
            self.brush_rect_item = QGraphicsRectItem(rect)
            
            # Style the rectangle
            pen = QPen(QColor("#FF6B35"))  # Orange color
            pen.setWidth(2)
            pen.setStyle(Qt.DashLine)
            self.brush_rect_item.setPen(pen)
            
            # Semi-transparent fill
            brush = QBrush(QColor(255, 107, 53, 30))  # Orange with alpha
            self.brush_rect_item.setBrush(brush)
            
            # Add to chart scene
            chart_scene = self.chart_view.chart().scene()
            if chart_scene:
                chart_scene.addItem(self.brush_rect_item)
                
        except Exception as e:
            print(f"Warning: Error creating brush rectangle: {e}")

    def _remove_brush_rectangle(self):
        """Remove the visual brush selection rectangle."""
        try:
            if self.brush_rect_item:
                chart_scene = self.chart_view.chart().scene()
                if chart_scene:
                    chart_scene.removeItem(self.brush_rect_item)
                self.brush_rect_item = None
        except Exception as e:
            print(f"Warning: Error removing brush rectangle: {e}")

    def _create_tooltip_text(self, index: int, x_value: Any, y_value: float) -> str:
        """Create rich tooltip text for a data point.
        
        Args:
            index: Index of the data point
            x_value: X-axis value
            y_value: Y-axis value
            
        Returns:
            Formatted tooltip text
        """
        tooltip_lines = []
        
        # Data point information
        x_name = self.x_variable_info.get('name', 'X')
        y_name = self.y_variable_info.get('name', 'Y')
        y_unit = self.y_variable_info.get('unit', '')
        
        # Format X value
        if isinstance(x_value, str):
            x_display = x_value
        else:
            x_display = f"{x_value:.2f}"
        
        # Format Y value with unit
        if y_unit == 'currency':
            y_display = f"${y_value:.2f}"
        elif y_unit == 'percent':
            y_display = f"{y_value:.1f}%"
        elif y_unit == 'hours':
            y_display = f"{y_value:.2f} hrs"
        elif y_unit == 'time':
            # Convert decimal hours to HH:MM format
            hours = int(y_value)
            minutes = int((y_value - hours) * 60)
            y_display = f"{hours:02d}:{minutes:02d}"
        else:
            y_display = f"{y_value:.2f}"
        
        tooltip_lines.append(f"<b>{x_name}:</b> {x_display}")
        tooltip_lines.append(f"<b>{y_name}:</b> {y_display}")
        
        # Add data point index
        tooltip_lines.append(f"<b>Point:</b> {index + 1} of {len(self.chart_data)}")
        
        # Show selection status
        if index in self.selected_points:
            tooltip_lines.append("<b>Status:</b> Selected ✓")
        
        # Add statistical context if available
        if self.chart_statistics:
            tooltip_lines.append("")  # Separator
            tooltip_lines.append("<b>Statistical Context:</b>")
            
            # Show mean and how this point compares
            mean = self.chart_statistics.get('mean')
            if mean is not None:
                diff_from_mean = y_value - mean
                if abs(diff_from_mean) > 0.01:
                    direction = "above" if diff_from_mean > 0 else "below"
                    tooltip_lines.append(f"• {abs(diff_from_mean):.2f} {direction} mean ({mean:.2f})")
                else:
                    tooltip_lines.append(f"• Near mean ({mean:.2f})")
            
            # Show standard deviation context
            std_dev = self.chart_statistics.get('std_dev')
            if std_dev is not None and std_dev > 0:
                z_score = (y_value - mean) / std_dev if mean is not None else 0
                if abs(z_score) > 2:
                    tooltip_lines.append(f"• Outlier (Z-score: {z_score:.1f})")
                elif abs(z_score) > 1:
                    tooltip_lines.append(f"• Above average variation (Z-score: {z_score:.1f})")
                else:
                    tooltip_lines.append(f"• Normal variation (Z-score: {z_score:.1f})")
            
            # Show correlation context
            correlation = self.chart_statistics.get('correlation')
            if correlation is not None and abs(correlation) > 0.1:
                strength = "strong" if abs(correlation) > 0.7 else "moderate" if abs(correlation) > 0.3 else "weak"
                direction = "positive" if correlation > 0 else "negative"
                tooltip_lines.append(f"• {strength.title()} {direction} correlation ({correlation:.3f})")
        
        # Add interaction instructions
        tooltip_lines.append("")
        tooltip_lines.append("<i>Click for detailed analysis</i>")
        tooltip_lines.append("<i>Ctrl+Click to select/deselect</i>")
        tooltip_lines.append("<i>Shift+Drag for region analysis</i>")
        if self.selected_points:
            tooltip_lines.append(f"<i>{len(self.selected_points)} points selected</i>")
        
        return "<br/>".join(tooltip_lines)

    def _create_drill_down_info(self, index: int, x_value: Any, y_value: float) -> Dict[str, Any]:
        """Create comprehensive drill-down information for a data point.
        
        Args:
            index: Index of the data point
            x_value: X-axis value
            y_value: Y-axis value
            
        Returns:
            Dictionary with detailed analysis information
        """
        x_name = self.x_variable_info.get('name', 'X')
        y_name = self.y_variable_info.get('name', 'Y')
        y_unit = self.y_variable_info.get('unit', '')
        
        # Format values
        if isinstance(x_value, str):
            x_display = x_value
        else:
            x_display = f"{x_value:.2f}"
        
        if y_unit == 'currency':
            y_display = f"${y_value:.2f}"
        elif y_unit == 'percent':
            y_display = f"{y_value:.1f}%"
        elif y_unit == 'hours':
            y_display = f"{y_value:.2f} hrs"
        elif y_unit == 'time':
            hours = int(y_value)
            minutes = int((y_value - hours) * 60)
            y_display = f"{hours:02d}:{minutes:02d}"
        else:
            y_display = f"{y_value:.2f}"
        
        # Basic information
        basic_info = {
            x_name: x_display,
            y_name: y_display,
            "Data Point": f"{index + 1} of {len(self.chart_data)}",
            "Position in Dataset": f"{((index + 1) / len(self.chart_data) * 100):.1f}% through data",
            "Selection Status": "Selected" if index in self.selected_points else "Not selected"
        }
        
        # Statistical context
        statistical_context = []
        if self.chart_statistics:
            mean = self.chart_statistics.get('mean')
            std_dev = self.chart_statistics.get('std_dev')
            median = self.chart_statistics.get('median')
            min_val = self.chart_statistics.get('min')
            max_val = self.chart_statistics.get('max')
            
            if mean is not None:
                diff_from_mean = y_value - mean
                statistical_context.append(f"Mean Comparison: {abs(diff_from_mean):.2f} {'above' if diff_from_mean > 0 else 'below'} mean ({mean:.2f})")
            
            if median is not None:
                diff_from_median = y_value - median
                statistical_context.append(f"Median Comparison: {abs(diff_from_median):.2f} {'above' if diff_from_median > 0 else 'below'} median ({median:.2f})")
            
            if std_dev is not None and std_dev > 0 and mean is not None:
                z_score = (y_value - mean) / std_dev
                statistical_context.append(f"Z-Score: {z_score:.2f} (standard deviations from mean)")
                
                if abs(z_score) > 2:
                    statistical_context.append("Classification: Statistical outlier (|Z| > 2)")
                elif abs(z_score) > 1:
                    statistical_context.append("Classification: Above average variation (|Z| > 1)")
                else:
                    statistical_context.append("Classification: Normal variation (|Z| ≤ 1)")
            
            if min_val is not None and max_val is not None:
                range_position = (y_value - min_val) / (max_val - min_val) * 100 if max_val != min_val else 50
                statistical_context.append(f"Range Position: {range_position:.1f}% of data range ({min_val:.2f} to {max_val:.2f})")
        
        # Comparative analysis
        comparative_analysis = []
        if len(self.chart_data) > 1:
            # Compare with neighboring points
            if index > 0:
                prev_y = self.chart_data[index - 1][1]
                change_from_prev = y_value - prev_y
                comparative_analysis.append(f"Change from previous point: {change_from_prev:+.2f}")
            
            if index < len(self.chart_data) - 1:
                next_y = self.chart_data[index + 1][1]
                change_to_next = next_y - y_value
                comparative_analysis.append(f"Change to next point: {change_to_next:+.2f}")
            
            # Percentile ranking
            y_values = [point[1] for point in self.chart_data]
            y_values_sorted = sorted(y_values)
            percentile = (y_values_sorted.index(y_value) + 1) / len(y_values_sorted) * 100
            comparative_analysis.append(f"Percentile rank: {percentile:.1f}% (better than {percentile:.1f}% of data points)")
            
            # Local trend analysis
            window_size = min(5, len(self.chart_data) // 4)  # Use 25% of data or 5 points, whichever is smaller
            if window_size >= 3:
                start_idx = max(0, index - window_size // 2)
                end_idx = min(len(self.chart_data), start_idx + window_size)
                local_values = [self.chart_data[i][1] for i in range(start_idx, end_idx)]
                local_mean = sum(local_values) / len(local_values)
                comparative_analysis.append(f"Local trend (±{window_size//2} points): {y_value - local_mean:+.2f} from local mean ({local_mean:.2f})")
        
        return {
            'basic_info': basic_info,
            'statistical_context': '\n'.join(statistical_context),
            'comparative_analysis': '\n'.join(comparative_analysis)
        }

    def _show_drill_down_dialog(self, index: int, x_value: Any, y_value: float):
        """Show the drill-down dialog for a data point."""
        try:
            drill_down_info = self._create_drill_down_info(index, x_value, y_value)
            dialog = DataPointDrillDownDialog(drill_down_info, self.chart_view)
            dialog.exec()
        except Exception as e:
            print(f"Warning: Error showing drill-down dialog: {e}")

    # ------------------------------------------------------------------
    # Event filter to capture double-click, hover, click, and selection
    # ------------------------------------------------------------------
    def eventFilter(self, watched, event):
        try:
            if (self.chart_view and 
                self.chart_view.viewport() and 
                watched is self.chart_view.viewport()):
                
                # Handle double-click to reset zoom
                if event.type() == QEvent.MouseButtonDblClick:
                    self.reset_zoom()
                    return True
                
                # Handle mouse press for various interactions
                elif (event.type() == QEvent.MouseButtonPress and 
                      event.button() == Qt.LeftButton and 
                      self.chart_data):
                    
                    # Convert mouse position to chart coordinates
                    chart_pos = self.chart_view.chart().mapToValue(event.pos())
                    
                    # Check if Shift is pressed for brush selection
                    if (event.modifiers() & Qt.ShiftModifier and 
                        self.brush_enabled):
                        # Start brush selection
                        self.brush_start_pos = chart_pos
                        self.brush_active = True
                        return True  # Consume the event
                    
                    # Find nearest data point for other interactions
                    nearest_point = self._find_nearest_data_point(chart_pos)
                    
                    if nearest_point:
                        index, x_val, y_val = nearest_point
                        
                        # Check if Ctrl is pressed for selection
                        if (event.modifiers() & Qt.ControlModifier and 
                            self.selection_enabled):
                            # Toggle selection
                            if index in self.selected_points:
                                self.selected_points.remove(index)
                            else:
                                self.selected_points.add(index)
                            self._update_selection_visualization()
                            return True  # Consume the event
                        
                        # Regular click for drill-down
                        elif self.click_drill_enabled:
                            self._show_drill_down_dialog(index, x_val, y_val)
                            return True  # Consume the event
                
                # Handle mouse release for brush selection
                elif (event.type() == QEvent.MouseButtonRelease and 
                      event.button() == Qt.LeftButton and 
                      self.brush_active and 
                      self.brush_start_pos is not None):
                    
                    # End brush selection
                    chart_pos = self.chart_view.chart().mapToValue(event.pos())
                    
                    # Remove the visual rectangle
                    self._remove_brush_rectangle()
                    
                    # Analyze the selected region
                    self.analyze_brush_region(self.brush_start_pos, chart_pos)
                    
                    # Reset brush state
                    self.brush_start_pos = None
                    self.brush_active = False
                    return True  # Consume the event
                
                # Handle mouse move for brush selection or hover tooltips
                elif event.type() == QEvent.MouseMove:
                    
                    # Convert mouse position to chart coordinates
                    chart_pos = self.chart_view.chart().mapToValue(event.pos())
                    
                    # Handle brush selection rectangle update
                    if (self.brush_active and 
                        self.brush_start_pos is not None):
                        # Update brush selection rectangle
                        self._create_brush_rectangle(self.brush_start_pos, chart_pos)
                        return False  # Don't consume the event
                    
                    # Handle hover tooltips
                    elif (self.hover_enabled and 
                          self.chart_data):
                        
                        # Find nearest data point
                        nearest_point = self._find_nearest_data_point(chart_pos)
                        
                        if nearest_point:
                            index, x_val, y_val = nearest_point
                            tooltip_text = self._create_tooltip_text(index, x_val, y_val)
                            
                            # Show tooltip at cursor position
                            global_pos = self.chart_view.mapToGlobal(event.pos())
                            QToolTip.showText(global_pos, tooltip_text)
                        else:
                            # Hide tooltip if not near any data point
                            QToolTip.hideText()
                        
                        return False  # Don't consume the event
                
                # Hide tooltip when mouse leaves
                elif event.type() == QEvent.Leave:
                    QToolTip.hideText()
                    # Cancel brush selection if active
                    if self.brush_active:
                        self._remove_brush_rectangle()
                        self.brush_start_pos = None
                        self.brush_active = False
                    return False
                
                # Handle key press for canceling brush selection
                elif (event.type() == QEvent.KeyPress and 
                      event.key() == Qt.Key_Escape and 
                      self.brush_active):
                    # Cancel brush selection
                    self._remove_brush_rectangle()
                    self.brush_start_pos = None
                    self.brush_active = False
                    return True  # Consume the event
                    
        except RuntimeError:
            # Handle case where QChartView has been deleted during shutdown
            return False
        except Exception as e:
            # Handle any other exceptions gracefully
            print(f"Warning: Error in chart interaction event filter: {e}")
            return False
            
        return super().eventFilter(watched, event) 