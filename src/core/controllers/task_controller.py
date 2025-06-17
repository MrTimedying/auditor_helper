from PySide6.QtCore import QObject, Slot
from typing import List, Dict, Any, Optional
import logging
from ..events.event_bus import get_event_bus
from ..events.event_types import EventType
from ..repositories.task_repository import TaskRepository
from ..repositories.week_repository import WeekRepository
from ..services.data_service import DataService

class TaskController(QObject):
    """Controller for task-related operations with Redis caching support"""
    
    def __init__(self, task_repository: TaskRepository = None, week_repository: WeekRepository = None, parent=None):
        super().__init__(parent)
        # Use Redis-enabled DataService
        data_service = DataService.get_instance()
        
        # Initialize repositories with Redis-enabled DataService
        self._task_repository = task_repository or TaskRepository(data_service)
        self._week_repository = week_repository or WeekRepository(data_service)
        
        self._event_bus = get_event_bus()
        self._logger = logging.getLogger(__name__)
        
        # Connect to events
        self._event_bus.connect_handler(EventType.TASK_CREATED, self._on_task_created)
        self._event_bus.connect_handler(EventType.TASK_UPDATED, self._on_task_updated)
        self._event_bus.connect_handler(EventType.TASK_DELETED, self._on_task_deleted)
    
    @Slot(int, result=int)
    def create_task(self, week_id: int, **kwargs) -> int:
        """Create new task and emit event"""
        try:
            with self._task_repository.transaction():
                task_id = self._task_repository.create(week_id, **kwargs)
                self._event_bus.emit_event(
                    EventType.TASK_CREATED, 
                    {'task_id': task_id, 'week_id': week_id}, 
                    'TaskController'
                )
                self._logger.info(f"Created task {task_id} in week {week_id}")
                return task_id
        except Exception as e:
            self._logger.error(f"Failed to create task: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'create_task', 'error': str(e), 'week_id': week_id},
                'TaskController'
            )
            raise
    
    @Slot(int, str, object)
    def update_task_field(self, task_id: int, field_name: str, value: Any) -> bool:
        """Update single task field and emit event"""
        try:
            success = self._task_repository.update(task_id, **{field_name: value})
            if success:
                self._event_bus.emit_event(
                    EventType.TASK_UPDATED,
                    {'task_id': task_id, 'field_name': field_name, 'value': value},
                    'TaskController'
                )
                self._logger.debug(f"Updated task {task_id} field {field_name} to {value}")
            return success
        except Exception as e:
            self._logger.error(f"Failed to update task {task_id}: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'update_task', 'error': str(e), 'task_id': task_id, 'field': field_name},
                'TaskController'
            )
            return False
    
    @Slot(int, dict)
    def update_task_multiple_fields(self, task_id: int, updates: Dict[str, Any]) -> bool:
        """Update multiple task fields and emit events"""
        try:
            success = self._task_repository.update(task_id, **updates)
            if success:
                for field_name, value in updates.items():
                    self._event_bus.emit_event(
                        EventType.TASK_UPDATED,
                        {'task_id': task_id, 'field_name': field_name, 'value': value},
                        'TaskController'
                    )
                self._logger.debug(f"Updated task {task_id} with {len(updates)} fields")
            return success
        except Exception as e:
            self._logger.error(f"Failed to update task {task_id}: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'update_task_multiple', 'error': str(e), 'task_id': task_id},
                'TaskController'
            )
            return False
    
    @Slot(int, int, result=bool)
    def delete_task(self, task_id: int, week_id: int) -> bool:
        """Delete single task and emit event"""
        try:
            success = self._task_repository.delete(task_id)
            if success:
                self._event_bus.emit_event(
                    EventType.TASK_DELETED,
                    {'task_id': task_id, 'week_id': week_id},
                    'TaskController'
                )
                self._logger.info(f"Deleted task {task_id} from week {week_id}")
            return success
        except Exception as e:
            self._logger.error(f"Failed to delete task {task_id}: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'delete_task', 'error': str(e), 'task_id': task_id},
                'TaskController'
            )
            return False
    
    @Slot(list, int, result=bool)
    def delete_tasks(self, task_ids: List[int], week_id: int) -> bool:
        """Delete multiple tasks and emit event"""
        try:
            with self._task_repository.transaction():
                deleted_count = self._task_repository.delete_multiple(task_ids)
                if deleted_count > 0:
                    self._event_bus.emit_event(
                        EventType.TASKS_BULK_UPDATED,
                        {'task_ids': task_ids, 'week_id': week_id, 'operation': 'delete'},
                        'TaskController'
                    )
                    self._logger.info(f"Deleted {deleted_count} tasks from week {week_id}")
                return deleted_count > 0
        except Exception as e:
            self._logger.error(f"Failed to delete tasks: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'delete_tasks', 'error': str(e), 'task_ids': task_ids},
                'TaskController'
            )
            return False
    
    @Slot(int, str, str, str)
    def update_task_timer_data(self, task_id: int, duration: str, 
                              time_begin: str = None, time_end: str = None) -> bool:
        """Update task with timer data"""
        try:
            success = self._task_repository.update_duration_and_time(
                task_id, duration, time_begin, time_end
            )
            if success:
                self._event_bus.emit_event(
                    EventType.TIMER_UPDATED,
                    {'task_id': task_id, 'duration': duration, 'time_begin': time_begin, 'time_end': time_end},
                    'TaskController'
                )
                self._logger.info(f"Updated timer data for task {task_id}")
            return success
        except Exception as e:
            self._logger.error(f"Failed to update timer data: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'update_timer_data', 'error': str(e), 'task_id': task_id},
                'TaskController'
            )
            return False
    
    @Slot(int, result=object)
    def get_task(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        try:
            return self._task_repository.get_by_id(task_id)
        except Exception as e:
            self._logger.error(f"Failed to get task {task_id}: {e}")
            return None
    
    @Slot(int, result='QVariant')
    def get_tasks_for_week(self, week_id: int) -> List[Dict[str, Any]]:
        """Get all tasks for a week"""
        try:
            return self._task_repository.get_by_week(week_id)
        except Exception as e:
            self._logger.error(f"Failed to get tasks for week {week_id}: {e}")
            return []
    
    @Slot(str, result='QVariant')
    def get_tasks_by_project(self, project_name: str) -> List[Dict[str, Any]]:
        """Get all tasks for a project"""
        try:
            return self._task_repository.get_tasks_by_project(project_name)
        except Exception as e:
            self._logger.error(f"Failed to get tasks for project {project_name}: {e}")
            return []
    
    @Slot(str, int, result='QVariant')
    def search_tasks(self, search_term: str, week_id: int = None) -> List[Dict[str, Any]]:
        """Search tasks by term"""
        try:
            return self._task_repository.search_tasks(search_term, week_id)
        except Exception as e:
            self._logger.error(f"Failed to search tasks: {e}")
            return []
    
    # Event handlers (for logging and additional processing)
    def _on_task_created(self, event_data):
        """Handle task created event"""
        if hasattr(self._task_repository._data_service, 'clear_cache'):
            self._task_repository._data_service.clear_cache()
    
    def _on_task_updated(self, event_data):
        """Handle task updated event"""
        if hasattr(self._task_repository._data_service, 'clear_cache'):
            self._task_repository._data_service.clear_cache()
    
    def _on_task_deleted(self, event_data):
        """Handle task deleted event"""
        if hasattr(self._task_repository._data_service, 'clear_cache'):
            self._task_repository._data_service.clear_cache() 