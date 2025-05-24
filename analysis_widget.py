import sqlite3
from PySide6 import QtCore, QtWidgets, QtGui
from collections import defaultdict # For easier data aggregation
import html # Import for escaping HTML special characters

DB_FILE = "tasks.db"

class AnalysisWidget(QtWidgets.QWidget):
    def __init__(self, parent=None): 
        super().__init__(parent)
        self.setWindowTitle("Data Analysis")
        self.setWindowFlags(QtCore.Qt.Window)

        main_layout = QtWidgets.QVBoxLayout(self)
        self.tabs = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tabs)

        # Create tabs: Weekly Overview and Daily Overview
        self.weekly_tab = QtWidgets.QWidget()
        self.daily_tab = QtWidgets.QWidget()

        self.tabs.addTab(self.weekly_tab, "Weekly Overview")
        self.tabs.addTab(self.daily_tab, "Daily Overview")

        # --- Setup Weekly Overview Tab ---
        weekly_layout = QtWidgets.QHBoxLayout(self.weekly_tab)
        
        # Left column - Weekly Statistics
        weekly_stats_widget = QtWidgets.QWidget()
        weekly_stats_layout = QtWidgets.QVBoxLayout(weekly_stats_widget)
        weekly_stats_layout.addWidget(QtWidgets.QLabel("<b>Weekly Statistics</b>"))
        self.total_time_label = QtWidgets.QLabel("Total Time: 00:00:00")
        self.avg_time_label = QtWidgets.QLabel("Average Time: 00:00:00")
        self.time_limit_usage_label = QtWidgets.QLabel("Time Limit Usage: 0.0%")
        self.fail_rate_label = QtWidgets.QLabel("Fail Rate: 0.0%")
        self.bonus_tasks_label = QtWidgets.QLabel("Bonus Tasks: 0")
        self.weekly_earnings_label = QtWidgets.QLabel("Weekly Earnings: $0.00")
        weekly_stats_layout.addWidget(self.total_time_label)
        weekly_stats_layout.addWidget(self.avg_time_label)
        weekly_stats_layout.addWidget(self.time_limit_usage_label)
        weekly_stats_layout.addWidget(self.fail_rate_label)
        weekly_stats_layout.addWidget(self.bonus_tasks_label)
        weekly_stats_layout.addWidget(self.weekly_earnings_label)
        weekly_stats_layout.addStretch()
        weekly_layout.addWidget(weekly_stats_widget)
        
        # Right column - Weekly Project Breakdown
        weekly_project_widget = QtWidgets.QWidget()
        weekly_project_layout = QtWidgets.QVBoxLayout(weekly_project_widget)
        weekly_project_layout.addWidget(QtWidgets.QLabel("<b>Project Breakdown</b>"))
        self.weekly_project_text = QtWidgets.QTextEdit()
        self.weekly_project_text.setReadOnly(True)
        weekly_project_layout.addWidget(self.weekly_project_text)
        weekly_layout.addWidget(weekly_project_widget)

        # --- Setup Daily Overview Tab ---
        daily_layout = QtWidgets.QHBoxLayout(self.daily_tab)
        
        # Left column - Daily Durations
        daily_duration_widget = QtWidgets.QWidget()
        daily_duration_layout = QtWidgets.QVBoxLayout(daily_duration_widget)
        daily_duration_layout.addWidget(QtWidgets.QLabel("<b>Daily Durations</b>"))
        self.daily_duration_text = QtWidgets.QTextEdit()
        self.daily_duration_text.setReadOnly(True)
        daily_duration_layout.addWidget(self.daily_duration_text)
        daily_layout.addWidget(daily_duration_widget)
        
        # Right column - Daily Project Breakdown
        daily_project_widget = QtWidgets.QWidget()
        daily_project_layout = QtWidgets.QVBoxLayout(daily_project_widget)
        daily_project_layout.addWidget(QtWidgets.QLabel("<b>Daily Project Breakdown</b>"))
        self.daily_project_text = QtWidgets.QTextEdit()
        self.daily_project_text.setReadOnly(True)
        daily_project_layout.addWidget(self.daily_project_text)
        daily_layout.addWidget(daily_project_widget)

    def _format_time(self, total_seconds):
        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        secs = int(total_seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

    def refresh_analysis(self, week_id):
        if week_id is None:
            self.clear_statistics()
            return

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute("""
            SELECT duration, time_limit, score, project_name, locale, date_audited, bonus_paid
            FROM tasks
            WHERE week_id=?
        """, (week_id,))
        tasks_data = c.fetchall()
        conn.close()

        if not tasks_data:
            self.clear_statistics()
            return

        total_task_seconds = 0
        total_limit_seconds = 0
        low_scores = 0
        num_tasks = len(tasks_data)
        bonus_task_count = 0
        regular_task_seconds = 0
        bonus_task_seconds = 0

        # Data structures for analysis
        project_locale_counts = defaultdict(lambda: defaultdict(int))
        daily_total_seconds = defaultdict(int)
        daily_regular_seconds = defaultdict(int)
        daily_bonus_seconds = defaultdict(int)
        daily_project_counts = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))

        for duration_str, time_limit_str, score, project_name, locale, date_audited, bonus_paid in tasks_data:
            current_task_seconds = 0
            is_bonus = bool(bonus_paid)
            
            try:
                if duration_str:
                    h, m, s = map(int, duration_str.split(':'))
                    current_task_seconds = h * 3600 + m * 60 + s
                    total_task_seconds += current_task_seconds
                    
                    # Track separately for regular and bonus tasks
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
            except (ValueError, AttributeError, TypeError) as e:
                print(f"Warning: Error parsing time/score data: {e} for task data: {(duration_str, time_limit_str, score)}")
                pass

            # Clean up project name and locale
            pn = project_name if project_name and project_name.strip() else "Unassigned Project"
            loc = locale if locale and locale.strip() else "N/A"
            
            # Update weekly project breakdown
            project_locale_counts[pn][loc] += 1

            # Update daily data if we have a date
            if date_audited and date_audited.strip():
                day = date_audited.strip()
                daily_total_seconds[day] += current_task_seconds
                # Track separately for regular and bonus tasks
                if is_bonus:
                    daily_bonus_seconds[day] += current_task_seconds
                else:
                    daily_regular_seconds[day] += current_task_seconds
                
                # Store daily project breakdown
                daily_project_counts[day][pn][loc] += 1

        # Calculate statistics
        avg_seconds = total_task_seconds / num_tasks if num_tasks > 0 else 0
        time_limit_usage = (total_task_seconds / total_limit_seconds * 100) if total_limit_seconds > 0 else 0
        fail_rate = (low_scores / num_tasks * 100) if num_tasks > 0 else 0
        
        # Calculate earnings with bonus pay (50% increase for bonus tasks)
        hourly_rate = 25.3
        regular_hours = regular_task_seconds / 3600.0
        bonus_hours = bonus_task_seconds / 3600.0
        bonus_rate = hourly_rate * 1.5  # 50% increase for bonus tasks
        weekly_earnings = (regular_hours * hourly_rate) + (bonus_hours * bonus_rate)

        # Update weekly statistics labels
        self.total_time_label.setText(f"Total Time: {self._format_time(total_task_seconds)}")
        self.avg_time_label.setText(f"Average Time: {self._format_time(avg_seconds)}")
        self.time_limit_usage_label.setText(f"Time Limit Usage: {time_limit_usage:.1f}%")
        self.fail_rate_label.setText(f"Fail Rate: {fail_rate:.1f}%")
        self.bonus_tasks_label.setText(f"Bonus Tasks: {bonus_task_count}")
        self.weekly_earnings_label.setText(f"Weekly Earnings: ${weekly_earnings:.2f}")

        # Update weekly project breakdown
        weekly_project_html = []
        for project_name_key, locales_map in sorted(project_locale_counts.items()):
            weekly_project_html.append(f"<b>{html.escape(str(project_name_key))}:</b>")
            for locale_key, count in sorted(locales_map.items()):
                weekly_project_html.append(f"&nbsp;&nbsp;{html.escape(str(locale_key))}: {count} task(s)")
            weekly_project_html.append("") 
        self.weekly_project_text.setHtml("<br>".join(weekly_project_html))

        # Update daily durations
        daily_duration_html = []
        for date_key in sorted(daily_total_seconds.keys()):
            total_time = self._format_time(daily_total_seconds[date_key])
            regular_time = self._format_time(daily_regular_seconds[date_key])
            bonus_time = self._format_time(daily_bonus_seconds[date_key])
            
            daily_duration_html.append(f"<b>{html.escape(str(date_key))}:</b>")
            daily_duration_html.append(f"&nbsp;&nbsp;Total: {total_time}")
            daily_duration_html.append(f"&nbsp;&nbsp;Regular: {regular_time}")
            daily_duration_html.append(f"&nbsp;&nbsp;Bonus: {bonus_time}")
            daily_duration_html.append("") 
        self.daily_duration_text.setHtml("<br>".join(daily_duration_html))

        # Update daily project breakdown
        daily_project_html = []
        for date_key in sorted(daily_project_counts.keys()):
            daily_project_html.append(f"<b>{html.escape(str(date_key))}</b>")
            
            for project_name_key, locales_map in sorted(daily_project_counts[date_key].items()):
                daily_project_html.append(f"&nbsp;&nbsp;<b>{html.escape(str(project_name_key))}:</b>")
                
                for locale_key, count in sorted(locales_map.items()):
                    daily_project_html.append(f"&nbsp;&nbsp;&nbsp;&nbsp;{html.escape(str(locale_key))}: {count} task(s)")
            
            daily_project_html.append("") 
        
        self.daily_project_text.setHtml("<br>".join(daily_project_html))

    def clear_statistics(self):
        # Clear weekly statistics
        self.total_time_label.setText("Total Time: 00:00:00")
        self.avg_time_label.setText("Average Time: 00:00:00")
        self.time_limit_usage_label.setText("Time Limit Usage: 0.0%")
        self.fail_rate_label.setText("Fail Rate: 0.0%")
        self.bonus_tasks_label.setText("Bonus Tasks: 0")
        self.weekly_earnings_label.setText("Weekly Earnings: $0.00")
        
        # Clear project breakdowns and daily data
        self.weekly_project_text.clear()
        self.daily_duration_text.clear()
        self.daily_project_text.clear()


