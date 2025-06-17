"""
Central Event Bus for Auditor Helper Application

This module provides the core event bus implementation using Qt signals/slots
for decoupled communication between application components.
"""

import logging
from typing import Any, Dict, Callable, Optional
from PySide6 import QtCore
from .event_types import EventType


class EventData:
    """Container for event data and metadata"""
    
    def __init__(self, event_type: EventType, data: Dict[str, Any] = None, source: str = None):
        """
        Initialize event data
        
        Args:
            event_type: The type of event
            data: Dictionary containing event-specific data
            source: String identifying the source component
        """
        self.event_type = event_type
        self.data = data or {}
        self.source = source
        self.timestamp = QtCore.QDateTime.currentDateTime()
    
    def __repr__(self):
        return f"EventData(type={self.event_type.value}, source={self.source}, data_keys={list(self.data.keys())})"


class AppEventBus(QtCore.QObject):
    """
    Central event bus for application-wide communication
    
    Uses Qt signals/slots for efficient, type-safe event handling.
    Implements singleton pattern for global access.
    """
    
    # Define signals for each event type
    # Task-related signals
    task_created = QtCore.Signal(EventData)
    task_updated = QtCore.Signal(EventData)
    task_deleted = QtCore.Signal(EventData)
    tasks_bulk_updated = QtCore.Signal(EventData)
    task_selection_changed = QtCore.Signal(EventData)
    
    # Week-related signals
    week_changed = QtCore.Signal(EventData)
    week_created = QtCore.Signal(EventData)
    week_updated = QtCore.Signal(EventData)
    week_deleted = QtCore.Signal(EventData)
    
    # Timer-related signals
    timer_started = QtCore.Signal(EventData)
    timer_stopped = QtCore.Signal(EventData)
    timer_updated = QtCore.Signal(EventData)
    timer_paused = QtCore.Signal(EventData)
    timer_resumed = QtCore.Signal(EventData)
    
    # Analysis-related signals
    analysis_refresh_requested = QtCore.Signal(EventData)
    analysis_data_updated = QtCore.Signal(EventData)
    analysis_settings_changed = QtCore.Signal(EventData)
    
    # UI-related signals
    ui_refresh_requested = QtCore.Signal(EventData)
    delete_button_update_requested = QtCore.Signal(EventData)
    selection_update_requested = QtCore.Signal(EventData)
    theme_changed = QtCore.Signal(EventData)
    
    # Data-related signals
    data_imported = QtCore.Signal(EventData)
    data_exported = QtCore.Signal(EventData)
    database_updated = QtCore.Signal(EventData)
    database_error = QtCore.Signal(EventData)
    
    # Application-level signals
    app_startup = QtCore.Signal(EventData)
    app_shutdown = QtCore.Signal(EventData)
    settings_changed = QtCore.Signal(EventData)
    error_occurred = QtCore.Signal(EventData)
    
    # Performance monitoring signals
    performance_metric_recorded = QtCore.Signal(EventData)
    cache_updated = QtCore.Signal(EventData)
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self._event_count = 0
        self._debug_mode = False
        
        # Create mapping from event types to signals
        self._signal_map = {
            # Task events
            EventType.TASK_CREATED: self.task_created,
            EventType.TASK_UPDATED: self.task_updated,
            EventType.TASK_DELETED: self.task_deleted,
            EventType.TASKS_BULK_UPDATED: self.tasks_bulk_updated,
            EventType.TASK_SELECTION_CHANGED: self.task_selection_changed,
            
            # Week events
            EventType.WEEK_CHANGED: self.week_changed,
            EventType.WEEK_CREATED: self.week_created,
            EventType.WEEK_UPDATED: self.week_updated,
            EventType.WEEK_DELETED: self.week_deleted,
            
            # Timer events
            EventType.TIMER_STARTED: self.timer_started,
            EventType.TIMER_STOPPED: self.timer_stopped,
            EventType.TIMER_UPDATED: self.timer_updated,
            EventType.TIMER_PAUSED: self.timer_paused,
            EventType.TIMER_RESUMED: self.timer_resumed,
            
            # Analysis events
            EventType.ANALYSIS_REFRESH_REQUESTED: self.analysis_refresh_requested,
            EventType.ANALYSIS_DATA_UPDATED: self.analysis_data_updated,
            EventType.ANALYSIS_SETTINGS_CHANGED: self.analysis_settings_changed,
            
            # UI events
            EventType.UI_REFRESH_REQUESTED: self.ui_refresh_requested,
            EventType.DELETE_BUTTON_UPDATE_REQUESTED: self.delete_button_update_requested,
            EventType.SELECTION_UPDATE_REQUESTED: self.selection_update_requested,
            EventType.THEME_CHANGED: self.theme_changed,
            
            # Data events
            EventType.DATA_IMPORTED: self.data_imported,
            EventType.DATA_EXPORTED: self.data_exported,
            EventType.DATABASE_UPDATED: self.database_updated,
            EventType.DATABASE_ERROR: self.database_error,
            
            # Application events
            EventType.APP_STARTUP: self.app_startup,
            EventType.APP_SHUTDOWN: self.app_shutdown,
            EventType.SETTINGS_CHANGED: self.settings_changed,
            EventType.ERROR_OCCURRED: self.error_occurred,
            
            # Performance events
            EventType.PERFORMANCE_METRIC_RECORDED: self.performance_metric_recorded,
            EventType.CACHE_UPDATED: self.cache_updated,
        }
        
        self.logger.info("Event bus initialized")
    
    def set_debug_mode(self, enabled: bool):
        """Enable or disable debug logging for events"""
        self._debug_mode = enabled
        if enabled:
            self.logger.setLevel(logging.DEBUG)
            self.logger.debug("Event bus debug mode enabled")
        else:
            self.logger.debug("Event bus debug mode disabled")
    
    def emit_event(self, event_type: EventType, data: Dict[str, Any] = None, source: str = None):
        """
        Emit an event through the bus
        
        Args:
            event_type: The type of event to emit
            data: Optional dictionary containing event-specific data
            source: Optional string identifying the source component
        """
        try:
            event_data = EventData(event_type, data, source)
            
            if event_type in self._signal_map:
                signal = self._signal_map[event_type]
                signal.emit(event_data)
                
                self._event_count += 1
                
                if self._debug_mode:
                    self.logger.debug(
                        f"Event #{self._event_count} emitted: {event_type.value} "
                        f"from {source or 'unknown'} with data: {data}"
                    )
                else:
                    self.logger.debug(f"Event emitted: {event_type.value} from {source or 'unknown'}")
                    
            else:
                self.logger.warning(f"Unknown event type: {event_type}")
                
        except Exception as e:
            self.logger.error(f"Error emitting event {event_type}: {e}")
    
    def connect_handler(self, event_type: EventType, handler: Callable[[EventData], None]):
        """
        Connect a handler function to an event type
        
        Args:
            event_type: The event type to listen for
            handler: Function to call when event is emitted
        """
        try:
            if event_type in self._signal_map:
                signal = self._signal_map[event_type]
                signal.connect(handler)
                self.logger.debug(f"Handler connected to {event_type.value}")
            else:
                self.logger.warning(f"Cannot connect to unknown event type: {event_type}")
                
        except Exception as e:
            self.logger.error(f"Error connecting handler to {event_type}: {e}")
    
    def disconnect_handler(self, event_type: EventType, handler: Callable[[EventData], None]):
        """
        Disconnect a handler function from an event type
        
        Args:
            event_type: The event type to stop listening for
            handler: Function to disconnect
        """
        try:
            if event_type in self._signal_map:
                signal = self._signal_map[event_type]
                signal.disconnect(handler)
                self.logger.debug(f"Handler disconnected from {event_type.value}")
            else:
                self.logger.warning(f"Cannot disconnect from unknown event type: {event_type}")
                
        except Exception as e:
            self.logger.error(f"Error disconnecting handler from {event_type}: {e}")
    
    def disconnect_all_handlers(self, event_type: EventType):
        """
        Disconnect all handlers from an event type
        
        Args:
            event_type: The event type to clear all handlers from
        """
        try:
            if event_type in self._signal_map:
                signal = self._signal_map[event_type]
                signal.disconnect()
                self.logger.debug(f"All handlers disconnected from {event_type.value}")
            else:
                self.logger.warning(f"Cannot disconnect from unknown event type: {event_type}")
                
        except Exception as e:
            self.logger.error(f"Error disconnecting all handlers from {event_type}: {e}")
    
    def get_event_count(self) -> int:
        """Get the total number of events emitted"""
        return self._event_count
    
    def reset_event_count(self):
        """Reset the event counter"""
        self._event_count = 0
        self.logger.debug("Event counter reset")
    
    def get_connected_event_types(self) -> list:
        """Get list of event types that have connected handlers"""
        connected_types = []
        for event_type, signal in self._signal_map.items():
            # Check if signal has any connections by trying to emit and catching
            # Note: PySide6 doesn't have a direct way to check receiver count
            # This is a simplified implementation for monitoring purposes
            try:
                # We'll track this differently - for now return all event types
                # that have been used (this is mainly for debugging/monitoring)
                connected_types.append(event_type)
            except Exception:
                pass
        return connected_types


# Singleton instance
_event_bus_instance: Optional[AppEventBus] = None


def get_event_bus() -> AppEventBus:
    """
    Get the singleton event bus instance
    
    Returns:
        The global AppEventBus instance
    """
    global _event_bus_instance
    if _event_bus_instance is None:
        _event_bus_instance = AppEventBus()
    return _event_bus_instance


def reset_event_bus():
    """
    Reset the singleton event bus instance (primarily for testing)
    """
    global _event_bus_instance
    if _event_bus_instance is not None:
        # Simply create a new instance instead of trying to disconnect all signals
        # This avoids warnings about disconnecting signals with no connections
        pass
    _event_bus_instance = None 