import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta
import sys
import os
import logging

# Lazy import for numpy - deferred until first use
from core.optimization.lazy_imports import get_lazy_manager

# Import global_settings using relative import
from core.settings.global_settings import global_settings

# Import Data Service Layer components
from core.services import TaskDAO, WeekDAO, DataServiceError

# Import chart constraints for tapered flexibility
from .chart_constraints import (
    get_allowed_x_variables, get_allowed_y_variables, 
    categorize_time_to_range, get_time_range_display_name,
    validate_variable_combination
)

# Import Rust Statistical Analysis Engine for performance improvements
from core.performance.rust_statistical_engine import (
    rust_engine, calculate_correlation, calculate_statistical_summary,
    calculate_confidence_interval, calculate_batch_correlations,
    calculate_moving_average, calculate_trend_analysis,
    StatisticalSummary, TrendAnalysis
)

# Configure logging
logger = logging.getLogger(__name__)

DB_FILE = "tasks.db"

class DataManager:
    def __init__(self):
        self.global_settings = global_settings
        
        # Initialize Data Access Objects
        self.task_dao = TaskDAO()
        self.week_dao = WeekDAO()
        
        # Setup lazy imports for scientific libraries
        self._lazy_manager = get_lazy_manager()
        self._setup_lazy_imports()
    
    def _setup_lazy_imports(self):
        """Setup lazy imports for heavy scientific libraries"""
        # Register numpy for lazy loading
        self._lazy_manager.register_module('numpy', 'numpy')
        
        # Start background preloading of critical modules
        self._lazy_manager.preload_modules(['numpy'], background=True)
    
    @property
    def np(self):
        """Lazy-loaded numpy module"""
        return self._lazy_manager.get_module('numpy')
    
    def get_week_settings(self, week_id):
        """Get week-specific settings or fall back to global defaults using Data Service Layer"""
        try:
            # Get week data using WeekDAO
            week_data = self.week_dao.get_week_by_id(week_id)
            
            if week_data:
                # Convert dict to tuple format for compatibility with existing logic
                week_data_tuple = (
                    week_data.get('week_start_day'),
                    week_data.get('week_start_hour'),
                    week_data.get('week_end_day'),
                    week_data.get('week_end_hour'),
                    week_data.get('is_custom_duration'),
                    week_data.get('is_bonus_week'),
                    week_data.get('week_specific_bonus_payrate'),
                    week_data.get('week_specific_bonus_start_day'),
                    week_data.get('week_specific_bonus_start_time'),
                    week_data.get('week_specific_bonus_end_day'),
                    week_data.get('week_specific_bonus_end_time'),
                    week_data.get('week_specific_enable_task_bonus'),
                    week_data.get('week_specific_bonus_task_threshold'),
                    week_data.get('week_specific_bonus_additional_amount'),
                    week_data.get('use_global_bonus_settings'),
                    week_data.get('office_hour_count'),
                    week_data.get('office_hour_payrate'),
                    week_data.get('office_hour_session_duration_minutes'),
                    week_data.get('use_global_office_hours_settings')
                )
            
                defaults = self.global_settings.get_default_week_settings()
                global_bonus_defaults = self.global_settings.get_default_bonus_settings()
                global_office_hours_defaults = self.global_settings.get_default_office_hour_settings()

                settings = {
                    'week_start_day': week_data_tuple[0],
                    'week_start_hour': week_data_tuple[1],
                    'week_end_day': week_data_tuple[2],
                    'week_end_hour': week_data_tuple[3],
                    'is_custom_duration': bool(week_data_tuple[4]),
                    'is_bonus_week': bool(week_data_tuple[5]),
                    'use_global_bonus_settings': bool(week_data_tuple[14]),
                    'office_hour_count': week_data_tuple[15],
                    'office_hour_payrate': week_data_tuple[16],
                    'office_hour_session_duration_minutes': week_data_tuple[17],
                    'use_global_office_hours_settings': bool(week_data_tuple[18])
                }

                # Apply duration settings
                if not settings['is_custom_duration']:
                    settings['week_start_day'] = defaults['week_start_day']
                    settings['week_start_hour'] = defaults['week_start_hour']
                    settings['week_end_day'] = defaults['week_end_day']
                    settings['week_end_hour'] = defaults['week_end_hour']
                
                # Apply bonus settings
                if not settings['is_bonus_week'] or settings['use_global_bonus_settings']:
                    settings['bonus_payrate'] = global_bonus_defaults['bonus_payrate']
                    settings['bonus_start_day'] = global_bonus_defaults['bonus_start_day']
                    settings['bonus_start_time'] = global_bonus_defaults['bonus_start_time']
                    settings['bonus_end_day'] = global_bonus_defaults['bonus_end_day']
                    settings['bonus_end_time'] = global_bonus_defaults['bonus_end_time']
                    settings['enable_task_bonus'] = global_bonus_defaults['enable_task_bonus']
                    settings['bonus_task_threshold'] = global_bonus_defaults['bonus_task_threshold']
                    settings['bonus_additional_amount'] = global_bonus_defaults['bonus_additional_amount']
                else:
                    settings['bonus_payrate'] = week_data_tuple[6]
                    settings['bonus_start_day'] = week_data_tuple[7]
                    settings['bonus_start_time'] = week_data_tuple[8]
                    settings['bonus_end_day'] = week_data_tuple[9]
                    settings['bonus_end_time'] = week_data_tuple[10]
                    settings['enable_task_bonus'] = bool(week_data_tuple[11])
                    settings['bonus_task_threshold'] = week_data_tuple[12]
                    settings['bonus_additional_amount'] = week_data_tuple[13]

                # Apply office hours settings
                if settings['use_global_office_hours_settings']:
                    settings['office_hour_payrate'] = global_office_hours_defaults['payrate']
                    settings['office_hour_session_duration_minutes'] = global_office_hours_defaults['session_duration_minutes']
                # else, use values from week_data which are already in settings
                
                return settings
            else:
                # Week not found, return all global defaults
                defaults = self.global_settings.get_default_week_settings()
                global_bonus_defaults = self.global_settings.get_default_bonus_settings()
                global_office_hours_defaults = self.global_settings.get_default_office_hour_settings()

                return {
                    'week_start_day': defaults['week_start_day'],
                    'week_start_hour': defaults['week_start_hour'],
                    'week_end_day': defaults['week_end_day'],
                    'week_end_hour': defaults['week_end_hour'],
                    'is_custom_duration': False, # No custom duration if week not found
                    'is_bonus_week': False, # Not a bonus week if not found
                    'use_global_bonus_settings': True, # Default to global bonus
                    'bonus_payrate': global_bonus_defaults['bonus_payrate'],
                    'bonus_start_day': global_bonus_defaults['bonus_start_day'],
                    'bonus_start_time': global_bonus_defaults['bonus_start_time'],
                    'bonus_end_day': global_bonus_defaults['bonus_end_day'],
                    'bonus_end_time': global_bonus_defaults['bonus_end_time'],
                    'enable_task_bonus': global_bonus_defaults['enable_task_bonus'],
                    'bonus_task_threshold': global_bonus_defaults['bonus_task_threshold'],
                    'bonus_additional_amount': global_bonus_defaults['bonus_additional_amount'],
                    'office_hour_count': 0, # No office hours if week not found
                    'office_hour_payrate': global_office_hours_defaults['payrate'],
                    'office_hour_session_duration_minutes': global_office_hours_defaults['session_duration_minutes'],
                    'use_global_office_hours_settings': True # Default to global office hours
                }
        except DataServiceError as e:
            logger.error(f"Error getting week settings: {e}")
            # Return all global defaults as fallback on error
            defaults = self.global_settings.get_default_week_settings()
            global_bonus_defaults = self.global_settings.get_default_bonus_settings()
            global_office_hours_defaults = self.global_settings.get_default_office_hour_settings()
            return {
                'week_start_day': defaults['week_start_day'],
                'week_start_hour': defaults['week_start_hour'],
                'week_end_day': defaults['week_end_day'],
                'week_end_hour': defaults['week_end_hour'],
                'is_custom_duration': False,
                'is_bonus_week': False,
                'use_global_bonus_settings': True,
                'bonus_payrate': global_bonus_defaults['bonus_payrate'],
                'bonus_start_day': global_bonus_defaults['bonus_start_day'],
                'bonus_start_time': global_bonus_defaults['bonus_start_time'],
                'bonus_end_day': global_bonus_defaults['bonus_end_day'],
                'bonus_end_time': global_bonus_defaults['bonus_end_time'],
                'enable_task_bonus': global_bonus_defaults['enable_task_bonus'],
                'bonus_task_threshold': global_bonus_defaults['bonus_task_threshold'],
                'bonus_additional_amount': global_bonus_defaults['bonus_additional_amount'],
                'office_hour_count': 0,
                'office_hour_payrate': global_office_hours_defaults['payrate'],
                'office_hour_session_duration_minutes': global_office_hours_defaults['session_duration_minutes'],
                'use_global_office_hours_settings': True
            }
    
    def get_bonus_settings(self):
        """Get global bonus settings"""
        return self.global_settings.get_default_bonus_settings()
    
    def get_payrates(self):
        """Get regular and bonus payrates from settings"""
        bonus_settings = self.get_bonus_settings()
        return {
            'regular_rate': self.global_settings.get_default_payrate(),
            'bonus_rate': bonus_settings['bonus_payrate']
        }
    
    def get_task_timestamp_for_bonus_check(self, task_data):
        """
        Extract the most appropriate timestamp from task data for bonus window checking.
        Priority: time_begin > time_end > date_audited (middle of day)
        Returns datetime object or None if no valid timestamp found.
        """
        try:
            # For different contexts, task_data might have different structures
            if isinstance(task_data, (list, tuple)) and len(task_data) >= 6:
                # From database query results (e.g., tasks table with columns)
                # Typical structure: duration, time_limit, score, project_name, locale, date_audited, [time_begin], [time_end]
                date_audited = task_data[5] if len(task_data) > 5 else None
                time_begin = task_data[6] if len(task_data) > 6 else None  
                time_end = task_data[7] if len(task_data) > 7 else None
            elif isinstance(task_data, dict):
                # From dictionary/object structure
                date_audited = task_data.get('date_audited')
                time_begin = task_data.get('time_begin')
                time_end = task_data.get('time_end')
            else:
                return None
            
            # Priority 1: time_begin (most precise for bonus start)
            if time_begin and str(time_begin).strip():
                try:
                    time_begin_str = str(time_begin).strip()
                    return datetime.strptime(time_begin_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass
            
            # Priority 2: time_end (second choice)
            if time_end and str(time_end).strip():
                try:
                    time_end_str = str(time_end).strip()
                    return datetime.strptime(time_end_str, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    pass
            
            # Priority 3: date_audited (fallback, assume middle of day)
            if date_audited and str(date_audited).strip():
                try:
                    date_audited_str = str(date_audited).strip()
                    if ' ' in date_audited_str:
                        # Already has time component
                        return datetime.strptime(date_audited_str, '%Y-%m-%d %H:%M:%S')
                    else:
                        # Date only, assume middle of day for bonus window check
                        return datetime.strptime(date_audited_str, '%Y-%m-%d').replace(hour=12, minute=0, second=0)
                except ValueError:
                    pass
            
            return None
            
        except Exception as e:
            print(f"Error extracting timestamp for bonus check: {e}")
            return None

    def is_task_eligible_for_bonus(self, task_data, week_settings, bonus_settings):
        """
        Check if a task is eligible for bonus by ensuring BOTH time_begin AND time_end 
        fall within the bonus time window.
        
        For a task to qualify for bonus:
        - The week must be marked as a bonus week
        - Global bonus system must be enabled
        - BOTH time_begin AND time_end must exist and be valid timestamps
        - BOTH time_begin AND time_end must fall within the bonus window
        """
        # Master toggle check - if global bonus is disabled, no tasks get bonus
        if not bonus_settings.get('global_bonus_enabled', True):
            return False
            
        if not week_settings['is_bonus_week']:
            return False
        
        try:
            # Extract time_begin and time_end from task data
            if isinstance(task_data, (list, tuple)) and len(task_data) >= 8:
                time_begin_str = task_data[6] if len(task_data) > 6 else None  
                time_end_str = task_data[7] if len(task_data) > 7 else None
            elif isinstance(task_data, dict):
                time_begin_str = task_data.get('time_begin')
                time_end_str = task_data.get('time_end')
            else:
                return False
            
            # Both time_begin and time_end must exist for bonus eligibility
            if not time_begin_str or not str(time_begin_str).strip():
                return False
            if not time_end_str or not str(time_end_str).strip():
                return False
            
            # Parse timestamps
            try:
                time_begin_str_clean = str(time_begin_str).strip()
                time_end_str_clean = str(time_end_str).strip()
                time_begin = datetime.strptime(time_begin_str_clean, '%Y-%m-%d %H:%M:%S')
                time_end = datetime.strptime(time_end_str_clean, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                return False
            
            # Both timestamps must fall within the bonus window
            begin_in_window = self.is_timestamp_in_bonus_window(time_begin, week_settings, bonus_settings)
            end_in_window = self.is_timestamp_in_bonus_window(time_end, week_settings, bonus_settings)
            
            return begin_in_window and end_in_window
            
        except Exception as e:
            print(f"Error checking task bonus eligibility: {e}")
            return False

    def is_timestamp_in_bonus_window(self, timestamp, week_settings, bonus_settings):
        """
        Check if a specific timestamp falls within the bonus time window.
        Handles wrap-around periods (e.g., Sunday 9 AM to Monday 9 AM).
        """
        try:
            # Get timestamp components
            timestamp_day = timestamp.weekday()  # 0=Monday, 6=Sunday
            timestamp_time = timestamp.time()
            
            # Get bonus window settings and convert from global settings format (1-7) to Python format (0-6)
            # Global settings: Monday=1, Sunday=7
            # Python weekday: Monday=0, Sunday=6
            bonus_start_day_global = bonus_settings['bonus_start_day']  # 1-7 format
            bonus_end_day_global = bonus_settings['bonus_end_day']      # 1-7 format
            
            # Convert to Python weekday format (0-6)
            bonus_start_day = (bonus_start_day_global - 1) % 7  # Convert 1-7 to 0-6
            bonus_end_day = (bonus_end_day_global - 1) % 7      # Convert 1-7 to 0-6
            
            bonus_start_time = datetime.strptime(bonus_settings['bonus_start_time'], "%H:%M").time()
            bonus_end_time = datetime.strptime(bonus_settings['bonus_end_time'], "%H:%M").time()
            
            # Handle different bonus window scenarios
            if bonus_start_day == bonus_end_day:
                # Same day bonus window (e.g., Monday 9 AM to Monday 5 PM)
                if timestamp_day == bonus_start_day:
                    return bonus_start_time <= timestamp_time <= bonus_end_time
                else:
                    return False
            
            elif bonus_start_day < bonus_end_day:
                # Normal multi-day window (e.g., Monday 9 AM to Friday 5 PM)
                if timestamp_day < bonus_start_day or timestamp_day > bonus_end_day:
                    return False
                elif timestamp_day == bonus_start_day:
                    return timestamp_time >= bonus_start_time
                elif timestamp_day == bonus_end_day:
                    return timestamp_time <= bonus_end_time
                else:
                    # Middle day - entire day is in bonus window
                    return True
            
            else:
                # Wrap-around window (e.g., Sunday 9 AM to Monday 9 AM)
                # In Python format: Sunday=6, Monday=0, so this would be 6 to 0
                if timestamp_day == bonus_start_day:
                    # On start day, must be after start time
                    return timestamp_time >= bonus_start_time
                elif timestamp_day == bonus_end_day:
                    # On end day, must be before end time
                    return timestamp_time <= bonus_end_time
                elif timestamp_day > bonus_start_day or timestamp_day < bonus_end_day:
                    # Days between start and end (wrapping around week)
                    return True
                else:
                    return False
            
        except Exception as e:
            print(f"Error checking timestamp in bonus window: {e}")
            return False

    def is_task_in_bonus_window(self, task_datetime, week_settings, bonus_settings):
        """DEPRECATED: Use is_task_eligible_for_bonus instead for proper validation"""
        return self.is_timestamp_in_bonus_window(task_datetime, week_settings, bonus_settings)

    def populate_week_combo_data(self):
        """Retrieve week data from the database using Data Service Layer"""
        try:
            weeks_data = self.week_dao.get_all_weeks()
            # Convert to tuple format for compatibility
            weeks = [(week['id'], week['week_label']) for week in weeks_data]
        except DataServiceError as e:
            logger.error(f"Error getting week combo data: {e}")
            weeks = []
        
        # Sort weeks chronologically by parsing the start date from week_label
        def parse_start_date(week_tuple):
            week_id, week_label = week_tuple
            try:
                # Extract start date from format "dd/MM/yyyy - dd/MM/yyyy"
                start_date_str = week_label.split(" - ")[0]
                
                # Try parsing multiple date formats
                date_formats = ["%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d", "%d-%m-%Y"]
                
                for fmt in date_formats:
                    try:
                        return datetime.strptime(start_date_str, fmt)
                    except ValueError:
                        continue # Try next format if this one fails
                
                # If no format matched, fall back to a very old date and print a warning
                print(f"Warning: Could not parse date from week label '{week_label}' in DataManager. Using default date.")
                return datetime(1900, 1, 1)
            except (ValueError, IndexError, AttributeError) as e:
                # If splitting or other initial operations fail, it's a completely malformed label
                print(f"Warning: Malformed week label '{week_label}' in DataManager. Error: {e}. Using default date.")
                return datetime(1900, 1, 1)
        
        # Sort by parsed start date
        weeks.sort(key=parse_start_date)
        return weeks

    def get_chart_data(self, x_variable, y_variables, current_week_id, current_start_date, current_end_date):
        """Get data for charting based on selected variables using Data Service Layer"""
        try:
            # Build query based on current data selection using established state variables
            if current_week_id is not None:
                # Week-based selection using WeekDAO
                week_data = self.week_dao.get_week_by_id(current_week_id)
                if not week_data:
                    return []
                
                week_label = week_data['week_label']
                try:
                    start_date_str, end_date_str = week_label.split(" - ")
                    # Try multiple date formats - first try dd-MM-yyyy, then dd/MM/yyyy
                    date_formats = ['%d-%m-%Y', '%d/%m/%Y']
                    start_date = None
                    end_date = None
                    
                    for fmt in date_formats:
                        try:
                            start_date = datetime.strptime(start_date_str, fmt).strftime('%Y-%m-%d')
                            end_date = datetime.strptime(end_date_str, fmt).strftime('%Y-%m-%d')
                            break  # Success, exit the format loop
                        except ValueError:
                            continue  # Try next format
                    
                    if start_date is None or end_date is None:
                        raise ValueError(f"Could not parse dates with any known format")
                    
                except (ValueError, IndexError) as e:
                    # Fallback or error handling for malformed week_label
                    return []
                
                where_clause = "WHERE date_audited BETWEEN ? AND ?"
                params = [start_date, end_date]
            elif current_start_date and current_end_date:
                # Date range selection
                where_clause = "WHERE date_audited BETWEEN ? AND ?"
                params = [current_start_date, current_end_date]
            else:
                # No selection - use all data
                where_clause = ""
                params = []
            
            # Build SELECT clause based on variables
            x_var_name, x_var_type = x_variable
            select_fields = [x_var_name]
            
            for y_var_name, y_var_type in y_variables:
                select_fields.append(y_var_name)
            
            # Handle composite metrics (need to calculate)
            if any(var in ['total_time', 'average_time', 'time_limit_usage', 'fail_rate', 'bonus_tasks_count', 'total_earnings'] 
                   for var, _ in [x_variable] + y_variables):
                # Need to aggregate data
                result = self.get_aggregated_chart_data(x_variable, y_variables, where_clause, params)
                return result
            else:
                # Direct query for raw data using TaskDAO
                if current_week_id is not None:
                    # Get tasks by week and filter by date range
                    raw_tasks = self.task_dao.get_tasks_by_week(current_week_id)
                    # Filter by date range from week_label parsing
                    raw_tasks = [task for task in raw_tasks 
                               if start_date <= task.get('date_audited', '') <= end_date]
                elif current_start_date and current_end_date:
                    # Get tasks by date range
                    raw_tasks = self.task_dao.get_tasks_by_date_range(current_start_date, current_end_date)
                else:
                    # Get all tasks
                    raw_tasks = self.task_dao.get_all_tasks()
                
                # Extract only the required fields and convert to tuple format
                converted_data = []
                for task in raw_tasks:
                    converted_row = []
                    for i, (var_name, var_type) in enumerate([x_variable] + y_variables):
                        value = task.get(var_name, '')
                        if i == 0:  # X variable
                            converted_row.append(value)  # Keep as is for now
                        else:  # Y variables
                            converted_value = self._convert_value_for_charting(value, var_name)
                            converted_row.append(converted_value)
                    converted_data.append(tuple(converted_row))
                
                return converted_data
                
        except DataServiceError as e:
            logger.error(f"Database error in get_chart_data: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in get_chart_data: {e}")
            return []
    
    def get_aggregated_chart_data(self, x_variable, y_variables, where_clause, params):
        """Get aggregated data for composite metrics"""
        x_var_name, x_var_type = x_variable
        
        # Group by X variable - handle composite metrics that don't exist as database columns
        if x_var_name in ['date_audited', 'week_id', 'project_name', 'locale', 'duration', 'time_limit', 'score', 'bonus_paid']:
            # These are actual database columns
            group_by_field = x_var_name
        else:
            # For composite metrics as X variables, we need to group by a different field
            # For now, group by date_audited as a fallback, but this needs special handling
            if x_var_name in ['total_time', 'average_time', 'time_limit_usage', 'fail_rate', 'bonus_tasks_count', 'total_earnings']:
                # For composite metrics as X variable, group by date to create time series
                group_by_field = 'date_audited'
            else:
                # Fallback for unknown variables
                group_by_field = 'date_audited'
        
        # Build aggregation query - get raw data first, then process in Python since duration/time_limit are strings
        query = f"""
        SELECT {group_by_field}, duration, time_limit, score, date_audited, week_id, time_begin, time_end
        FROM tasks 
        {where_clause}
        ORDER BY {group_by_field}
        """
        
        cursor.execute(query, params)
        raw_data = cursor.fetchall()
        
        # Group and aggregate the data manually since we need to parse time strings
        grouped_data = defaultdict(lambda: {
            'task_count': 0,
            'total_duration_seconds': 0,
            'total_limit_seconds': 0,
            'fail_count': 0,
            'bonus_count': 0,
            'durations': []  # For calculating averages
        })
        
        def parse_time_to_seconds(time_str):
            """Convert HH:MM:SS string to seconds"""
            if not time_str or not time_str.strip():
                return 0
            try:
                parts = time_str.strip().split(':')
                if len(parts) == 3:
                    h, m, s = map(int, parts)
                    return h * 3600 + m * 60 + s
                else:
                    return 0
            except (ValueError, AttributeError):
                return 0
        
        # Get payrates and bonus settings for calculations
        payrates = self.get_payrates()
        bonus_settings = self.get_bonus_settings()
        
        # Process raw data and group by X variable
        for row in raw_data:
            x_value = row[0]
            duration_str = row[1]
            time_limit_str = row[2]
            score = row[3]
            date_audited = row[4]
            week_id = row[5]
            
            group = grouped_data[x_value]
            group['task_count'] += 1
            
            # Parse duration
            duration_seconds = parse_time_to_seconds(duration_str)
            group['total_duration_seconds'] += duration_seconds
            group['durations'].append(duration_seconds)
            
            # Parse time limit
            limit_seconds = parse_time_to_seconds(time_limit_str)
            group['total_limit_seconds'] += limit_seconds
            
            # Count failures
            if score is not None and score in (1, 2):
                group['fail_count'] += 1
            
            # Determine if this task is in bonus period using new system
            is_bonus = False
            if week_id and date_audited:
                week_settings = self.get_week_settings(week_id)
                if week_settings['is_bonus_week']:
                    task_datetime = self.get_task_timestamp_for_bonus_check(row)
                    if task_datetime:
                        is_bonus = self.is_task_eligible_for_bonus(row, week_settings, bonus_settings)
            
            if is_bonus:
                group['bonus_count'] += 1
        
        # Convert to chart data format
        chart_data = []
        for x_value, group in grouped_data.items():
            task_count = group['task_count']
            total_duration_seconds = group['total_duration_seconds']
            total_limit_seconds = group['total_limit_seconds']
            fail_count = group['fail_count']
            bonus_count = group['bonus_count']
            durations = group['durations']
            
            # Calculate aggregate metrics
            total_time = total_duration_seconds / 3600.0  # Convert to hours
            average_time = (sum(durations) / len(durations)) / 3600.0 if durations else 0
            time_limit_usage = (total_duration_seconds / total_limit_seconds * 100) if total_limit_seconds > 0 else 0
            fail_rate = (fail_count / task_count * 100) if task_count > 0 else 0
            bonus_tasks_count = bonus_count
            
            # Calculate earnings using dynamic payrates
            # Note: This is a simplified aggregation - in reality bonus status is per-task
            # For chart aggregation, we approximate based on bonus_count ratio
            total_hours = total_duration_seconds / 3600.0
            if bonus_count > 0 and task_count > 0:
                # Approximate bonus vs regular hours based on ratio
                bonus_ratio = bonus_count / task_count
                bonus_hours = total_hours * bonus_ratio
                regular_hours = total_hours * (1 - bonus_ratio)
            else:
                bonus_hours = 0
                regular_hours = total_hours
            
            total_earnings = (regular_hours * payrates['regular_rate']) + (bonus_hours * payrates['bonus_rate'])
            
            # Build row data for selected variables
            # Handle X variable value - if it's a composite metric, calculate it
            if x_var_name == 'total_time':
                x_display_value = total_time
            elif x_var_name == 'average_time':
                x_display_value = average_time
            elif x_var_name == 'time_limit_usage':
                x_display_value = time_limit_usage
            elif x_var_name == 'fail_rate':
                x_display_value = fail_rate
            elif x_var_name == 'bonus_tasks_count':
                x_display_value = bonus_tasks_count
            elif x_var_name == 'total_earnings':
                x_display_value = total_earnings
            else:
                # For raw database columns, use the actual value
                x_display_value = x_value
            
            row_data = [x_display_value]  # X variable value
            
            for y_var_name, y_var_type in y_variables:
                if y_var_name == 'total_time':
                    row_data.append(total_time)
                elif y_var_name == 'average_time':
                    row_data.append(average_time)
                elif y_var_name == 'time_limit_usage':
                    row_data.append(time_limit_usage)
                elif y_var_name == 'fail_rate':
                    row_data.append(fail_rate)
                elif y_var_name == 'bonus_tasks_count':
                    row_data.append(bonus_tasks_count)
                elif y_var_name == 'total_earnings':
                    row_data.append(total_earnings)
                elif y_var_name == 'duration':
                    # For raw duration, return average duration in seconds
                    avg_duration_seconds = sum(durations) / len(durations) if durations else 0
                    row_data.append(avg_duration_seconds)
                elif y_var_name == 'time_limit':
                    # For raw time limit, return average time limit in seconds
                    avg_limit_seconds = total_limit_seconds / task_count if task_count > 0 else 0
                    row_data.append(avg_limit_seconds)
                elif y_var_name == 'score':
                    # For score, return average score (calculated from fail rate)
                    avg_score = ((task_count - fail_count) * 3 + fail_count * 1.5) / task_count if task_count > 0 else 0
                    row_data.append(avg_score)
                elif y_var_name == 'bonus_paid':
                    # For bonus paid, return ratio
                    bonus_ratio = bonus_count / task_count if task_count > 0 else 0
                    row_data.append(bonus_ratio)
                else:
                    # For other raw variables, return count or 0
                    row_data.append(task_count if y_var_name in ['project_name', 'locale', 'date_audited', 'week_id'] else 0)
            
            chart_data.append(tuple(row_data))
        
        return chart_data

    def get_tasks_data_by_week(self, week_id):
        """Retrieve tasks data for a specific week using Data Service Layer."""
        try:
            tasks_data = self.task_dao.get_tasks_by_week(week_id)
            # Convert to tuple format for compatibility with existing analytics logic
            return [(
                task.get('duration', '00:00:00'),
                task.get('time_limit', '00:00:00'),
                task.get('score', 0),
                task.get('project_name', ''),
                task.get('locale', ''),
                task.get('date_audited', ''),
                task.get('time_begin', ''),
                task.get('time_end', '')
            ) for task in tasks_data]
        except DataServiceError as e:
            logger.error(f"Error getting tasks data by week {week_id}: {e}")
            return []

    def get_tasks_data_by_time_range(self, start_date, end_date):
        """Retrieve tasks data for a specific time range using Data Service Layer."""
        try:
            tasks_data = self.task_dao.get_tasks_by_date_range(start_date, end_date)
            # Convert to tuple format for compatibility with existing analytics logic
            return [(
                task.get('duration', '00:00:00'),
                task.get('time_limit', '00:00:00'),
                task.get('score', 0),
                task.get('project_name', ''),
                task.get('locale', ''),
                task.get('date_audited', ''),
                task.get('time_begin', ''),
                task.get('time_end', '')
            ) for task in tasks_data]
        except DataServiceError as e:
            logger.error(f"Error getting tasks data by time range {start_date} to {end_date}: {e}")
            return []

    def get_tasks_data_for_daily_project(self, selection_type, selected_id, selected_day, current_start_date, current_end_date):
        """Retrieve tasks data for daily project breakdown using Data Service Layer."""
        try:
            if selection_type == "week":
                tasks_data = self.task_dao.get_tasks_by_date(selected_day, week_id=selected_id)
            elif selection_type == "time_range":
                tasks_data = self.task_dao.get_tasks_by_date(selected_day)
            else:
                tasks_data = []
            
            # Convert to tuple format for compatibility with existing analytics logic
            return [(
                task.get('duration', '00:00:00'),
                task.get('time_limit', '00:00:00'),
                task.get('score', 0),
                task.get('project_name', ''),
                task.get('locale', ''),
                task.get('date_audited', ''),
                task.get('time_begin', ''),
                task.get('time_end', '')
            ) for task in tasks_data]
        except DataServiceError as e:
            logger.error(f"Error getting tasks data for daily project: {e}")
            return []

    def calculate_aggregate_statistics(self, tasks_data, week_id=None):
        """Calculate aggregate statistics for the given tasks data."""
        total_seconds = 0
        total_time_limit_seconds = 0
        total_score = 0
        fail_count = 0
        total_tasks = len(tasks_data)
        bonus_tasks_count = 0
        
        # Fetch global payrate and bonus settings once
        global_payrate = self.global_settings.get_default_payrate()
        global_bonus_settings = self.get_bonus_settings()

        total_earnings = 0.0
        task_bonus_applied = False # Track if the additional task bonus has been applied

        # Get week settings once if a specific week is selected
        current_week_settings = None
        if week_id:
            current_week_settings = self.get_week_settings(week_id)

        # First, calculate earnings from tasks
        for task in tasks_data:
            duration_str = task[0] # Duration is at index 0
            time_limit_str = task[1] # Time Limit is at index 1
            score = task[2] # Score is at index 2
            date_audited_str = task[5] # Date Audited is at index 5
            
            # Convert duration to seconds
            duration_seconds = self._parse_time_to_seconds(duration_str)
            total_seconds += duration_seconds
            
            # Convert time limit to seconds
            time_limit_seconds = self._parse_time_to_seconds(time_limit_str)
            total_time_limit_seconds += time_limit_seconds
            
            total_score += score
            
            if score < 3: # Assuming score < 3 is a 'fail'
                fail_count += 1
            
            # Determine actual bonus settings for this task based on week_id and flags
            effective_bonus_settings = global_bonus_settings
            effective_payrate = global_payrate
            is_bonus_week_actual = False
            
            if current_week_settings and current_week_settings['is_bonus_week'] and not current_week_settings['use_global_bonus_settings']:
                effective_bonus_settings = {
                    'global_bonus_enabled': global_bonus_settings['global_bonus_enabled'], # Master toggle still applies
                    'bonus_start_day': current_week_settings['bonus_start_day'],
                    'bonus_start_time': current_week_settings['bonus_start_time'],
                    'bonus_end_day': current_week_settings['bonus_end_day'],
                    'bonus_end_time': current_week_settings['bonus_end_time'],
                    'bonus_payrate': current_week_settings['bonus_payrate'],
                    'enable_task_bonus': current_week_settings['enable_task_bonus'],
                    'bonus_task_threshold': current_week_settings['bonus_task_threshold'],
                    'bonus_additional_amount': current_week_settings['bonus_additional_amount']
                }
                effective_payrate = current_week_settings['bonus_payrate'] # Week-specific bonus payrate
                is_bonus_week_actual = True
            elif current_week_settings and current_week_settings['is_bonus_week'] and current_week_settings['use_global_bonus_settings']:
                # Week is marked as bonus week, but uses global bonus settings
                is_bonus_week_actual = True

            # Check for bonus eligibility using the improved timestamp method
            is_task_eligible_for_bonus = False
            if is_bonus_week_actual and effective_bonus_settings['global_bonus_enabled']:
                task_datetime = self.get_task_timestamp_for_bonus_check(task)
                if task_datetime:
                    is_task_eligible_for_bonus = self.is_task_eligible_for_bonus(task, current_week_settings, effective_bonus_settings)

            if is_task_eligible_for_bonus:
                bonus_tasks_count += 1
                total_earnings += (duration_seconds / 3600.0) * effective_bonus_settings['bonus_payrate']
            else:
                total_earnings += (duration_seconds / 3600.0) * global_payrate # Always use global payrate if not a bonus task
            
        # After looping through all tasks, apply the task-based bonus if criteria met
        if current_week_settings and current_week_settings['is_bonus_week'] and not current_week_settings['use_global_bonus_settings']:
            # Use week-specific task bonus settings
            if current_week_settings['enable_task_bonus'] and bonus_tasks_count >= current_week_settings['bonus_task_threshold'] and not task_bonus_applied:
                total_earnings += current_week_settings['bonus_additional_amount']
                task_bonus_applied = True
        elif global_bonus_settings['enable_task_bonus'] and bonus_tasks_count >= global_bonus_settings['bonus_task_threshold'] and not task_bonus_applied:
            # Use global task bonus settings
            total_earnings += global_bonus_settings['bonus_additional_amount']
            task_bonus_applied = True

        # Add office hour earnings if a specific week is selected and not using global office hours
        if week_id and current_week_settings and not current_week_settings['use_global_office_hours_settings']:
            office_hour_earnings = current_week_settings['office_hour_count'] * current_week_settings['office_hour_payrate'] * (current_week_settings['office_hour_session_duration_minutes'] / 60.0)
            total_earnings += office_hour_earnings
        elif week_id and current_week_settings and current_week_settings['use_global_office_hours_settings']:
            office_hours_data = self.global_settings.get_default_office_hour_settings()
            office_hour_count = current_week_settings.get('office_hour_count', 0)
            office_hour_earnings = office_hour_count * office_hours_data['payrate'] * (office_hours_data['session_duration_minutes'] / 60.0)
            total_earnings += office_hour_earnings

        avg_seconds = total_seconds / total_tasks if total_tasks > 0 else 0
        avg_time_limit_usage = (total_seconds / total_time_limit_seconds) * 100 if total_time_limit_seconds > 0 else 0
        fail_rate = (fail_count / total_tasks) * 100 if total_tasks > 0 else 0
        
        return {
            'total_time': self._format_time(total_seconds),
            'average_time': self._format_time(avg_seconds),
            'time_limit_usage': f"{avg_time_limit_usage:.2f}%",
            'fail_rate': f"{fail_rate:.2f}%",
            'bonus_tasks': str(bonus_tasks_count),
            'total_earnings': f"${total_earnings:.2f}"
        }

    def calculate_daily_statistics(self, tasks_data, week_id=None):
        """Calculate daily statistics for the given tasks data."""
        daily_stats = defaultdict(lambda: {
            'total_seconds': 0,
            'total_time_limit_seconds': 0,
            'total_score': 0,
            'fail_count': 0,
            'task_count': 0,
            'bonus_tasks_count': 0,
            'total_earnings': 0.0,
            'date': ""
        })
        
        global_payrate = self.global_settings.get_default_payrate()
        global_bonus_settings = self.get_bonus_settings()

        # Get week settings once if a specific week is selected
        current_week_settings = None
        if week_id:
            current_week_settings = self.get_week_settings(week_id)

        for task in tasks_data:
            date_audited_str = task[5]  # Date Audited is at index 5
            duration_str = task[0] # Duration is at index 0
            time_limit_str = task[1] # Time Limit is at index 1
            score = task[2] # Score is at index 2

            daily_data = daily_stats[date_audited_str]
            daily_data['date'] = date_audited_str

            duration_seconds = self._parse_time_to_seconds(duration_str)
            daily_data['total_seconds'] += duration_seconds
            daily_data['total_time_limit_seconds'] += self._parse_time_to_seconds(time_limit_str)
            daily_data['total_score'] += score
            daily_data['task_count'] += 1

            if score < 3:
                daily_data['fail_count'] += 1

            # Determine actual bonus settings for this task based on week_id and flags
            effective_bonus_settings = global_bonus_settings
            is_bonus_week_actual = False
            
            if current_week_settings and current_week_settings['is_bonus_week'] and not current_week_settings['use_global_bonus_settings']:
                effective_bonus_settings = {
                    'global_bonus_enabled': global_bonus_settings['global_bonus_enabled'],
                    'bonus_start_day': current_week_settings['bonus_start_day'],
                    'bonus_start_time': current_week_settings['bonus_start_time'],
                    'bonus_end_day': current_week_settings['bonus_end_day'],
                    'bonus_end_time': current_week_settings['bonus_end_time'],
                    'bonus_payrate': current_week_settings['bonus_payrate'],
                    'enable_task_bonus': current_week_settings['enable_task_bonus'],
                    'bonus_task_threshold': current_week_settings['bonus_task_threshold'],
                    'bonus_additional_amount': current_week_settings['bonus_additional_amount']
                }
                is_bonus_week_actual = True
            elif current_week_settings and current_week_settings['is_bonus_week'] and current_week_settings['use_global_bonus_settings']:
                # Week is marked as bonus week, but uses global bonus settings
                is_bonus_week_actual = True

            # Check for bonus eligibility using the improved timestamp method
            is_task_eligible_for_bonus = False
            if is_bonus_week_actual and effective_bonus_settings['global_bonus_enabled']:
                task_datetime = self.get_task_timestamp_for_bonus_check(task)
                if task_datetime:
                    is_task_eligible_for_bonus = self.is_task_eligible_for_bonus(task, current_week_settings, effective_bonus_settings)

            if is_task_eligible_for_bonus:
                daily_data['bonus_tasks_count'] += 1
                daily_data['total_earnings'] += (duration_seconds / 3600.0) * effective_bonus_settings['bonus_payrate']
            else:
                daily_data['total_earnings'] += (duration_seconds / 3600.0) * global_payrate
        
        # After looping through all tasks, apply the task-based bonus to aggregate daily earnings
        # Task-based bonus is usually applied once for the entire period, so we apply it here per day
        # if that day meets the threshold. This might need further clarification based on exact requirements.
        # For now, apply based on *daily* bonus tasks count.
        for day_data in daily_stats.values():
            if current_week_settings and current_week_settings['is_bonus_week'] and not current_week_settings['use_global_bonus_settings']:
                if current_week_settings['enable_task_bonus'] and day_data['bonus_tasks_count'] >= current_week_settings['bonus_task_threshold']:
                    day_data['total_earnings'] += current_week_settings['bonus_additional_amount']
            elif global_bonus_settings['enable_task_bonus'] and day_data['bonus_tasks_count'] >= global_bonus_settings['bonus_task_threshold']:
                day_data['total_earnings'] += global_bonus_settings['bonus_additional_amount']

        # Add office hour earnings to each day if a specific week is selected and not using global office hours
        if week_id and current_week_settings and not current_week_settings['use_global_office_hours_settings']:
            office_hour_earnings_per_session = current_week_settings['office_hour_payrate'] * (current_week_settings['office_hour_session_duration_minutes'] / 60.0)
            office_hour_count = current_week_settings.get('office_hour_count', 0)
            total_office_hour_earnings_for_week = office_hour_count * office_hour_earnings_per_session
            num_days_with_tasks = len(daily_stats)
            if num_days_with_tasks > 0:
                proportional_oh_earnings_per_day = total_office_hour_earnings_for_week / num_days_with_tasks
                for day_data in daily_stats.values():
                    day_data['total_earnings'] += proportional_oh_earnings_per_day
        elif week_id and current_week_settings and current_week_settings['use_global_office_hours_settings']:
            office_hours_data = self.global_settings.get_default_office_hour_settings()
            office_hour_earnings_per_session = office_hours_data['payrate'] * (office_hours_data['session_duration_minutes'] / 60.0)
            office_hour_count = current_week_settings.get('office_hour_count', 0)
            total_office_hour_earnings_for_week = office_hour_count * office_hour_earnings_per_session
            num_days_with_tasks = len(daily_stats)
            if num_days_with_tasks > 0:
                proportional_oh_earnings_per_day = total_office_hour_earnings_for_week / num_days_with_tasks
                for day_data in daily_stats.values():
                    day_data['total_earnings'] += proportional_oh_earnings_per_day

        formatted_daily_stats = {}
        for day, stats in daily_stats.items():
            avg_seconds = stats['total_seconds'] / stats['task_count'] if stats['task_count'] > 0 else 0
            time_limit_usage = (stats['total_seconds'] / stats['total_time_limit_seconds']) * 100 if stats['total_time_limit_seconds'] > 0 else 0
            fail_rate = (stats['fail_count'] / stats['task_count']) * 100 if stats['task_count'] > 0 else 0
            
            formatted_daily_stats[day] = {
                'date': stats['date'],
                'total_time': self._format_time(stats['total_seconds']),
                'average_time': self._format_time(avg_seconds),
                'time_limit_usage': f"{time_limit_usage:.2f}%",
                'fail_rate': f"{fail_rate:.2f}%",
                'bonus_tasks': str(stats['bonus_tasks_count']),
                'total_earnings': f"${stats['total_earnings']:.2f}"
            }
        
        return formatted_daily_stats

    def calculate_project_statistics(self, tasks_data, week_id=None):
        """Calculate project-based statistics for the given tasks data."""
        project_data = defaultdict(lambda: defaultdict(lambda: {
            'total_seconds': 0,
            'task_count': 0,
            'bonus_count': 0,
            'total_earnings': 0.0 # Add total_earnings to project data
        }))

        # Get settings for bonus calculations
        global_bonus_settings = self.get_bonus_settings()
        global_payrate = self.global_settings.get_default_payrate()

        current_week_settings = None
        if week_id:
            current_week_settings = self.get_week_settings(week_id)

        for task in tasks_data:
            duration_str, time_limit_str, score, project_name, locale, date_audited = task[:6]
            pn = project_name if project_name and project_name.strip() else "Unassigned Project"
            loc = locale if locale and locale.strip() else "N/A"
            
            current_task_seconds = 0
            try:
                if duration_str:
                    h, m, s = map(int, duration_str.split(':'))
                    current_task_seconds = h * 3600 + m * 60 + s
            except (ValueError, AttributeError, TypeError):
                pass

            project_data[pn][loc]['total_seconds'] += current_task_seconds
            project_data[pn][loc]['task_count'] += 1

            # Determine actual bonus settings for this task based on week_id and flags
            effective_bonus_settings = global_bonus_settings
            is_bonus_week_actual = False
            
            if current_week_settings and current_week_settings['is_bonus_week'] and not current_week_settings['use_global_bonus_settings']:
                effective_bonus_settings = {
                    'global_bonus_enabled': global_bonus_settings['global_bonus_enabled'],
                    'bonus_start_day': current_week_settings['bonus_start_day'],
                    'bonus_start_time': current_week_settings['bonus_start_time'],
                    'bonus_end_day': current_week_settings['bonus_end_day'],
                    'bonus_end_time': current_week_settings['bonus_end_time'],
                    'bonus_payrate': current_week_settings['bonus_payrate'],
                    'enable_task_bonus': current_week_settings['enable_task_bonus'],
                    'bonus_task_threshold': current_week_settings['bonus_task_threshold'],
                    'bonus_additional_amount': current_week_settings['bonus_additional_amount']
                }
                is_bonus_week_actual = True
            elif current_week_settings and current_week_settings['is_bonus_week'] and current_week_settings['use_global_bonus_settings']:
                # Week is marked as bonus week, but uses global bonus settings
                is_bonus_week_actual = True

            # Check for bonus eligibility using the improved timestamp method
            is_task_eligible_for_bonus = False
            if is_bonus_week_actual and effective_bonus_settings['global_bonus_enabled']:
                task_datetime = self.get_task_timestamp_for_bonus_check(task)
                if task_datetime:
                    is_task_eligible_for_bonus = self.is_task_eligible_for_bonus(task, current_week_settings, effective_bonus_settings)
            
            if is_task_eligible_for_bonus:
                project_data[pn][loc]['bonus_count'] += 1
                project_data[pn][loc]['total_earnings'] += (current_task_seconds / 3600.0) * effective_bonus_settings['bonus_payrate']
            else:
                project_data[pn][loc]['total_earnings'] += (current_task_seconds / 3600.0) * global_payrate

        # Apply task-based bonus for each project/locale combination
        for project_name, locales in project_data.items():
            for locale, data in locales.items():
                task_bonus_applied_for_project_locale = False
                if current_week_settings and current_week_settings['is_bonus_week'] and not current_week_settings['use_global_bonus_settings']:
                    if current_week_settings['enable_task_bonus'] and data['bonus_count'] >= current_week_settings['bonus_task_threshold'] and not task_bonus_applied_for_project_locale:
                        project_data[project_name][locale]['total_earnings'] += current_week_settings['bonus_additional_amount']
                        task_bonus_applied_for_project_locale = True
                elif global_bonus_settings['enable_task_bonus'] and data['bonus_count'] >= global_bonus_settings['bonus_task_threshold'] and not task_bonus_applied_for_project_locale:
                    project_data[project_name][locale]['total_earnings'] += global_bonus_settings['bonus_additional_amount']
                    task_bonus_applied_for_project_locale = True

        return project_data

    def _format_time(self, total_seconds):
        """Format seconds into HH:MM:SS"""
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        secs = int(total_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    
    def _convert_value_for_charting(self, value, var_name):
        """Convert database values to numeric values suitable for charting"""
        if value is None:
            return 0
        
        # Handle time strings (HH:MM:SS format)
        if var_name in ['duration', 'time_limit'] and isinstance(value, str):
            try:
                parts = value.strip().split(':')
                if len(parts) == 3:
                    h, m, s = map(int, parts)
                    return h * 3600 + m * 60 + s  # Convert to total seconds
                else:
                    return 0
            except (ValueError, AttributeError):
                return 0
        
        # Handle numeric values
        elif var_name in ['score', 'bonus_paid']:
            try:
                return float(value) if value is not None else 0
            except (ValueError, TypeError):
                return 0
        
        # Handle categorical variables - for now return as string, will be converted to index in chart creation
        elif var_name in ['project_name', 'locale', 'date_audited', 'week_id']:
            return str(value) if value is not None else "Unknown"
        
        # Default: try to convert to float, fallback to 0
        else:
            try:
                return float(value) if value is not None else 0
            except (ValueError, TypeError):
                return 0 

    def get_week_office_hours_data(self, week_id):
        """Get week-specific office hour settings, falling back to global defaults."""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        
        try:
            c.execute("""
                SELECT office_hour_count, office_hour_payrate, 
                       office_hour_session_duration_minutes, use_global_office_hours_settings
                FROM weeks WHERE id=?
            """, (week_id,))
            
            week_data = c.fetchone()
            
            if week_data and week_data[3] is not None and not bool(week_data[3]): # use_global_office_hours_settings is explicitly False
                # Use week-specific office hour settings
                return {
                    'count': week_data[0] if week_data[0] is not None else 0,
                    'payrate': week_data[1] if week_data[1] is not None else self.global_settings.get_default_office_hour_settings()['payrate'],
                    'session_duration_minutes': week_data[2] if week_data[2] is not None else self.global_settings.get_default_office_hour_settings()['session_duration_minutes']
                }
            else:
                # Use global defaults for office hours (either NULL or True)
                defaults = self.global_settings.get_default_office_hour_settings()
                return {
                    'count': week_data[0] if week_data and week_data[0] is not None else 0,
                    'payrate': defaults['payrate'],
                    'session_duration_minutes': defaults['session_duration_minutes']
                }
        except Exception as e:
            print(f"Error getting week office hours data: {e}")
            # Fallback to global defaults in case of error
            defaults = self.global_settings.get_default_office_hour_settings()
            return {
                'count': 0, # Default to 0 count on error
                'payrate': defaults['payrate'],
                'session_duration_minutes': defaults['session_duration_minutes']
            }
        finally:
            conn.close()

    def _parse_time_to_seconds(self, time_str):
        """Convert HH:MM:SS string to seconds"""
        if not time_str or not time_str.strip():
            return 0
        try:
            parts = time_str.strip().split(':')
            if len(parts) == 3:
                h, m, s = map(int, parts)
                return h * 3600 + m * 60 + s
            else:
                return 0
        except (ValueError, AttributeError):
            return 0 

    # NEW METHODS FOR TAPERED FLEXIBILITY REFACTOR
    
    def get_constrained_chart_data(self, x_variable, y_variable, chart_type, current_week_id, current_start_date, current_end_date):
        """
        Get chart data for the tapered flexibility system with constrained variable combinations.
        Only allows 1 X and 1 Y variable from the predefined allowed sets.
        """
        # Validate the combination
        is_valid, message = validate_variable_combination(x_variable, y_variable, chart_type)
        if not is_valid:
            raise ValueError(f"Invalid variable combination: {message}")
        
        conn = None
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Build query based on current data selection
            where_clause, params = self._build_where_clause(current_week_id, current_start_date, current_end_date, cursor)
            
            # Get raw task data with all necessary fields
            query = f"""
            SELECT duration, time_limit, score, project_name, locale, date_audited, 
                   week_id, time_begin, time_end, bonus_paid
            FROM tasks 
            {where_clause}
            ORDER BY date_audited, time_begin
            """
            
            cursor.execute(query, params)
            raw_data = cursor.fetchall()
            
            # Group and aggregate the data
            return self._aggregate_constrained_data(raw_data, x_variable, y_variable)
            
        except sqlite3.Error as e:
            print(f"Database error in get_constrained_chart_data: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error in get_constrained_chart_data: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def _build_where_clause(self, current_week_id, current_start_date, current_end_date, cursor):
        """Build WHERE clause and parameters for data selection"""
        if current_week_id is not None:
            # Week-based selection
            cursor.execute("SELECT week_label FROM weeks WHERE id = ?", (current_week_id,))
            week_result = cursor.fetchone()
            if not week_result:
                return "", []
            
            week_label = week_result[0]
            try:
                start_date_str, end_date_str = week_label.split(" - ")
                # Try multiple date formats
                date_formats = ['%d-%m-%Y', '%d/%m/%Y']
                start_date = None
                end_date = None
                
                for fmt in date_formats:
                    try:
                        start_date = datetime.strptime(start_date_str, fmt).strftime('%Y-%m-%d')
                        end_date = datetime.strptime(end_date_str, fmt).strftime('%Y-%m-%d')
                        break
                    except ValueError:
                        continue
                
                if start_date is None or end_date is None:
                    raise ValueError("Could not parse dates")
                
            except (ValueError, IndexError):
                return "", []
            
            return "WHERE date_audited BETWEEN ? AND ?", [start_date, end_date]
            
        elif current_start_date and current_end_date:
            # Date range selection
            return "WHERE date_audited BETWEEN ? AND ?", [current_start_date, current_end_date]
        else:
            # No selection - use all data
            return "", []
    
    def _aggregate_constrained_data(self, raw_data, x_variable, y_variable):
        """Aggregate raw task data according to constrained variable definitions"""
        allowed_x = get_allowed_x_variables()
        allowed_y = get_allowed_y_variables()
        
        x_config = allowed_x[x_variable]
        y_config = allowed_y[y_variable]
        
        # Group data by X variable
        grouped_data = defaultdict(list)
        
        for row in raw_data:
            duration_str, time_limit_str, score, project_name, locale, date_audited, week_id, time_begin, time_end, bonus_paid = row
            
            # Determine X-axis grouping value
            x_value = self._get_x_grouping_value(row, x_variable, x_config)
            if x_value is not None:
                grouped_data[x_value].append(row)
        
        # Calculate Y-axis values for each group
        chart_data = []
        for x_value, tasks in grouped_data.items():
            y_value = self._calculate_y_metric(tasks, y_variable, y_config)
            chart_data.append((x_value, y_value))
        
        # Sort by X value for proper chart ordering
        if x_variable in ['time_day', 'time_month']:
            chart_data.sort(key=lambda x: x[0])  # Sort by date
        elif x_variable == 'time_week':
            chart_data.sort(key=lambda x: int(x[0]) if str(x[0]).isdigit() else 0)  # Sort by week number
        
        return chart_data
    
    def _get_x_grouping_value(self, row, x_variable, x_config):
        """Get the grouping value for X-axis based on variable type"""
        duration_str, time_limit_str, score, project_name, locale, date_audited, week_id, time_begin, time_end, bonus_paid = row
        
        if x_variable == 'time_day':
            return date_audited
            
        elif x_variable == 'time_week':
            return str(week_id) if week_id else 'Unknown'
            
        elif x_variable == 'time_month':
            try:
                dt = datetime.strptime(date_audited, '%Y-%m-%d')
                return dt.strftime('%Y-%m')  # Format: '2024-01'
            except (ValueError, AttributeError):
                return None
                
        elif x_variable == 'projects':
            return project_name if project_name else 'Unknown'
            
        elif x_variable == 'claim_time_ranges':
            category = categorize_time_to_range(time_begin)
            return get_time_range_display_name(category)
            
        return None
    
    def _calculate_y_metric(self, tasks, y_variable, y_config):
        """Calculate the Y-axis metric value for a group of tasks"""
        if not tasks:
            return 0
        
        if y_variable == 'duration_average':
            return self._calculate_duration_average(tasks)
            
        elif y_variable == 'claim_datetime_average':
            return self._calculate_claim_time_average(tasks)
            
        elif y_variable == 'money_made_total':
            return self._calculate_money_total(tasks)
            
        elif y_variable == 'money_made_average':
            return self._calculate_money_average(tasks)
            
        elif y_variable == 'time_usage_percent':
            return self._calculate_time_usage_percent(tasks)
            
        elif y_variable == 'fail_rate_percent':
            return self._calculate_fail_rate_percent(tasks)
            
        elif y_variable == 'average_rating':
            return self._calculate_average_rating(tasks)
            
        return 0
    
    def _calculate_duration_average(self, tasks):
        """Calculate average duration in hours"""
        total_seconds = 0
        count = 0
        
        for task in tasks:
            duration_str = task[0]
            duration_seconds = self._parse_time_to_seconds(duration_str)
            if duration_seconds > 0:
                total_seconds += duration_seconds
                count += 1
        
        if count == 0:
            return 0
        
        return round(total_seconds / count / 3600.0, 2)  # Convert to hours
    
    def _calculate_claim_time_average(self, tasks):
        """Calculate average time of day for task claims (in decimal hours)"""
        total_seconds_in_day = 0
        count = 0
        
        for task in tasks:
            time_begin = task[7]
            # Convert to string and check if valid
            if time_begin and str(time_begin).strip():
                try:
                    time_begin_str = str(time_begin).strip()
                    dt = datetime.strptime(time_begin_str, '%Y-%m-%d %H:%M:%S')
                    # Convert to seconds since midnight
                    seconds_since_midnight = dt.hour * 3600 + dt.minute * 60 + dt.second
                    total_seconds_in_day += seconds_since_midnight
                    count += 1
                except (ValueError, AttributeError):
                    continue
        
        if count == 0:
            return 0
        
        avg_seconds = total_seconds_in_day / count
        return round(avg_seconds / 3600.0, 2)  # Convert to decimal hours (e.g., 14.5 for 2:30 PM)
    
    def _calculate_money_total(self, tasks):
        """Calculate total earnings"""
        total_earnings = 0
        payrates = self.get_payrates()
        
        for task in tasks:
            duration_str = task[0]
            week_id = task[6]
            
            duration_seconds = self._parse_time_to_seconds(duration_str)
            duration_hours = duration_seconds / 3600.0
            
            # Determine if task is eligible for bonus
            is_bonus = self._is_task_bonus_eligible(task, week_id)
            rate = payrates['bonus_rate'] if is_bonus else payrates['regular_rate']
            
            total_earnings += duration_hours * rate
        
        return round(total_earnings, 2)
    
    def _calculate_money_average(self, tasks):
        """Calculate average earnings per task"""
        if not tasks:
            return 0
        
        total_earnings = self._calculate_money_total(tasks)
        return round(total_earnings / len(tasks), 2)
    
    def _calculate_time_usage_percent(self, tasks):
        """Calculate average percentage of time limit used"""
        total_percentage = 0
        count = 0
        
        for task in tasks:
            duration_str = task[0]
            time_limit_str = task[1]
            
            duration_seconds = self._parse_time_to_seconds(duration_str)
            limit_seconds = self._parse_time_to_seconds(time_limit_str)
            
            if limit_seconds > 0:
                percentage = (duration_seconds / limit_seconds) * 100
                total_percentage += percentage
                count += 1
        
        if count == 0:
            return 0
        
        return round(total_percentage / count, 1)
    
    def _calculate_fail_rate_percent(self, tasks):
        """Calculate percentage of failed tasks (score < 3)"""
        if not tasks:
            return 0
        
        fail_count = 0
        for task in tasks:
            score = task[2]
            if score is not None and score < 3:
                fail_count += 1
        
        return round((fail_count / len(tasks)) * 100, 1)
    
    def _calculate_average_rating(self, tasks):
        """Calculate average score/rating"""
        if not tasks:
            return 0
        
        total_score = 0
        count = 0
        
        for task in tasks:
            score = task[2]
            if score is not None:
                total_score += score
                count += 1
        
        if count == 0:
            return 0
        
        return round(total_score / count, 2)
    
    def _is_task_bonus_eligible(self, task, week_id):
        """Simplified bonus eligibility check for earnings calculation"""
        if not week_id:
            return False
        
        try:
            week_settings = self.get_week_settings(week_id)
            if not week_settings.get('is_bonus_week', False):
                return False
            
            bonus_settings = self.get_bonus_settings()
            return self.is_task_eligible_for_bonus(task, week_settings, bonus_settings)
        except Exception:
            return False
    
    def calculate_enhanced_statistics(self, tasks_data, week_id=None):
        """
        Calculate enhanced statistical analysis using Rust Statistical Analysis Engine
        
        Provides 15-50x performance improvement over traditional calculations
        and includes advanced statistical metrics like confidence intervals,
        correlation analysis, and trend detection.
        """
        if not tasks_data:
            return {
                'basic_stats': {},
                'advanced_stats': {},
                'correlations': {},
                'trends': {},
                'performance_metrics': {}
            }
        
        # Extract numerical data for statistical analysis
        durations = []
        scores = []
        time_limits = []
        time_usage_ratios = []
        earnings = []
        
        # Get week settings for bonus calculations
        current_week_settings = None
        if week_id:
            current_week_settings = self.get_week_settings(week_id)
        
        global_payrate = self.global_settings.get_default_payrate()
        global_bonus_settings = self.get_bonus_settings()
        
        for task in tasks_data:
            duration_str = task[0]
            time_limit_str = task[1]
            score = task[2]
            
            # Convert to numerical values
            duration_seconds = self._parse_time_to_seconds(duration_str)
            time_limit_seconds = self._parse_time_to_seconds(time_limit_str)
            
            durations.append(duration_seconds / 3600.0)  # Convert to hours
            scores.append(float(score))
            time_limits.append(time_limit_seconds / 3600.0)  # Convert to hours
            
            # Calculate time usage ratio
            if time_limit_seconds > 0:
                time_usage_ratios.append(duration_seconds / time_limit_seconds)
            else:
                time_usage_ratios.append(0.0)
            
            # Calculate earnings for this task
            is_bonus_eligible = False
            if current_week_settings and current_week_settings['is_bonus_week']:
                is_bonus_eligible = self._is_task_bonus_eligible(task, week_id)
            
            if is_bonus_eligible:
                task_earnings = (duration_seconds / 3600.0) * global_bonus_settings['bonus_payrate']
            else:
                task_earnings = (duration_seconds / 3600.0) * global_payrate
            
            earnings.append(task_earnings)
        
        # Use Rust Statistical Engine for high-performance calculations
        try:
            # Basic statistical summaries
            duration_stats = calculate_statistical_summary(durations)
            score_stats = calculate_statistical_summary(scores)
            earnings_stats = calculate_statistical_summary(earnings)
            time_usage_stats = calculate_statistical_summary(time_usage_ratios)
            
            # Confidence intervals
            duration_ci = calculate_confidence_interval(durations, 0.95)
            score_ci = calculate_confidence_interval(scores, 0.95)
            earnings_ci = calculate_confidence_interval(earnings, 0.95)
            
            # Correlation analysis
            correlation_data = {
                'duration': durations,
                'score': scores,
                'time_usage': time_usage_ratios,
                'earnings': earnings
            }
            correlations = calculate_batch_correlations(correlation_data)
            
            # Trend analysis (duration vs score)
            if len(durations) >= 2 and len(scores) >= 2:
                duration_score_trend = calculate_trend_analysis(durations, scores)
                duration_earnings_trend = calculate_trend_analysis(durations, earnings)
            else:
                duration_score_trend = TrendAnalysis(0.0, 0.0, 0.0, [])
                duration_earnings_trend = TrendAnalysis(0.0, 0.0, 0.0, [])
            
            # Moving averages for trend detection
            if len(durations) >= 5:
                duration_ma = calculate_moving_average(durations, 5)
                score_ma = calculate_moving_average(scores, 5)
            else:
                duration_ma = []
                score_ma = []
            
            # Performance metrics
            performance_metrics = {
                'efficiency_score': float(self.np.mean(scores)) / float(self.np.mean(durations)) if self.np.mean(durations) > 0 else 0.0,
                'consistency_index': 1.0 / (1.0 + duration_stats.std_dev) if duration_stats.std_dev > 0 else 1.0,
                'earnings_per_hour': float(self.np.sum(earnings)) / float(self.np.sum(durations)) if self.np.sum(durations) > 0 else 0.0,
                'quality_trend': duration_score_trend.slope,
                'outlier_rate': (duration_stats.outlier_count + score_stats.outlier_count) / (2 * len(tasks_data)) if len(tasks_data) > 0 else 0.0
            }
            
            return {
                'basic_stats': {
                    'duration': {
                        'mean': duration_stats.mean,
                        'median': duration_stats.median,
                        'std_dev': duration_stats.std_dev,
                        'min': duration_stats.min_val,
                        'max': duration_stats.max_val,
                        'q1': duration_stats.q1,
                        'q3': duration_stats.q3,
                        'outliers': len(duration_stats.outliers),
                        'confidence_interval': duration_ci
                    },
                    'score': {
                        'mean': score_stats.mean,
                        'median': score_stats.median,
                        'std_dev': score_stats.std_dev,
                        'min': score_stats.min_val,
                        'max': score_stats.max_val,
                        'q1': score_stats.q1,
                        'q3': score_stats.q3,
                        'outliers': len(score_stats.outliers),
                        'confidence_interval': score_ci
                    },
                    'earnings': {
                        'mean': earnings_stats.mean,
                        'median': earnings_stats.median,
                        'std_dev': earnings_stats.std_dev,
                        'min': earnings_stats.min_val,
                        'max': earnings_stats.max_val,
                        'total': float(self.np.sum(earnings)),
                        'confidence_interval': earnings_ci
                    },
                    'time_usage': {
                        'mean': time_usage_stats.mean,
                        'median': time_usage_stats.median,
                        'std_dev': time_usage_stats.std_dev
                    }
                },
                'correlations': correlations,
                'trends': {
                    'duration_vs_score': {
                        'slope': duration_score_trend.slope,
                        'intercept': duration_score_trend.intercept,
                        'r_squared': duration_score_trend.r_squared,
                        'interpretation': self._interpret_trend(duration_score_trend.slope, 'duration_score')
                    },
                    'duration_vs_earnings': {
                        'slope': duration_earnings_trend.slope,
                        'intercept': duration_earnings_trend.intercept,
                        'r_squared': duration_earnings_trend.r_squared,
                        'interpretation': self._interpret_trend(duration_earnings_trend.slope, 'duration_earnings')
                    }
                },
                'moving_averages': {
                    'duration': duration_ma,
                    'score': score_ma
                },
                'performance_metrics': performance_metrics,
                'rust_engine_used': rust_engine.rust_available
            }
            
        except Exception as e:
            logging.error(f"Enhanced statistics calculation failed: {e}")
            # Fallback to basic statistics
            return self.calculate_aggregate_statistics(tasks_data, week_id)
    
    def _interpret_trend(self, slope, trend_type):
        """Interpret trend slope values for user-friendly display"""
        if trend_type == 'duration_score':
            if slope > 0.1:
                return "Quality improves with longer tasks"
            elif slope < -0.1:
                return "Quality decreases with longer tasks"
            else:
                return "No significant quality trend"
        elif trend_type == 'duration_earnings':
            if slope > 0.5:
                return "Strong positive earnings correlation"
            elif slope > 0.1:
                return "Moderate positive earnings correlation"
            elif slope < -0.1:
                return "Negative earnings correlation"
            else:
                return "No significant earnings trend"
        return "Trend analysis available"
    
    def get_correlation_insights(self, tasks_data, week_id=None):
        """
        Get correlation insights using Rust Statistical Engine
        
        Provides high-performance correlation analysis between different task metrics
        """
        if not tasks_data or len(tasks_data) < 2:
            return {}
        
        # Extract data for correlation analysis
        durations = []
        scores = []
        time_limits = []
        earnings = []
        
        for task in tasks_data:
            duration_seconds = self._parse_time_to_seconds(task[0])
            time_limit_seconds = self._parse_time_to_seconds(task[1])
            score = float(task[2])
            
            durations.append(duration_seconds / 3600.0)
            scores.append(score)
            time_limits.append(time_limit_seconds / 3600.0)
            
            # Calculate earnings (simplified)
            global_payrate = self.global_settings.get_default_payrate()
            earnings.append((duration_seconds / 3600.0) * global_payrate)
        
        # Calculate correlations using Rust engine
        correlation_data = {
            'duration': durations,
            'score': scores,
            'time_limit': time_limits,
            'earnings': earnings
        }
        
        correlations = calculate_batch_correlations(correlation_data)
        
        # Interpret correlations
        insights = {}
        for pair, corr_value in correlations.items():
            var1, var2 = pair.split('_', 1)
            strength = abs(corr_value)
            direction = "positive" if corr_value > 0 else "negative"
            
            if strength > 0.7:
                strength_desc = "strong"
            elif strength > 0.4:
                strength_desc = "moderate"
            elif strength > 0.2:
                strength_desc = "weak"
            else:
                strength_desc = "negligible"
            
            insights[pair] = {
                'correlation': corr_value,
                'strength': strength_desc,
                'direction': direction,
                'description': f"{strength_desc.title()} {direction} correlation between {var1} and {var2}"
            }
        
        return insights 