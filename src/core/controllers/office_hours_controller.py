from PySide6.QtCore import QObject, Slot
import logging
from typing import Dict, Any
from ..events.event_bus import get_event_bus
from ..events.event_types import EventType
from ..repositories.week_repository import WeekRepository

class OfficeHoursController(QObject):
    """Controller for office hours operations"""
    
    def __init__(self, week_repository: WeekRepository, parent=None):
        super().__init__(parent)
        self._repository = week_repository
        self._event_bus = get_event_bus()
        self._logger = logging.getLogger(__name__)
        
        # Connect to events
        self._event_bus.connect_handler(EventType.WEEK_UPDATED, self._on_week_updated)
    
    @Slot(int, result=bool)
    def add_office_hour_session(self, week_id: int) -> bool:
        """Add office hour session to week"""
        try:
            current_count = self._repository.get_office_hour_count(week_id)
            new_count = current_count + 1
            success = self._repository.update_office_hour_count(week_id, new_count)
            
            if success:
                self._event_bus.emit_event(
                    EventType.WEEK_UPDATED,
                    {'week_id': week_id, 'field_name': 'office_hour_sessions', 'value': new_count, 'operation': 'add'},
                    'OfficeHoursController'
                )
                self._logger.info(f"Added office hour session to week {week_id}, total: {new_count}")
            
            return success
            
        except Exception as e:
            self._logger.error(f"Failed to add office hour session: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'add_office_hours', 'error': str(e), 'week_id': week_id},
                'OfficeHoursController'
            )
            return False
    
    @Slot(int, result=bool)
    def remove_office_hour_session(self, week_id: int) -> bool:
        """Remove office hour session from week"""
        try:
            current_count = self._repository.get_office_hour_count(week_id)
            if current_count <= 0:
                return False
            
            new_count = current_count - 1
            success = self._repository.update_office_hour_count(week_id, new_count)
            
            if success:
                self._event_bus.emit_event(
                    EventType.WEEK_UPDATED,
                    {'week_id': week_id, 'field_name': 'office_hour_sessions', 'value': new_count, 'operation': 'remove'},
                    'OfficeHoursController'
                )
                self._logger.info(f"Removed office hour session from week {week_id}, total: {new_count}")
            
            return success
            
        except Exception as e:
            self._logger.error(f"Failed to remove office hour session: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'remove_office_hours', 'error': str(e), 'week_id': week_id},
                'OfficeHoursController'
            )
            return False
    
    @Slot(int, int, result=bool)
    def set_office_hour_count(self, week_id: int, count: int) -> bool:
        """Set office hour count for week"""
        try:
            if count < 0:
                count = 0
            
            success = self._repository.update_office_hour_count(week_id, count)
            
            if success:
                self._event_bus.emit_event(
                    EventType.WEEK_UPDATED,
                    {'week_id': week_id, 'field_name': 'office_hour_sessions', 'value': count, 'operation': 'set'},
                    'OfficeHoursController'
                )
                self._logger.info(f"Set office hour count for week {week_id} to {count}")
            
            return success
            
        except Exception as e:
            self._logger.error(f"Failed to set office hour count: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'set_office_hours', 'error': str(e), 'week_id': week_id, 'count': count},
                'OfficeHoursController'
            )
            return False
    
    @Slot(int, result=int)
    def get_office_hour_count(self, week_id: int) -> int:
        """Get current office hour count for week"""
        try:
            return self._repository.get_office_hour_count(week_id)
        except Exception as e:
            self._logger.error(f"Failed to get office hour count: {e}")
            return 0
    
    @Slot(result='QVariant')
    def get_all_office_hours(self) -> Dict[int, int]:
        """Get office hour counts for all weeks"""
        try:
            weeks = self._repository.get_all()
            office_hours = {}
            for week in weeks:
                office_hours[week['id']] = week.get('office_hour_sessions', 0)
            return office_hours
        except Exception as e:
            self._logger.error(f"Failed to get all office hours: {e}")
            return {}
    
    @Slot(int, result=bool)
    def has_office_hours(self, week_id: int) -> bool:
        """Check if week has any office hours"""
        try:
            count = self._repository.get_office_hour_count(week_id)
            return count > 0
        except Exception as e:
            self._logger.error(f"Failed to check office hours: {e}")
            return False
    
    # Event handlers
    def _on_week_updated(self, event_data):
        """Handle week updated event"""
        if hasattr(self._repository._data_service, 'clear_cache'):
            self._repository._data_service.clear_cache() 