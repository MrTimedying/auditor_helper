from PySide6.QtCore import QObject, Slot
from typing import List, Dict, Any, Optional
import logging
from ..events.event_bus import get_event_bus
from ..events.event_types import EventType
from ..repositories.week_repository import WeekRepository

class WeekController(QObject):
    """Controller for week-related operations"""
    
    def __init__(self, week_repository: WeekRepository, parent=None):
        super().__init__(parent)
        self._repository = week_repository
        self._event_bus = get_event_bus()
        self._logger = logging.getLogger(__name__)
        
        # Connect to events
        self._event_bus.connect_handler(EventType.WEEK_CREATED, self._on_week_created)
        self._event_bus.connect_handler(EventType.WEEK_UPDATED, self._on_week_updated)
    
    @Slot(str, str, result=int)
    def create_week(self, start_date: str, end_date: str, **kwargs) -> int:
        """Create new week and emit event"""
        try:
            with self._repository.transaction():
                week_id = self._repository.create(start_date, end_date, **kwargs)
                self._event_bus.emit_event(
                    EventType.WEEK_CREATED,
                    {'week_id': week_id, 'start_date': start_date, 'end_date': end_date},
                    'WeekController'
                )
                self._logger.info(f"Created week {week_id} ({start_date} to {end_date})")
                return week_id
        except Exception as e:
            self._logger.error(f"Failed to create week: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'create_week', 'error': str(e), 'start_date': start_date, 'end_date': end_date},
                'WeekController'
            )
            raise
    
    @Slot(int, bool, result=bool)
    def toggle_week_bonus(self, week_id: int, is_bonus_enabled: bool) -> bool:
        """Toggle week bonus status and emit event"""
        try:
            success = self._repository.update_bonus_status(week_id, is_bonus_enabled)
            if success:
                self._event_bus.emit_event(
                    EventType.WEEK_UPDATED,
                    {'week_id': week_id, 'field_name': 'is_bonus_week', 'value': is_bonus_enabled},
                    'WeekController'
                )
                status = "enabled" if is_bonus_enabled else "disabled"
                self._logger.info(f"Week {week_id} bonus {status}")
            return success
        except Exception as e:
            self._logger.error(f"Failed to toggle week bonus: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'toggle_week_bonus', 'error': str(e), 'week_id': week_id},
                'WeekController'
            )
            return False
    
    @Slot(int, str, object, result=bool)
    def update_week_field(self, week_id: int, field_name: str, value: Any) -> bool:
        """Update single week field and emit event"""
        try:
            success = self._repository.update(week_id, **{field_name: value})
            if success:
                self._event_bus.emit_event(
                    EventType.WEEK_UPDATED,
                    {'week_id': week_id, 'field_name': field_name, 'value': value},
                    'WeekController'
                )
                self._logger.debug(f"Updated week {week_id} field {field_name} to {value}")
            return success
        except Exception as e:
            self._logger.error(f"Failed to update week {week_id}: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'update_week', 'error': str(e), 'week_id': week_id, 'field': field_name},
                'WeekController'
            )
            return False
    
    @Slot(int, result=object)
    def get_week(self, week_id: int) -> Optional[Dict[str, Any]]:
        """Get week by ID"""
        try:
            return self._repository.get_by_id(week_id)
        except Exception as e:
            self._logger.error(f"Failed to get week {week_id}: {e}")
            return None
    
    @Slot(result='QVariant')
    def get_all_weeks(self) -> List[Dict[str, Any]]:
        """Get all weeks"""
        try:
            return self._repository.get_all()
        except Exception as e:
            self._logger.error(f"Failed to get all weeks: {e}")
            return []
    
    @Slot(result='QVariant')
    def get_bonus_weeks(self) -> List[Dict[str, Any]]:
        """Get all bonus weeks"""
        try:
            return self._repository.get_bonus_weeks()
        except Exception as e:
            self._logger.error(f"Failed to get bonus weeks: {e}")
            return []
    
    @Slot(int, result=bool)
    def is_bonus_week(self, week_id: int) -> bool:
        """Check if week is a bonus week"""
        try:
            week_data = self._repository.get_by_id(week_id)
            return week_data.get('is_bonus_week', 0) == 1 if week_data else False
        except Exception as e:
            self._logger.error(f"Failed to check bonus status for week {week_id}: {e}")
            return False
    
    # Event handlers
    def _on_week_created(self, event_data):
        """Handle week created event"""
        if hasattr(self._repository._data_service, 'clear_cache'):
            self._repository._data_service.clear_cache()
    
    def _on_week_updated(self, event_data):
        """Handle week updated event"""
        if hasattr(self._repository._data_service, 'clear_cache'):
            self._repository._data_service.clear_cache() 