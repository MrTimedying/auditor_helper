"""
Enhanced TaskTableModel for QML integration
Extends the original TaskTableModel with QML-specific functionality
"""

import sqlite3
from PySide6 import QtCore, QtWidgets, QtGui, QtQml
from datetime import datetime, timedelta
from core.db.db_connection_pool import get_db_connection
from core.db.database_config import DATABASE_FILE
from core.settings.global_settings import global_settings

DB_FILE = DATABASE_FILE

class QMLTaskModel(QtCore.QAbstractListModel):
    """QML-compatible task model with proper property exposure"""
    
    # Define roles for QML access
    IdRole = QtCore.Qt.UserRole + 1
    AttemptIdRole = QtCore.Qt.UserRole + 2
    DurationRole = QtCore.Qt.UserRole + 3
    ProjectIdRole = QtCore.Qt.UserRole + 4
    ProjectNameRole = QtCore.Qt.UserRole + 5
    OperationIdRole = QtCore.Qt.UserRole + 6
    TimeLimitRole = QtCore.Qt.UserRole + 7
    DateAuditedRole = QtCore.Qt.UserRole + 8
    ScoreRole = QtCore.Qt.UserRole + 9
    FeedbackRole = QtCore.Qt.UserRole + 10
    LocaleRole = QtCore.Qt.UserRole + 11
    TimeBeginRole = QtCore.Qt.UserRole + 12
    TimeEndRole = QtCore.Qt.UserRole + 13
    IsSelectedRole = QtCore.Qt.UserRole + 14
    
    # Custom signals
    timeLimitChanged = QtCore.Signal(int, str)  # task_id, new_time_limit_string
    selectionChanged = QtCore.Signal()
    taskAdded = QtCore.Signal(int)  # task_id - emitted when a new task is created
    modelAboutToBeReset = QtCore.Signal()
    modelReset = QtCore.Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tasks = []
        self.selected_tasks = set()
        self.main_window = parent
        self.current_week_id = None
        
        # Column headers for reference
        self.headers = [
            "Attempt ID", "Duration", "Project ID", "Project Name", 
            "Operation ID", "Time Limit", "Date Audited", "Score", 
            "Feedback", "Locale", "Time Begin", "Time End"
        ]
    
    def roleNames(self):
        """Define role names for QML access"""
        return {
            self.IdRole: b"taskId",
            self.AttemptIdRole: b"attemptId",
            self.DurationRole: b"duration",
            self.ProjectIdRole: b"projectId",
            self.ProjectNameRole: b"projectName",
            self.OperationIdRole: b"operationId",
            self.TimeLimitRole: b"timeLimit",
            self.DateAuditedRole: b"dateAudited",
            self.ScoreRole: b"score",
            self.FeedbackRole: b"feedback",
            self.LocaleRole: b"locale",
            self.TimeBeginRole: b"timeBegin",
            self.TimeEndRole: b"timeEnd",
            self.IsSelectedRole: b"isSelected"
        }
    
    def rowCount(self, parent=QtCore.QModelIndex()):
        return len(self.tasks)
    
    def data(self, index, role=QtCore.Qt.DisplayRole):
        if not index.isValid() or index.row() >= len(self.tasks):
            return None
        
        task = self.tasks[index.row()]
        task_id = task[0]
        
        if role == self.IdRole:
            return task_id
        elif role == self.AttemptIdRole:
            return str(task[1]) if len(task) > 1 else ""
        elif role == self.DurationRole:
            return str(task[2]) if len(task) > 2 else ""
        elif role == self.ProjectIdRole:
            return str(task[3]) if len(task) > 3 else ""
        elif role == self.ProjectNameRole:
            return str(task[4]) if len(task) > 4 else ""
        elif role == self.OperationIdRole:
            return str(task[5]) if len(task) > 5 else ""
        elif role == self.TimeLimitRole:
            return str(task[6]) if len(task) > 6 else ""
        elif role == self.DateAuditedRole:
            return str(task[7]) if len(task) > 7 else ""
        elif role == self.ScoreRole:
            return str(task[8]) if len(task) > 8 else ""
        elif role == self.FeedbackRole:
            return str(task[9]) if len(task) > 9 else ""
        elif role == self.LocaleRole:
            return str(task[10]) if len(task) > 10 else ""
        elif role == self.TimeBeginRole:
            return str(task[11]) if len(task) > 11 else ""
        elif role == self.TimeEndRole:
            return str(task[12]) if len(task) > 12 else ""
        elif role == self.IsSelectedRole:
            return task_id in self.selected_tasks
        
        return None
    
    @QtCore.Slot(int, bool)
    def setTaskSelection(self, taskId, selected):
        """Set selection state for a task"""
        if selected:
            self.selected_tasks.add(taskId)
        else:
            self.selected_tasks.discard(taskId)
        
        # Find the row and emit dataChanged
        for row, task in enumerate(self.tasks):
            if task[0] == taskId:
                index = self.createIndex(row, 0)
                self.dataChanged.emit(index, index, [self.IsSelectedRole])
                break
        
        self.selectionChanged.emit()
    
    @QtCore.Slot(int, str, str)
    def updateTaskField(self, taskId, fieldName, value):
        """Update a task field"""
        # Map field names to database columns
        field_mapping = {
            "attemptId": "attempt_id",
            "duration": "duration", 
            "projectId": "project_id",
            "projectName": "project_name",
            "operationId": "operation_id",
            "timeLimit": "time_limit",
            "dateAudited": "date_audited",
            "score": "score",
            "feedback": "feedback",
            "locale": "locale",
            "timeBegin": "time_begin",
            "timeEnd": "time_end"
        }
        
        db_field = field_mapping.get(fieldName)
        if not db_field:
            return
        
        # Update database
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Special handling for some fields
            if db_field == "score":
                try:
                    value = int(value)
                    if value < 1:
                        value = 1
                    elif value > 5:
                        value = 5
                except ValueError:
                    value = 0
            
            # Validate time format for duration and time_limit
            if db_field in ["duration", "time_limit"]:
                if not self.is_valid_time_format(value):
                    value = "00:00:00"
            
            query = f"UPDATE tasks SET {db_field}=? WHERE id=?"
            c.execute(query, (value, taskId))
            conn.commit()
        
        # Update local cache and emit changes
        for row, task in enumerate(self.tasks):
            if task[0] == taskId:
                # Update the task tuple
                task_list = list(task)
                field_index = self._get_field_index(fieldName)
                if field_index is not None and field_index < len(task_list):
                    task_list[field_index] = value
                    self.tasks[row] = tuple(task_list)
                
                # Emit dataChanged
                index = self.createIndex(row, 0)
                self.dataChanged.emit(index, index)
                break
        
        # Emit signal if time_limit was changed
        if fieldName == "timeLimit":
            if self.is_valid_time_format(str(value)):
                self.timeLimitChanged.emit(taskId, str(value))
            else:
                self.timeLimitChanged.emit(taskId, "00:00:00")
    
    def _get_field_index(self, fieldName):
        """Get the index in the task tuple for a field name"""
        field_indices = {
            "attemptId": 1,
            "duration": 2,
            "projectId": 3,
            "projectName": 4,
            "operationId": 5,
            "timeLimit": 6,
            "dateAudited": 7,
            "score": 8,
            "feedback": 9,
            "locale": 10,
            "timeBegin": 11,
            "timeEnd": 12
        }
        return field_indices.get(fieldName)
    
    @QtCore.Slot(result=list)
    def getSelectedTaskIds(self):
        """Get list of selected task IDs"""
        return list(self.selected_tasks)
    
    @QtCore.Slot(result=int)
    def getSelectedCount(self):
        """Get count of selected tasks"""
        return len(self.selected_tasks)
    
    @QtCore.Slot()
    def clearSelection(self):
        """Clear all selections"""
        self.selected_tasks.clear()
        self.beginResetModel()
        self.endResetModel()
        self.selectionChanged.emit()
    
    @QtCore.Slot(int)
    def refreshTasks(self, weekId):
        """Refresh tasks for a specific week"""
        # Emit custom signal before reset
        self.modelAboutToBeReset.emit()
        
        self.beginResetModel()
        self.current_week_id = weekId
        self.selected_tasks.clear()
        
        with get_db_connection() as conn:
            c = conn.cursor()
            c.execute("""
                SELECT id, attempt_id, duration, project_id, project_name, 
                       operation_id, time_limit, date_audited, score, 
                       feedback, locale, time_begin, time_end
                FROM tasks 
                WHERE week_id = ? 
                ORDER BY id ASC
            """, (weekId,))
            self.tasks = c.fetchall()
        
        self.endResetModel()
        
        # Emit custom signal after reset
        self.modelReset.emit()
        
        # Emit selectionChanged to ensure UI updates after clearing selections
        self.selectionChanged.emit()
    
    def is_valid_time_format(self, time_str):
        """Validate time format (HH:MM:SS)"""
        try:
            parts = time_str.split(':')
            if len(parts) != 3:
                return False
            hours, minutes, seconds = map(int, parts)
            return 0 <= hours <= 23 and 0 <= minutes <= 59 and 0 <= seconds <= 59
        except (ValueError, AttributeError):
            return False
    
    # Properties for QML binding
    @QtCore.Property(int, notify=selectionChanged)
    def selectedCount(self):
        return len(self.selected_tasks)
    
    @QtCore.Property(list, notify=selectionChanged)
    def selectedTaskIds(self):
        """Property for selected task IDs"""
        return list(self.selected_tasks)
    
    # New methods for unified dialog functionality
    
    @QtCore.Slot(int, result='QVariant')
    def getTaskData(self, taskId):
        """Get complete task data for editing dialog"""
        for task in self.tasks:
            if task[0] == taskId:
                return {
                    "taskId": task[0],
                    "attemptId": str(task[1]) if len(task) > 1 else "",
                    "duration": str(task[2]) if len(task) > 2 else "00:00:00",
                    "projectId": str(task[3]) if len(task) > 3 else "",
                    "projectName": str(task[4]) if len(task) > 4 else "",
                    "operationId": str(task[5]) if len(task) > 5 else "",
                    "timeLimit": str(task[6]) if len(task) > 6 else "00:00:00",
                    "dateAudited": str(task[7]) if len(task) > 7 else "",
                    "score": str(task[8]) if len(task) > 8 else "1",
                    "feedback": str(task[9]) if len(task) > 9 else "",
                    "locale": str(task[10]) if len(task) > 10 else "",
                    "timeBegin": str(task[11]) if len(task) > 11 else "",
                    "timeEnd": str(task[12]) if len(task) > 12 else ""
                }
        return None
    
    @QtCore.Slot(int, 'QVariant')
    def updateTaskData(self, taskId, taskData):
        """Update multiple task fields at once from dialog"""
        field_mapping = {
            "attemptId": "attempt_id",
            "duration": "duration", 
            "projectId": "project_id",
            "projectName": "project_name",
            "operationId": "operation_id",
            "timeLimit": "time_limit",
            "dateAudited": "date_audited",
            "score": "score",
            "feedback": "feedback",
            "locale": "locale",
            "timeBegin": "time_begin",
            "timeEnd": "time_end"
        }
        
        # Update database
        with get_db_connection() as conn:
            c = conn.cursor()
            
            # Build update query
            updates = []
            values = []
            
            for field, value in taskData.items():
                db_field = field_mapping.get(field)
                if db_field:
                    # Special handling for some fields
                    if db_field == "score":
                        try:
                            value = int(value)
                            if value < 1:
                                value = 1
                            elif value > 5:
                                value = 5
                        except ValueError:
                            value = 1
                    
                    # Validate time format
                    if db_field in ["duration", "time_limit"]:
                        if not self.is_valid_time_format(str(value)):
                            value = "00:00:00"
                    
                    updates.append(f"{db_field}=?")
                    values.append(value)
            
            if updates:
                query = f"UPDATE tasks SET {', '.join(updates)} WHERE id=?"
                values.append(taskId)
                c.execute(query, values)
                conn.commit()
        
        # Refresh the task data
        self.refreshTasks(self.current_week_id)
        
        # Notify main window to refresh analysis if available
        if self.main_window and hasattr(self.main_window, 'analysis_widget'):
            self.main_window.analysis_widget.refresh_analysis()
    
    @QtCore.Slot(int)
    def startTimer(self, taskId):
        """Start timer for a task (preserve existing timer functionality)"""
        if self.main_window and hasattr(self.main_window, 'task_grid'):
            # Delegate to existing timer functionality
            self.main_window.task_grid.start_timer_for_task(taskId)
    
    @QtCore.Slot(int)
    def stopTimer(self, taskId):
        """Stop timer for a task (preserve existing timer functionality)"""
        if self.main_window and hasattr(self.main_window, 'task_grid'):
            # Delegate to existing timer functionality
            self.main_window.task_grid.stop_timer_for_task(taskId)
    
    @QtCore.Slot(int, bool)
    def setRowSelected(self, row, selected):
        """Set selection state for a row by index"""
        if 0 <= row < len(self.tasks):
            taskId = self.tasks[row][0]
            self.setTaskSelection(taskId, selected)
    
    @QtCore.Slot(int, result=int)
    def getTaskIdForRow(self, row):
        """Get task ID for a given row index"""
        if 0 <= row < len(self.tasks):
            return self.tasks[row][0]
        return 0
    
    @QtCore.Slot(list)
    def deleteTasksByIds(self, taskIds):
        """Delete multiple tasks by their IDs"""
        if not taskIds:
            return
        
        # Delete from database
        with get_db_connection() as conn:
            c = conn.cursor()
            placeholders = ','.join(['?'] * len(taskIds))
            query = f"DELETE FROM tasks WHERE id IN ({placeholders})"
            c.execute(query, taskIds)
            conn.commit()
        
        # Remove from selected tasks
        for taskId in taskIds:
            self.selected_tasks.discard(taskId)
        
        # Refresh the task data
        self.refreshTasks(self.current_week_id)
        
        # Notify main window to refresh analysis if available
        if self.main_window and hasattr(self.main_window, 'analysis_widget'):
            self.main_window.analysis_widget.refresh_analysis()
        
        self.selectionChanged.emit()

# Register the model for QML usage
QtQml.qmlRegisterType(QMLTaskModel, "TaskModel", 1, 0, "QMLTaskModel") 