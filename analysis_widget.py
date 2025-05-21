
import sqlite3
from PySide6 import QtCore, QtWidgets, QtGui
from collections import defaultdict # For easier data aggregation
import html # Import for escaping HTML special characters

DB_FILE = "tasks.db"

class AnalysisWidget(QtWidgets.QWidget):
    def __init__(self, parent=None): # Corrected constructor name
        super().__init__(parent)
        self.setWindowTitle("Data Analysis")
        self.setWindowFlags(QtCore.Qt.Window)

        main_layout = QtWidgets.QVBoxLayout(self)
        self.tabs = QtWidgets.QTabWidget()
        main_layout.addWidget(self.tabs)

        self.overview_tab = QtWidgets.QWidget()
        self.project_tab = QtWidgets.QWidget()
        self.daily_tab = QtWidgets.QWidget()

        self.tabs.addTab(self.overview_tab, "Weekly Overview")
        self.tabs.addTab(self.project_tab, "Project Breakdown")
        self.tabs.addTab(self.daily_tab, "Daily Performance")

        # --- Setup Overview Tab ---
        overview_layout = QtWidgets.QVBoxLayout(self.overview_tab)
        overview_layout.addWidget(QtWidgets.QLabel("<b>Weekly Statistics</b>"))
        self.total_time_label = QtWidgets.QLabel("Total Time: 00:00:00")
        self.avg_time_label = QtWidgets.QLabel("Average Time: 00:00:00")
        self.time_limit_usage_label = QtWidgets.QLabel("Time Limit Usage: 0.0%")
        self.fail_rate_label = QtWidgets.QLabel("Fail Rate: 0.0%")
        # Corrected: Removed unnecessary escape for $
        self.weekly_earnings_label = QtWidgets.QLabel("Weekly Earnings: \$0.00")
        overview_layout.addWidget(self.total_time_label)
        overview_layout.addWidget(self.avg_time_label)
        overview_layout.addWidget(self.time_limit_usage_label)
        overview_layout.addWidget(self.fail_rate_label)
        overview_layout.addWidget(self.weekly_earnings_label)
        overview_layout.addStretch()

        # --- Setup Project Breakdown Tab ---
        project_layout = QtWidgets.QVBoxLayout(self.project_tab)
        project_layout.addWidget(QtWidgets.QLabel("<b>Projects by Locale</b>"))
        self.project_breakdown_text = QtWidgets.QTextEdit()
        self.project_breakdown_text.setReadOnly(True)
        project_layout.addWidget(self.project_breakdown_text)

        # --- Setup Daily Performance Tab ---
        daily_layout = QtWidgets.QVBoxLayout(self.daily_tab)
        daily_layout.addWidget(QtWidgets.QLabel("<b>Daily Durations</b>"))
        self.daily_duration_text = QtWidgets.QTextEdit()
        self.daily_duration_text.setReadOnly(True)
        daily_layout.addWidget(self.daily_duration_text)

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
            SELECT duration, time_limit, score, project_name, locale, date_audited
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

        project_locale_counts = defaultdict(lambda: defaultdict(int))
        daily_total_seconds = defaultdict(int)

        for duration_str, time_limit_str, score, project_name, locale, date_audited in tasks_data:
            current_task_seconds = 0
            try:
                if duration_str:
                    h, m, s = map(int, duration_str.split(':'))
                    current_task_seconds = h * 3600 + m * 60 + s
                    total_task_seconds += current_task_seconds
                
                if time_limit_str:
                    h, m, s = map(int, time_limit_str.split(':'))
                    total_limit_seconds += h * 3600 + m * 60 + s
                
                if score is not None and score in (1, 2): # Check score is not None
                    low_scores += 1
            except (ValueError, AttributeError, TypeError) as e:
                print(f"Warning: Error parsing time/score data: {e} for task data: {(duration_str, time_limit_str, score)}")
                pass

            pn = project_name if project_name and project_name.strip() else "Unassigned Project"
            loc = locale if locale and locale.strip() else "N/A"
            project_locale_counts[pn][loc] += 1

            # Revised logic: Add to daily totals if date exists, even if duration is 0
            if date_audited and date_audited.strip():
                daily_total_seconds[date_audited.strip()] += current_task_seconds

        avg_seconds = total_task_seconds / num_tasks if num_tasks > 0 else 0
        time_limit_usage = (total_task_seconds / total_limit_seconds * 100) if total_limit_seconds > 0 else 0
        fail_rate = (low_scores / num_tasks * 100) if num_tasks > 0 else 0
        
        hourly_rate = 25.3
        total_hours = total_task_seconds / 3600.0
        weekly_earnings = total_hours * hourly_rate

        self.total_time_label.setText(f"Total Time: {self._format_time(total_task_seconds)}")
        self.avg_time_label.setText(f"Average Time: {self._format_time(avg_seconds)}")
        self.time_limit_usage_label.setText(f"Time Limit Usage: {time_limit_usage:.1f}%")
        self.fail_rate_label.setText(f"Fail Rate: {fail_rate:.1f}%")
        # Corrected: Removed unnecessary escape for $
        self.weekly_earnings_label.setText(f"Weekly Earnings: ${weekly_earnings:.2f}")

        project_display_html = []
        for project_name_key, locales_map in sorted(project_locale_counts.items()):
            # Corrected: Use html.escape and ensure key is string
            project_display_html.append(f"<b>{html.escape(str(project_name_key))}:</b>")
            for locale_key, count in sorted(locales_map.items()):
                project_display_html.append(f"&nbsp;&nbsp;{html.escape(str(locale_key))}: {count} task(s)")
            project_display_html.append("") 
        self.project_breakdown_text.setHtml("<br>".join(project_display_html))

        daily_display_html = []
        for date_key, daily_seconds_val in sorted(daily_total_seconds.items()):
            formatted_time = self._format_time(daily_seconds_val)
            # Corrected: Use html.escape and ensure key is string
            daily_display_html.append(f"{html.escape(str(date_key))}: {formatted_time}")
        self.daily_duration_text.setHtml("<br>".join(daily_display_html))

    def clear_statistics(self):
        self.total_time_label.setText("Total Time: 00:00:00")
        self.avg_time_label.setText("Average Time: 00:00:00")
        self.time_limit_usage_label.setText("Time Limit Usage: 0.0%")
        self.fail_rate_label.setText("Fail Rate: 0.0%")
        # Corrected: Removed unnecessary escape for $
        self.weekly_earnings_label.setText("Weekly Earnings: \\$0.00")
        self.project_breakdown_text.clear()
        self.daily_duration_text.clear()


