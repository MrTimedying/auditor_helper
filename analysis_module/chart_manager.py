from PySide6.QtCharts import QChart, QChartView, QLineSeries, QBarSeries, QBarSet, QScatterSeries, QPieSeries, QPieSlice, QValueAxis, QBarCategoryAxis
from PySide6 import QtCore, QtGui

class ChartManager:
    def __init__(self, chart_view: QChartView):
        self.chart_view = chart_view
        self.chart = chart_view.chart()

    def create_chart(self, data, x_variable, y_variables, chart_type):
        """Create QtChart based on data and configuration"""
        self.chart.removeAllSeries()
        # Remove all axes
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)
        
        x_var_name, x_var_type = x_variable
        chart_title = f"{chart_type}: {x_var_name} vs {', '.join([y[0] for y in y_variables])}"
        self.chart.setTitle(chart_title)
        
        if chart_type == "Line Chart":
            self.create_line_chart(data, x_variable, y_variables)
        elif chart_type == "Bar Chart":
            self.create_bar_chart(data, x_variable, y_variables)
        elif chart_type == "Scatter Plot":
            self.create_scatter_chart(data, x_variable, y_variables)
        elif chart_type == "Pie Chart":
            self.create_pie_chart(data, x_variable, y_variables)
    
    def create_line_chart(self, data, x_variable, y_variables):
        """Create line chart"""
        x_var_name, x_var_type = x_variable
        
        # Create series for each Y variable
        for i, (y_var_name, y_var_type) in enumerate(y_variables):
            series = QLineSeries()
            series.setName(y_var_name)
            # Make lines thinner
            pen = series.pen()
            pen.setWidth(1)  # Set line width to 1 pixel (thinner)
            series.setPen(pen)
            
            for row_idx, row in enumerate(data):
                x_val = row[0]
                y_val = row[i + 1]  # Y values start at index 1
                
                # Convert X value for plotting
                if x_var_type == "categorical":
                    # For categorical X, use row index
                    x_plot = float(row_idx)
                else:
                    # For quantitative X, convert to float
                    try:
                        x_plot = float(x_val)
                    except (ValueError, TypeError):
                        x_plot = float(row_idx)  # Fallback to index
                
                # Convert Y value
                try:
                    y_plot = float(y_val)
                except (ValueError, TypeError):
                    y_plot = 0  # Fallback to 0
                
                series.append(x_plot, y_plot)
            
            self.chart.addSeries(series)
        
        # Create axes - use category axis for categorical X variables
        if x_var_type == "categorical":
            categories = [str(row[0]) for row in data]
            axis_x = QBarCategoryAxis()
            axis_x.append(categories)
            axis_x.setTitleText(x_var_name)
            axis_x.setTitleBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis title color
            axis_x.setLabelsBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis labels color
            axis_x.setLinePenColor(QtGui.QColor("#D6D6D6"))  # Set axis line color
        else:
            axis_x = QValueAxis()
            axis_x.setTitleText(x_var_name)
            axis_x.setTitleBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis title color
            axis_x.setLabelsBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis labels color
            axis_x.setLinePenColor(QtGui.QColor("#D6D6D6"))  # Set axis line color
        self.chart.addAxis(axis_x, QtCore.Qt.AlignBottom)
        
        axis_y = QValueAxis()
        axis_y.setTitleText("Values")
        axis_y.setTitleBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis title color
        axis_y.setLabelsBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis labels color
        axis_y.setLinePenColor(QtGui.QColor("#D6D6D6"))  # Set axis line color
        self.chart.addAxis(axis_y, QtCore.Qt.AlignLeft)
        
        # Attach axes to series
        for series in self.chart.series():
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)
    
    def create_bar_chart(self, data, x_variable, y_variables):
        """Create bar chart"""
        x_var_name, x_var_type = x_variable
        
        # Create bar series
        series = QBarSeries()
        
        # Create bar sets for each Y variable
        bar_sets = []
        for y_var_name, y_var_type in y_variables:
            bar_set = QBarSet(y_var_name)
            for row in data:
                y_val = row[y_variables.index((y_var_name, y_var_type)) + 1]
                bar_set.append(float(y_val))
            bar_sets.append(bar_set)
            series.append(bar_set)
        
        self.chart.addSeries(series)
        
        # Create axes
        categories = [str(row[0]) for row in data]
        axis_x = QBarCategoryAxis()
        axis_x.append(categories)
        axis_x.setTitleText(x_var_name)
        axis_x.setTitleBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis title color
        axis_x.setLabelsBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis labels color
        axis_x.setLinePenColor(QtGui.QColor("#D6D6D6"))  # Set axis line color
        self.chart.addAxis(axis_x, QtCore.Qt.AlignBottom)
        
        axis_y = QValueAxis()
        axis_y.setTitleText("Values")
        axis_y.setTitleBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis title color
        axis_y.setLabelsBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis labels color
        axis_y.setLinePenColor(QtGui.QColor("#D6D6D6"))  # Set axis line color
        self.chart.addAxis(axis_y, QtCore.Qt.AlignLeft)
        
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
    
    def create_scatter_chart(self, data, x_variable, y_variables):
        """Create scatter plot"""
        # For scatter plots, use first Y variable only
        if y_variables:
            y_var_name, y_var_type = y_variables[0]
            
            series = QScatterSeries()
            series.setName(f"{x_variable[0]} vs {y_var_name}")
            series.setMarkerSize(8)
            
            for row_idx, row in enumerate(data):
                x_val = row[0]
                y_val = row[1]  # First Y variable
                
                # Convert values for plotting
                x_var_name, x_var_type = x_variable
                if x_var_type == "categorical":
                    x_plot = float(row_idx)
                else:
                    try:
                        x_plot = float(x_val)
                    except (ValueError, TypeError):
                        x_plot = float(row_idx)
                
                try:
                    y_plot = float(y_val)
                except (ValueError, TypeError):
                    y_plot = 0
                
                series.append(x_plot, y_plot)
            
            self.chart.addSeries(series)
            
            # Create axes
            x_var_name, x_var_type = x_variable
            if x_var_type == "categorical":
                categories = [str(row[0]) for row in data]
                axis_x = QBarCategoryAxis()
                axis_x.append(categories)
                axis_x.setTitleText(x_var_name)
                axis_x.setTitleBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis title color
                axis_x.setLabelsBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis labels color
                axis_x.setLinePenColor(QtGui.QColor("#D6D6D6"))  # Set axis line color
            else:
                axis_x = QValueAxis()
                axis_x.setTitleText(x_var_name)
                axis_x.setTitleBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis title color
                axis_x.setLabelsBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis labels color
                axis_x.setLinePenColor(QtGui.QColor("#D6D6D6"))  # Set axis line color
            self.chart.addAxis(axis_x, QtCore.Qt.AlignBottom)
            
            axis_y = QValueAxis()
            axis_y.setTitleText(y_var_name)
            axis_y.setTitleBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis title color
            axis_y.setLabelsBrush(QtGui.QBrush(QtGui.QColor("#D6D6D6")))  # Set axis labels color
            axis_y.setLinePenColor(QtGui.QColor("#D6D6D6"))  # Set axis line color
            self.chart.addAxis(axis_y, QtCore.Qt.AlignLeft)
            
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)
    
    def create_pie_chart(self, data, x_variable, y_variables):
        """Create pie chart"""
        if y_variables:
            y_var_name, y_var_type = y_variables[0]
            
            series = QPieSeries()
            
            for row in data:
                label = str(row[0])  # X variable as label
                value = float(row[1])  # First Y variable as value
                
                slice = QPieSlice(label, value)
                series.append(slice)
            
            self.chart.addSeries(series)

    def clear_chart(self):
        """Clear the chart completely when variables are modified"""
        self.chart.removeAllSeries()
        # Remove all axes
        for axis in self.chart.axes():
            self.chart.removeAxis(axis)
        self.chart.setTitle("Select variables and click 'Generate Chart'") 