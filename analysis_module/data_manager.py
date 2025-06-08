import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta

DB_FILE = "tasks.db"

class DataManager:
    def __init__(self):
        pass

    def populate_week_combo_data(self):
        """Retrieve week data from the database"""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("SELECT id, week_label FROM weeks ORDER BY id")
        weeks = c.fetchall()
        conn.close()
        
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
        """Get data for charting based on selected variables"""
        try:
            conn = sqlite3.connect(DB_FILE)
            cursor = conn.cursor()
            
            # Build query based on current data selection using established state variables
            if current_week_id is not None:
                # Week-based selection
                cursor.execute("SELECT week_label FROM weeks WHERE id = ?", (current_week_id,))
                week_result = cursor.fetchone()
                if not week_result:
                    conn.close()
                    return []
                
                week_label = week_result[0]
                try:
                    start_date_str, end_date_str = week_label.split(" - ")
                    # Dates are in dd/MM/yyyy format
                    start_date = datetime.strptime(start_date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
                    end_date = datetime.strptime(end_date_str, '%d/%m/%Y').strftime('%Y-%m-%d')
                except (ValueError, IndexError):
                    # Fallback or error handling for malformed week_label
                    conn.close()
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
                return self.get_aggregated_chart_data(x_variable, y_variables, where_clause, params, cursor)
            else:
                # Direct query for raw data - need to convert strings to numbers
                query = f"SELECT {', '.join(select_fields)} FROM tasks {where_clause}"
                cursor.execute(query, params)
                raw_data = cursor.fetchall()
                
                # Convert string data to numeric for charting
                converted_data = []
                for row in raw_data:
                    converted_row = []
                    for i, value in enumerate(row):
                        if i == 0:  # X variable
                            converted_row.append(value)  # Keep as is for now
                        else:  # Y variables
                            y_var_name, y_var_type = y_variables[i-1]
                            converted_value = self._convert_value_for_charting(value, y_var_name)
                            converted_row.append(converted_value)
                    converted_data.append(tuple(converted_row))
                
                conn.close()
                return converted_data
                
        except sqlite3.Error as e:
            print(f"Database error in get_chart_data: {e}")
            return []
    
    def get_aggregated_chart_data(self, x_variable, y_variables, where_clause, params, cursor):
        """Get aggregated data for composite metrics"""
        x_var_name, x_var_type = x_variable
        
        # Group by X variable
        if x_var_name in ['date_audited', 'week_id']:
            group_by_field = x_var_name
        elif x_var_name in ['project_name', 'locale']:
            group_by_field = x_var_name
        else:
            # For numeric X variables, we might need to bin them
            group_by_field = x_var_name
        
        # Build aggregation query - get raw data first, then process in Python since duration/time_limit are strings
        query = f"""
        SELECT {group_by_field}, duration, time_limit, score, bonus_paid
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
        
        # Process raw data and group by X variable
        for row in raw_data:
            x_value = row[0]
            duration_str = row[1]
            time_limit_str = row[2]
            score = row[3]
            bonus_paid = row[4]
            
            group = grouped_data[x_value]
            group['task_count'] += 1
            
            # Parse duration
            duration_seconds = parse_time_to_seconds(duration_str)
            group['total_duration_seconds'] += duration_seconds
            group['durations'].append(duration_seconds)
            
            # Parse time limit
            limit_seconds = parse_time_to_seconds(time_limit_str)
            group['total_limit_seconds'] += limit_seconds
            
            # Count failures and bonuses
            if score is not None and score in (1, 2):
                group['fail_count'] += 1
            
            if bonus_paid:
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
            
            # Calculate earnings
            hourly_rate = 25.3
            regular_hours = 0
            bonus_hours = 0
            for i, duration_sec in enumerate(durations):
                hours = duration_sec / 3600.0
                if i < bonus_count:  # Assume first N tasks are bonus (simplified)
                    bonus_hours += hours
                else:
                    regular_hours += hours
            total_earnings = (regular_hours * hourly_rate) + (bonus_hours * hourly_rate * 1.5)
            
            # Build row data for selected variables
            row_data = [x_value]  # X variable value
            
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
        """Retrieve tasks data for a specific week."""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            SELECT duration, time_limit, score, project_name, locale, date_audited, bonus_paid
            FROM tasks
            WHERE week_id=?
        """, (week_id,))
        tasks_data = c.fetchall()
        conn.close()
        return tasks_data

    def get_tasks_data_by_time_range(self, start_date, end_date):
        """Retrieve tasks data for a specific time range."""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            SELECT duration, time_limit, score, project_name, locale, date_audited, bonus_paid
            FROM tasks
            WHERE date_audited BETWEEN ? AND ?
        """, (start_date, end_date))
        tasks_data = c.fetchall()
        conn.close()
        return tasks_data

    def get_tasks_data_for_daily_project(self, selection_type, selected_id, selected_day, current_start_date, current_end_date):
        """Retrieve tasks data for daily project breakdown based on current selection type."""
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        if selection_type == "week":
            c.execute("""
                SELECT duration, time_limit, score, project_name, locale, date_audited, bonus_paid
                FROM tasks
                WHERE week_id=? AND date_audited=?
            """, (selected_id, selected_day))
        elif selection_type == "time_range":
            c.execute("""
                SELECT duration, time_limit, score, project_name, locale, date_audited, bonus_paid
                FROM tasks
                WHERE date_audited=?
            """, (selected_day,))
        else:
            tasks_data = []
        
        if selection_type in ["week", "time_range"]:
            tasks_data = c.fetchall()
        else:
            tasks_data = []
        conn.close()
        return tasks_data

    def calculate_aggregate_statistics(self, tasks_data):
        """Calculate aggregate statistics for the selected time period"""
        total_task_seconds = 0
        total_limit_seconds = 0
        low_scores = 0
        num_tasks = len(tasks_data)
        bonus_task_count = 0
        regular_task_seconds = 0
        bonus_task_seconds = 0

        for duration_str, time_limit_str, score, project_name, locale, date_audited, bonus_paid in tasks_data:
            current_task_seconds = 0
            is_bonus = bool(bonus_paid)
            
            try:
                if duration_str:
                    h, m, s = map(int, duration_str.split(':'))
                    current_task_seconds = h * 3600 + m * 60 + s
                    total_task_seconds += current_task_seconds
                    
                    if is_bonus:
                        bonus_task_seconds += current_task_seconds
                        bonus_task_count += 1
                    else:
                        regular_task_seconds += current_task_seconds
                
                if time_limit_str:
                    h, m, s = map(int, time_limit_str.split(':'))
                    total_limit_seconds += h * 3600 + m * 60 + s
                
                if score is not None and score in (1, 2):
                    low_scores += 1
            except (ValueError, AttributeError, TypeError):
                pass

        # Calculate final statistics
        avg_seconds = total_task_seconds / num_tasks if num_tasks > 0 else 0
        time_limit_usage = (total_task_seconds / total_limit_seconds * 100) if total_limit_seconds > 0 else 0
        fail_rate = (low_scores / num_tasks * 100) if num_tasks > 0 else 0
        
        # Calculate earnings
        hourly_rate = 25.3
        regular_hours = regular_task_seconds / 3600.0
        bonus_hours = bonus_task_seconds / 3600.0
        bonus_rate = hourly_rate * 1.5
        total_earnings = (regular_hours * hourly_rate) + (bonus_hours * bonus_rate)

        return {
            'total_time': self._format_time(total_task_seconds),
            'average_time': self._format_time(avg_seconds),
            'time_limit_usage': f"{time_limit_usage:.1f}%",
            'fail_rate': f"{fail_rate:.1f}%",
            'bonus_tasks': str(bonus_task_count),
            'total_earnings': f"${total_earnings:.2f}"
        }

    def calculate_daily_statistics(self, tasks_data):
        """Calculate daily statistics breakdown"""
        daily_data = defaultdict(lambda: {
            'total_seconds': 0,
            'regular_seconds': 0,
            'bonus_seconds': 0,
            'total_limit_seconds': 0,
            'low_scores': 0,
            'task_count': 0,
            'bonus_count': 0
        })

        for duration_str, time_limit_str, score, project_name, locale, date_audited, bonus_paid in tasks_data:
            if not date_audited or not date_audited.strip():
                continue
                
            day = date_audited.strip()
            is_bonus = bool(bonus_paid)
            
            daily_data[day]['task_count'] += 1
            if is_bonus:
                daily_data[day]['bonus_count'] += 1
            
            try:
                if duration_str:
                    h, m, s = map(int, duration_str.split(':'))
                    current_task_seconds = h * 3600 + m * 60 + s
                    daily_data[day]['total_seconds'] += current_task_seconds
                    
                    if is_bonus:
                        daily_data[day]['bonus_seconds'] += current_task_seconds
                    else:
                        daily_data[day]['regular_seconds'] += current_task_seconds
                
                if time_limit_str:
                    h, m, s = map(int, time_limit_str.split(':'))
                    daily_data[day]['total_limit_seconds'] += h * 3600 + m * 60 + s
                
                if score is not None and score in (1, 2):
                    daily_data[day]['low_scores'] += 1
            except (ValueError, AttributeError, TypeError):
                pass

        # Convert to final format
        daily_stats = {}
        hourly_rate = 25.3
        bonus_rate = hourly_rate * 1.5
        
        for day, data in daily_data.items():
            avg_seconds = data['total_seconds'] / data['task_count'] if data['task_count'] > 0 else 0
            time_limit_usage = (data['total_seconds'] / data['total_limit_seconds'] * 100) if data['total_limit_seconds'] > 0 else 0
            fail_rate = (data['low_scores'] / data['task_count'] * 100) if data['task_count'] > 0 else 0
            
            regular_hours = data['regular_seconds'] / 3600.0
            bonus_hours = data['bonus_seconds'] / 3600.0
            total_earnings = (regular_hours * hourly_rate) + (bonus_hours * bonus_rate)
            
            daily_stats[day] = {
                'date': day,
                'total_time': self._format_time(data['total_seconds']),
                'average_time': self._format_time(avg_seconds),
                'time_limit_usage': f"{time_limit_usage:.1f}%",
                'fail_rate': f"{fail_rate:.1f}%",
                'bonus_tasks': str(data['bonus_count']),
                'total_earnings': f"${total_earnings:.2f}"
            }
        
        return daily_stats

    def calculate_project_statistics(self, tasks_data):
        """Calculate project-based statistics"""
        project_data = defaultdict(lambda: defaultdict(lambda: {
            'total_seconds': 0,
            'task_count': 0,
            'bonus_count': 0
        }))

        for duration_str, time_limit_str, score, project_name, locale, date_audited, bonus_paid in tasks_data:
            pn = project_name if project_name and project_name.strip() else "Unassigned Project"
            loc = locale if locale and locale.strip() else "N/A"
            is_bonus = bool(bonus_paid)
            
            project_data[pn][loc]['task_count'] += 1
            if is_bonus:
                project_data[pn][loc]['bonus_count'] += 1
            
            try:
                if duration_str:
                    h, m, s = map(int, duration_str.split(':'))
                    current_task_seconds = h * 3600 + m * 60 + s
                    project_data[pn][loc]['total_seconds'] += current_task_seconds
            except (ValueError, AttributeError, TypeError):
                pass

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