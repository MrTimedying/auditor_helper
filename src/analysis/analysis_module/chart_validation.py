"""
Chart Validation System

This module provides comprehensive validation for chart data and variable combinations,
ensuring proper error handling and user guidance for chart generation.
"""

from enum import Enum
from typing import List, Tuple, Dict, Any

class ValidationIssue:
    """Represents a validation issue with severity and suggested actions"""
    
    class Severity(Enum):
        INFO = "info"
        WARNING = "warning"
        ERROR = "error"
        CRITICAL = "critical"
    
    def __init__(self, severity: Severity, message: str, suggestions: List[str] = None):
        self.severity = severity
        self.message = message
        self.suggestions = suggestions or []

class ChartValidationEngine:
    """Comprehensive validation engine for chart data and variable combinations"""
    
    def __init__(self):
        self.max_categories = 50  # Maximum categories for effective visualization
        self.min_data_points = 1  # Minimum data points required
        self.max_y_variables = 10  # Maximum Y variables for readability
    
    def validate_chart_request(self, data: List[Tuple], x_variable: Tuple[str, str], 
                             y_variables: List[Tuple[str, str]], chart_type: str) -> List[ValidationIssue]:
        """Comprehensive validation of chart generation request"""
        issues = []
        
        # Data quality checks
        issues.extend(self._validate_data_quality(data, x_variable, y_variables))
        
        # Variable combination checks
        issues.extend(self._validate_variable_combinations(x_variable, y_variables, chart_type))
        
        # Chart type specific checks
        issues.extend(self._validate_chart_type_compatibility(data, x_variable, y_variables, chart_type))
        
        # Performance and usability checks
        issues.extend(self._validate_performance_considerations(data, x_variable, y_variables))
        
        return issues
    
    def _validate_data_quality(self, data: List[Tuple], x_variable: Tuple[str, str], 
                              y_variables: List[Tuple[str, str]]) -> List[ValidationIssue]:
        """Validate data quality and completeness"""
        issues = []
        
        # Check for empty dataset
        if not data:
            issues.append(ValidationIssue(
                ValidationIssue.Severity.ERROR,
                "No data available for the selected variables and time range.",
                ["Try selecting a different time range", "Check if tasks exist for the selected period", "Verify data import was successful"]
            ))
            return issues
        
        # Check for insufficient data
        if len(data) < self.min_data_points:
            issues.append(ValidationIssue(
                ValidationIssue.Severity.WARNING,
                f"Very limited data available ({len(data)} data point{'s' if len(data) != 1 else ''}).",
                ["Consider expanding the time range", "Results may not be meaningful with so few data points"]
            ))
        
        # Check for all-null Y variables
        null_y_vars = []
        for i, (y_var_name, _) in enumerate(y_variables):
            y_column_index = i + 1  # Y variables start at index 1
            if y_column_index < len(data[0]):
                y_values = [row[y_column_index] for row in data if len(row) > y_column_index]
                if all(val in (None, 0, '', 'None') for val in y_values):
                    null_y_vars.append(y_var_name)
        
        if null_y_vars:
            issues.append(ValidationIssue(
                ValidationIssue.Severity.WARNING,
                f"The following variables contain no meaningful data: {', '.join(null_y_vars)}",
                ["Consider removing these variables", "Check data quality for these metrics"]
            ))
        
        # Check for extreme outliers (basic detection)
        outlier_vars = self._detect_outliers(data, y_variables)
        if outlier_vars:
            issues.append(ValidationIssue(
                ValidationIssue.Severity.INFO,
                f"Potential outliers detected in: {', '.join(outlier_vars)}",
                ["Review data for unusual values", "Consider if outliers represent real events or data errors"]
            ))
        
        return issues
    
    def _validate_variable_combinations(self, x_variable: Tuple[str, str], 
                                      y_variables: List[Tuple[str, str]], chart_type: str) -> List[ValidationIssue]:
        """Validate variable combinations and compatibility"""
        issues = []
        
        # Check for too many Y variables
        if len(y_variables) > self.max_y_variables:
            issues.append(ValidationIssue(
                ValidationIssue.Severity.WARNING,
                f"Too many Y variables ({len(y_variables)}) may result in cluttered visualization.",
                ["Consider reducing to 3-5 variables for better readability", "Use separate charts for different variable groups"]
            ))
        
        # Check for duplicate variables
        y_var_names = [var[0] for var in y_variables]
        duplicates = [name for name in y_var_names if y_var_names.count(name) > 1]
        if duplicates:
            issues.append(ValidationIssue(
                ValidationIssue.Severity.ERROR,
                f"Duplicate Y variables detected: {', '.join(set(duplicates))}",
                ["Remove duplicate variables from selection"]
            ))
        
        # Check for same variable in X and Y
        x_var_name = x_variable[0]
        if x_var_name in y_var_names:
            issues.append(ValidationIssue(
                ValidationIssue.Severity.WARNING,
                f"Variable '{x_var_name}' is used as both X and Y variable.",
                ["This may not provide meaningful insights", "Consider using different variables"]
            ))
        
        return issues
    
    def _validate_chart_type_compatibility(self, data: List[Tuple], x_variable: Tuple[str, str],
                                         y_variables: List[Tuple[str, str]], chart_type: str) -> List[ValidationIssue]:
        """Validate chart type compatibility with selected variables"""
        issues = []
        x_var_name, x_var_type = x_variable
        
        if chart_type == "Pie Chart":
            # Pie chart specific validations
            if len(y_variables) != 1:
                issues.append(ValidationIssue(
                    ValidationIssue.Severity.ERROR,
                    "Pie charts require exactly one Y variable.",
                    ["Select only one Y variable", "Use a different chart type for multiple variables"]
                ))
            
            if x_var_type != "categorical":
                issues.append(ValidationIssue(
                    ValidationIssue.Severity.ERROR,
                    "Pie charts require a categorical X variable.",
                    ["Select a categorical variable (like Project Name, Locale) for X-axis", "Use Bar Chart for quantitative X variables"]
                ))
            
            # Check for too many categories in pie chart
            if data and x_var_type == "categorical":
                unique_categories = len(set(row[0] for row in data))
                if unique_categories > 10:
                    issues.append(ValidationIssue(
                        ValidationIssue.Severity.WARNING,
                        f"Pie chart with {unique_categories} categories may be difficult to read.",
                        ["Consider grouping smaller categories into 'Other'", "Use Bar Chart for better category visualization"]
                    ))
        
        elif chart_type == "Scatter Plot":
            # Scatter plot specific validations
            if len(y_variables) > 1:
                issues.append(ValidationIssue(
                    ValidationIssue.Severity.INFO,
                    "Scatter plots will only use the first Y variable.",
                    ["Only the first selected Y variable will be plotted", "Use Line Chart to show multiple Y variables"]
                ))
        
        elif chart_type == "Line Chart":
            # Line chart recommendations
            if x_var_type == "categorical":
                unique_categories = len(set(row[0] for row in data)) if data else 0
                if unique_categories > self.max_categories:
                    issues.append(ValidationIssue(
                        ValidationIssue.Severity.WARNING,
                        f"Line chart with {unique_categories} categories may be difficult to read.",
                        ["Consider using Bar Chart for categorical data", "Filter data to reduce categories"]
                    ))
        
        elif chart_type == "Bar Chart":
            # Bar chart validations
            if data and x_var_type == "categorical":
                unique_categories = len(set(row[0] for row in data))
                if unique_categories > self.max_categories:
                    issues.append(ValidationIssue(
                        ValidationIssue.Severity.WARNING,
                        f"Bar chart with {unique_categories} categories may be overcrowded.",
                        ["Consider filtering data", "Group smaller categories", "Use horizontal bars for many categories"]
                    ))
        
        return issues
    
    def _validate_performance_considerations(self, data: List[Tuple], x_variable: Tuple[str, str],
                                           y_variables: List[Tuple[str, str]]) -> List[ValidationIssue]:
        """Validate performance and memory considerations"""
        issues = []
        
        # Check for large datasets
        if len(data) > 1000:
            issues.append(ValidationIssue(
                ValidationIssue.Severity.INFO,
                f"Large dataset ({len(data)} points) may affect chart performance.",
                ["Chart rendering may be slower", "Consider data sampling for better performance"]
            ))
        
        if len(data) > 10000:
            issues.append(ValidationIssue(
                ValidationIssue.Severity.WARNING,
                f"Very large dataset ({len(data)} points) detected.",
                ["Consider filtering data by time range", "Performance may be significantly impacted"]
            ))
        
        return issues
    
    def _detect_outliers(self, data: List[Tuple], y_variables: List[Tuple[str, str]]) -> List[str]:
        """Basic outlier detection for Y variables"""
        outlier_vars = []
        
        for i, (y_var_name, _) in enumerate(y_variables):
            y_column_index = i + 1
            if y_column_index < len(data[0]):
                y_values = []
                for row in data:
                    if len(row) > y_column_index:
                        try:
                            val = float(row[y_column_index])
                            if val != 0:  # Ignore zeros
                                y_values.append(val)
                        except (ValueError, TypeError):
                            continue
                
                if len(y_values) > 3:  # Need minimum data for outlier detection
                    # Simple outlier detection: values beyond 3 standard deviations
                    mean_val = sum(y_values) / len(y_values)
                    variance = sum((x - mean_val) ** 2 for x in y_values) / len(y_values)
                    std_dev = variance ** 0.5
                    
                    if std_dev > 0:
                        outliers = [v for v in y_values if abs(v - mean_val) > 3 * std_dev]
                        if outliers:
                            outlier_vars.append(y_var_name)
        
        return outlier_vars
    
    def get_chart_type_requirements(self, chart_type: str) -> Dict[str, Any]:
        """Get requirements and constraints for specific chart types"""
        requirements = {
            "Pie Chart": {
                "max_y_variables": 1,
                "required_x_type": "categorical",
                "max_categories": 10,
                "description": "Shows parts of a whole using categorical data"
            },
            "Line Chart": {
                "max_y_variables": 10,
                "preferred_x_type": "quantitative",
                "max_categories": 50,
                "description": "Shows trends and changes over continuous data"
            },
            "Bar Chart": {
                "max_y_variables": 10,
                "preferred_x_type": "categorical",
                "max_categories": 50,
                "description": "Compares quantities across categories"
            },
            "Scatter Plot": {
                "max_y_variables": 1,
                "preferred_x_type": "quantitative",
                "description": "Shows relationships between two quantitative variables"
            }
        }
        return requirements.get(chart_type, {}) 