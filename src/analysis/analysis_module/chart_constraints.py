# Chart Constraints Configuration for Tapered Flexibility
# This module defines the allowed variable combinations and chart types for the simplified charting system

# Allowed Y-axis Variables (Quantitative Metrics - Only 1 at a time)
ALLOWED_Y_VARIABLES = {
    'duration_average': {
        'display_name': 'Duration (Average)',
        'description': 'Average time spent on tasks',
        'unit': 'hours',
        'data_type': 'float'
    },
    'claim_datetime_average': {
        'display_name': 'Claim Time (Average)',
        'description': 'Average time of day for task claims',
        'unit': 'time',
        'data_type': 'time'
    },
    'money_made_total': {
        'display_name': 'Money Made (Total)',
        'description': 'Sum of earnings',
        'unit': 'currency',
        'data_type': 'float'
    },
    'money_made_average': {
        'display_name': 'Money Made (Average)',
        'description': 'Average earnings per task/unit',
        'unit': 'currency',
        'data_type': 'float'
    },
    'time_usage_percent': {
        'display_name': 'Time Usage %',
        'description': 'Percentage of time limit used',
        'unit': 'percent',
        'data_type': 'float'
    },
    'fail_rate_percent': {
        'display_name': 'Fail Rate %',
        'description': 'Percentage of failed tasks',
        'unit': 'percent',
        'data_type': 'float'
    },
    'average_rating': {
        'display_name': 'Average Rating',
        'description': 'Average score/rating',
        'unit': 'score',
        'data_type': 'float'
    }
}

# Allowed X-axis Variables (Categorical or Temporal Dimensions - Only 1 at a time)
ALLOWED_X_VARIABLES = {
    'time_day': {
        'display_name': 'Time (Day)',
        'description': 'Date audited by day',
        'data_type': 'date',
        'group_by_field': 'date_audited'
    },
    'time_week': {
        'display_name': 'Time (Week)',
        'description': 'Week identifier',
        'data_type': 'categorical',
        'group_by_field': 'week_id'
    },
    'time_month': {
        'display_name': 'Time (Month)',
        'description': 'Aggregated by month from date audited',
        'data_type': 'date',
        'group_by_field': 'date_audited',
        'aggregation': 'month'
    },
    'projects': {
        'display_name': 'Projects',
        'description': 'Project name',
        'data_type': 'categorical',
        'group_by_field': 'project_name'
    },
    'claim_time_ranges': {
        'display_name': 'Claim Time Ranges',
        'description': 'Categorical periods from claim time (Morning, Noon, Afternoon, Night)',
        'data_type': 'categorical',
        'group_by_field': 'time_begin',
        'transformation': 'time_range_categorization'
    }
}

# Allowed Chart Types and their compatibility
ALLOWED_CHART_TYPES = {
    'line': {
        'display_name': 'Line Chart',
        'description': 'Primarily for time-series data',
        'compatible_x_variables': ['time_day', 'time_week', 'time_month']
    },
    'bar': {
        'display_name': 'Bar Chart',
        'description': 'Suitable for categorical variables and discrete periods',
        'compatible_x_variables': ['time_day', 'time_week', 'time_month', 'projects', 'claim_time_ranges']
    }
}

# Time range categorization mapping
TIME_RANGE_CATEGORIES = {
    'morning': {'start': 6, 'end': 12, 'display': 'Morning (6:00-12:00)'},
    'noon': {'start': 12, 'end': 15, 'display': 'Noon (12:00-15:00)'},
    'afternoon': {'start': 15, 'end': 18, 'display': 'Afternoon (15:00-18:00)'},
    'night': {'start': 18, 'end': 6, 'display': 'Night (18:00-6:00)'}  # Wraps around midnight
}

def get_allowed_y_variables():
    """Get list of allowed Y-axis variables"""
    return ALLOWED_Y_VARIABLES

def get_allowed_x_variables():
    """Get list of allowed X-axis variables"""
    return ALLOWED_X_VARIABLES

def get_allowed_chart_types():
    """Get list of allowed chart types"""
    return ALLOWED_CHART_TYPES

def get_compatible_chart_types(x_variable):
    """Get chart types compatible with the given X variable"""
    compatible_types = []
    for chart_type, config in ALLOWED_CHART_TYPES.items():
        if x_variable in config['compatible_x_variables']:
            compatible_types.append(chart_type)
    return compatible_types

def validate_variable_combination(x_variable, y_variable, chart_type):
    """Validate if the variable combination and chart type are allowed"""
    # Check if variables are in allowed lists
    if x_variable not in ALLOWED_X_VARIABLES:
        return False, f"X variable '{x_variable}' is not allowed"
    
    if y_variable not in ALLOWED_Y_VARIABLES:
        return False, f"Y variable '{y_variable}' is not allowed"
    
    # Check if chart type is compatible with X variable
    if chart_type not in ALLOWED_CHART_TYPES:
        return False, f"Chart type '{chart_type}' is not allowed"
    
    compatible_types = get_compatible_chart_types(x_variable)
    if chart_type not in compatible_types:
        return False, f"Chart type '{chart_type}' is not compatible with X variable '{x_variable}'"
    
    return True, "Valid combination"

def categorize_time_to_range(time_string):
    """Convert time string to time range category"""
    if not time_string or not time_string.strip():
        return 'unknown'
    
    try:
        from datetime import datetime
        # Parse datetime string (expecting format like '2024-01-01 14:30:00')
        dt = datetime.strptime(time_string, '%Y-%m-%d %H:%M:%S')
        hour = dt.hour
        
        # Determine time range
        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 15:
            return 'noon'
        elif 15 <= hour < 18:
            return 'afternoon'
        else:  # 18-24 or 0-6
            return 'night'
            
    except (ValueError, AttributeError):
        return 'unknown'

def get_time_range_display_name(category):
    """Get display name for time range category"""
    if category in TIME_RANGE_CATEGORIES:
        return TIME_RANGE_CATEGORIES[category]['display']
    return 'Unknown' 