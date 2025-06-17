"""
Hybrid TaskGrid that embeds QML TableView in a QWidget
Combines the best of both worlds: modern QML UI with existing Python logic
Enhanced with Data Service Layer for improved performance and caching
"""

import os
import logging
from PySide6 import QtCore, QtWidgets, QtQuick, QtQml
from PySide6.QtQuickWidgets import QQuickWidget
from PySide6.QtQml import qmlRegisterType
from PySide6.QtCore import QUrl, Slot, Signal
from datetime import datetime, timedelta

from ui.qml_task_model import QMLTaskModel
from ui.timer_dialog import TimerDialog
from ui.feedback_dialog import FeedbackDialog
from ui.classic_task_edit_dialog import ClassicTaskEditDialog

# Import Data Service Layer components
from core.services import TaskDAO, WeekDAO, DataServiceError

# Import Event Bus components
from core.events import get_event_bus, EventType

# Configure logging
logger = logging.getLogger(__name__)

class QMLTaskGrid(QtWidgets.QWidget):
    """QML-based task grid with Data Service Layer integration for enhanced performance"""
    
    # Define custom signal for time limit changes
    timeLimitChanged = QtCore.Signal(int, str)  # task_id, new_time_limit_string
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.office_hour_count_label = None
        self.modern_dialog = None
        
        # Initialize Event Bus
        self.event_bus = get_event_bus()
        
        # Initialize Data Access Objects
        self.task_dao = TaskDAO()
        self.week_dao = WeekDAO()
        
        # Create the QML model
        self.task_model = QMLTaskModel(self)
        
        # Connect model signals
        self.task_model.timeLimitChanged.connect(self.timeLimitChanged)
        self.task_model.selectionChanged.connect(self._on_selection_changed)
        
        # Setup QML engine and view
        self._setup_qml()
        
        # Setup layout
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.qml_widget)
    
    def _setup_qml(self):
        """Setup QML engine and load the QML interface"""
        # Create QQuickWidget
        self.qml_widget = QQuickWidget()
        self.qml_widget.setResizeMode(QQuickWidget.SizeRootObjectToView)
        
        # Get QML engine and register types
        engine = self.qml_widget.engine()
        
        # Set QML import paths
        qml_dir = os.path.join(os.path.dirname(__file__), "qml")
        engine.addImportPath(qml_dir)
        
        # Register the model instance with QML context
        context = self.qml_widget.rootContext()
        context.setContextProperty("taskModel", self.task_model)
        context.setContextProperty("taskController", self)
        
        # Load the QML file
        qml_file = os.path.join(qml_dir, "TaskGridView.qml")
        self.qml_widget.setSource(QtCore.QUrl.fromLocalFile(qml_file))
        
        # Connect QML signals
        root_object = self.qml_widget.rootObject()
        if root_object:
            root_object.taskDoubleClicked.connect(self.open_task_edit_dialog)
            root_object.taskClicked.connect(self._handle_task_clicked)
            # Removed root_object.selectionChanged connection to avoid dual signal paths
            # Selection changes are now handled only through the Python model signal
            
            # Set the model
            root_object.setProperty("model", self.task_model)
    
    @QtCore.Slot(int)
    def _handle_task_double_clicked(self, task_id):
        """Handle double-click events on task rows - opens unified edit dialog"""
        # The unified dialog is now handled entirely in QML
        # This method is kept for compatibility but the actual dialog opening
        # is handled by the QML openTaskEditDialog function
        pass
    
    @QtCore.Slot(int)
    def _handle_task_clicked(self, task_id):
        """Handle single-click events on tasks"""
        # Could be used for additional functionality
        pass
    
    def _on_selection_changed(self):
        """Handle selection changes"""
        # Emit event through event bus
        self.event_bus.emit_event(
            EventType.TASK_SELECTION_CHANGED,
            {
                'selected_count': len(self.selected_tasks),
                'selected_task_ids': list(self.selected_tasks)
            },
            'QMLTaskGrid'
        )
        
        # Maintain backward compatibility
        if hasattr(self.main_window, 'update_delete_button'):
            self.main_window.update_delete_button()
    
    @property
    def current_week_id(self):
        """Get current week ID"""
        return self.task_model.current_week_id
    
    @property
    def selected_tasks(self):
        """Get selected task IDs"""
        return self.task_model.selected_tasks
    
    def refresh_tasks(self, week_id):
        """Refresh tasks for a specific week"""
        self.task_model.refreshTasks(week_id)
    
    def delete_selected_tasks(self):
        """Delete selected tasks using Data Service Layer"""
        selected_ids = self.task_model.getSelectedTaskIds()
        if not selected_ids:
            return
        
        try:
            # Use TaskDAO for efficient batch deletion with caching
            deleted_count = self.task_dao.delete_multiple_tasks(selected_ids)
            logger.info(f"Successfully deleted {deleted_count} tasks: {selected_ids}")
            
            # Emit task deleted event
            self.event_bus.emit_event(
                EventType.TASKS_BULK_UPDATED,
                {
                    'action': 'deleted',
                    'task_ids': selected_ids,
                    'count': deleted_count,
                    'week_id': self.task_model.current_week_id
                },
                'QMLTaskGrid'
            )
            
            # Refresh the view
            self.refresh_tasks(self.task_model.current_week_id)
            
            # Update analysis (maintain backward compatibility)
            if hasattr(self.main_window, 'refresh_analysis'):
                self.main_window.refresh_analysis()
                
        except DataServiceError as e:
            logger.error(f"Failed to delete tasks {selected_ids}: {e}")
            # Could show user notification here if needed
            raise
    
    def add_task(self, week_id):
        """Add a new task"""
        self.create_task_in_week(week_id)
    
    def create_task_in_week(self, week_id):
        """Create a new task in the specified week using Data Service Layer"""
        try:
            # Use TaskDAO for optimized task creation with default values
            task_id = self.task_dao.create_task(
                week_id,
                attempt_id="",
                duration="00:00:00",
                project_id="",
                project_name="",
                operation_id="",
                time_limit="00:00:00",
                date_audited=datetime.now().strftime("%Y-%m-%d"),
                score=1,
                feedback="",
                locale="",
                time_begin="",
                time_end=""
            )
            logger.info(f"Successfully created new task {task_id} in week {week_id}")
            
            # Emit task created event
            self.event_bus.emit_event(
                EventType.TASK_CREATED,
                {
                    'task_id': task_id,
                    'week_id': week_id,
                    'action': 'created'
                },
                'QMLTaskGrid'
            )
            
            # Refresh the view
            self.refresh_tasks(week_id)
            
            # Emit the taskAdded signal for QML to handle scroll-to-task
            self.task_model.taskAdded.emit(task_id)
            
            # Check setting for auto-edit functionality
            from core.settings.global_settings import global_settings
            if global_settings.should_auto_edit_new_tasks():
                # Open edit dialog automatically after a brief delay
                QtCore.QTimer.singleShot(300, lambda: self.open_task_edit_dialog(task_id))
            
            # Update analysis (maintain backward compatibility)
            if hasattr(self.main_window, 'refresh_analysis'):
                self.main_window.refresh_analysis()
                
        except DataServiceError as e:
            logger.error(f"Failed to create task in week {week_id}: {e}")
            raise
    
    def open_timer_dialog(self, task_id):
        """Open timer dialog for a task"""
        # Get task data
        task_data = None
        for task in self.task_model.tasks:
            if task[0] == task_id:
                task_data = task
                break
        
        if not task_data:
            return
        
        # Extract current duration and time limit
        current_duration = task_data[2] if len(task_data) > 2 else "00:00:00"
        time_limit = task_data[6] if len(task_data) > 6 else "00:00:00"
        
        # Open timer dialog
        timer_dialog = TimerDialog(
            self, 
            task_id=task_id,
            current_duration=current_duration,
            time_limit=time_limit
        )
        
        # Connect timer signals
        timer_dialog.durationUpdated.connect(
            self.update_task_time_and_duration_from_timer
        )
        
        timer_dialog.exec()
    
    def edit_feedback(self, task_id):
        """Edit feedback for a task"""
        # Get current feedback
        current_feedback = ""
        for task in self.task_model.tasks:
            if task[0] == task_id:
                current_feedback = task[9] if len(task) > 9 else ""
                break
        
        # Open feedback dialog
        feedback_dialog = FeedbackDialog(
            self, 
            feedback=current_feedback, 
            task_id=task_id
        )
        
        if feedback_dialog.exec() == QtWidgets.QDialog.Accepted:
            # Refresh the view to show updated feedback
            self.refresh_tasks(self.task_model.current_week_id)
    
    def update_task_time_and_duration_from_timer(self, task_id, new_duration_seconds, 
                                                is_first_start_for_task, has_duration_changed, 
                                                start_timestamp_for_new_task=None):
        """Update task time and duration from timer using Data Service Layer"""
        try:
            # Convert seconds to HH:MM:SS format
            hours = new_duration_seconds // 3600
            minutes = (new_duration_seconds % 3600) // 60
            seconds = new_duration_seconds % 60
            duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            # Prepare update data
            update_data = {'duration': duration_str}
            
            if start_timestamp_for_new_task:
                # Update time_begin and time_end
                time_begin = start_timestamp_for_new_task.strftime("%H:%M:%S")
                time_end = (start_timestamp_for_new_task + timedelta(seconds=new_duration_seconds)).strftime("%H:%M:%S")
                update_data.update({
                    'time_begin': time_begin,
                    'time_end': time_end
                })
            
            # Use TaskDAO for optimized task update with caching
            self.task_dao.update_task(task_id, update_data)
            logger.info(f"Successfully updated task {task_id} duration to {duration_str}")
            
            # Emit task updated event
            self.event_bus.emit_event(
                EventType.TASK_UPDATED,
                {
                    'task_id': task_id,
                    'action': 'timer_update',
                    'duration': duration_str,
                    'duration_seconds': new_duration_seconds,
                    'week_id': self.task_model.current_week_id
                },
                'QMLTaskGrid'
            )
            
            # Refresh the view
            self.refresh_tasks(self.task_model.current_week_id)
            
            # Update analysis (maintain backward compatibility)
            if hasattr(self.main_window, 'refresh_analysis'):
                self.main_window.refresh_analysis()
                
        except DataServiceError as e:
            logger.error(f"Failed to update task {task_id} duration: {e}")
            raise
    
    def set_office_hour_count_label(self, label):
        """Set the office hour count label"""
        self.office_hour_count_label = label
        self.update_office_hour_count_display()
    
    def add_office_hour_session(self):
        """Add an office hour session using Data Service Layer"""
        if not self.task_model.current_week_id:
            return
        
        try:
            # Use WeekDAO for optimized office hour increment with caching
            self.week_dao.increment_office_hours(self.task_model.current_week_id)
            logger.info(f"Successfully incremented office hours for week {self.task_model.current_week_id}")
            
            self.update_office_hour_count_display()
            
        except DataServiceError as e:
            logger.error(f"Failed to increment office hours for week {self.task_model.current_week_id}: {e}")
            raise
    
    def remove_office_hour_session(self):
        """Remove an office hour session using Data Service Layer"""
        if not self.task_model.current_week_id:
            return
        
        try:
            # Use WeekDAO for optimized office hour decrement with caching
            self.week_dao.decrement_office_hours(self.task_model.current_week_id)
            logger.info(f"Successfully decremented office hours for week {self.task_model.current_week_id}")
            
            self.update_office_hour_count_display()
            
        except DataServiceError as e:
            logger.error(f"Failed to decrement office hours for week {self.task_model.current_week_id}: {e}")
            raise
    
    def update_office_hour_count_display(self):
        """Update the office hour count display using Data Service Layer"""
        if not self.office_hour_count_label or not self.task_model.current_week_id:
            return
        
        try:
            # Use WeekDAO for cached office hour count retrieval
            week_data = self.week_dao.get_week_by_id(self.task_model.current_week_id)
            count = week_data.get('office_hour_count', 0) if week_data else 0
            
            self.office_hour_count_label.setText(str(count))
            
        except DataServiceError as e:
            logger.error(f"Failed to get office hour count for week {self.task_model.current_week_id}: {e}")
            # Fallback to showing 0
            self.office_hour_count_label.setText("0")
    
    def cleanup_diagnostics(self):
        """Cleanup method for compatibility with original TaskGrid"""
        # QML version doesn't need diagnostics cleanup, but method exists for compatibility
        pass
    
    @Slot(int)
    def open_task_edit_dialog(self, task_id):
        """Open classic task edit dialog"""
        # Get task data
        task_data = None
        for task in self.task_model.tasks:
            if task[0] == task_id:
                task_data = task
                break
        
        if not task_data:
            return
        
        # Create and setup classic dialog
        dialog = ClassicTaskEditDialog(self)
        
        # Prepare task data dict
        task_dict = {
            'attemptId': task_data[1] if len(task_data) > 1 else "",
            'duration': task_data[2] if len(task_data) > 2 else "00:00:00",
            'projectId': task_data[3] if len(task_data) > 3 else "",
            'projectName': task_data[4] if len(task_data) > 4 else "",
            'operationId': task_data[5] if len(task_data) > 5 else "",
            'timeLimit': task_data[6] if len(task_data) > 6 else "00:00:00",
            'dateAudited': task_data[7] if len(task_data) > 7 else "",
            'score': str(task_data[8]) if len(task_data) > 8 else "1",
            'feedback': task_data[9] if len(task_data) > 9 else "",
            'locale': task_data[10] if len(task_data) > 10 else "",
            'timeBegin': task_data[11] if len(task_data) > 11 else "",
            'timeEnd': task_data[12] if len(task_data) > 12 else ""
        }
        
        # Set task data
        dialog.set_task_data(task_id, task_dict)
        
        # Connect signals
        dialog.taskDataSaved.connect(self.on_task_data_saved)
        
        # Show dialog
        dialog.exec()
    
    def on_task_data_saved(self, task_id, task_data):
        """Handle task data saved from dialog"""
        # Emit task updated event
        self.event_bus.emit_event(
            EventType.TASK_UPDATED,
            {
                'task_id': task_id,
                'action': 'dialog_edit',
                'task_data': task_data,
                'week_id': self.task_model.current_week_id
            },
            'QMLTaskGrid'
        )
        
        # Refresh the view to show updated data
        self.refresh_tasks(self.task_model.current_week_id)
        
        # Update analysis if available (maintain backward compatibility)
        if hasattr(self.main_window, 'refresh_analysis'):
            self.main_window.refresh_analysis()
        



# Test the integration
if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    
    # Create the QML task grid
    task_grid = QMLTaskGrid()
    
    # Create and set up model
    model = QMLTaskModel()
    model.refreshTasks(1)  # Load tasks for week 1
    task_grid.task_model = model
    
    # Show the widget
    task_grid.resize(800, 600)
    task_grid.show()
    
    app.exec() 