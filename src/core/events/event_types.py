"""
Event Types for Auditor Helper Application

This module defines all the event types used throughout the application
for the centralized event bus system.
"""

from enum import Enum


class EventType(Enum):
    """Enumeration of all application event types"""
    
    # Task-related events
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated" 
    TASK_DELETED = "task_deleted"
    TASKS_BULK_UPDATED = "tasks_bulk_updated"
    TASK_SELECTION_CHANGED = "task_selection_changed"
    
    # Week-related events
    WEEK_CHANGED = "week_changed"
    WEEK_CREATED = "week_created"
    WEEK_UPDATED = "week_updated"
    WEEK_DELETED = "week_deleted"
    
    # Timer-related events
    TIMER_STARTED = "timer_started"
    TIMER_STOPPED = "timer_stopped"
    TIMER_UPDATED = "timer_updated"
    TIMER_PAUSED = "timer_paused"
    TIMER_RESUMED = "timer_resumed"
    
    # Analysis-related events
    ANALYSIS_REFRESH_REQUESTED = "analysis_refresh_requested"
    ANALYSIS_DATA_UPDATED = "analysis_data_updated"
    ANALYSIS_SETTINGS_CHANGED = "analysis_settings_changed"
    
    # UI-related events
    UI_REFRESH_REQUESTED = "ui_refresh_requested"
    DELETE_BUTTON_UPDATE_REQUESTED = "delete_button_update_requested"
    SELECTION_UPDATE_REQUESTED = "selection_update_requested"
    THEME_CHANGED = "theme_changed"
    
    # Data-related events
    DATA_IMPORTED = "data_imported"
    DATA_EXPORTED = "data_exported"
    DATABASE_UPDATED = "database_updated"
    DATABASE_ERROR = "database_error"
    
    # Application-level events
    APP_STARTUP = "app_startup"
    APP_SHUTDOWN = "app_shutdown"
    SETTINGS_CHANGED = "settings_changed"
    ERROR_OCCURRED = "error_occurred"
    
    # Performance monitoring events
    PERFORMANCE_METRIC_RECORDED = "performance_metric_recorded"
    CACHE_UPDATED = "cache_updated"
    
    def __str__(self):
        return self.value
    
    @classmethod
    def get_task_events(cls):
        """Get all task-related event types"""
        return [
            cls.TASK_CREATED,
            cls.TASK_UPDATED,
            cls.TASK_DELETED,
            cls.TASKS_BULK_UPDATED,
            cls.TASK_SELECTION_CHANGED
        ]
    
    @classmethod
    def get_week_events(cls):
        """Get all week-related event types"""
        return [
            cls.WEEK_CHANGED,
            cls.WEEK_CREATED,
            cls.WEEK_UPDATED,
            cls.WEEK_DELETED
        ]
    
    @classmethod
    def get_timer_events(cls):
        """Get all timer-related event types"""
        return [
            cls.TIMER_STARTED,
            cls.TIMER_STOPPED,
            cls.TIMER_UPDATED,
            cls.TIMER_PAUSED,
            cls.TIMER_RESUMED
        ]
    
    @classmethod
    def get_analysis_events(cls):
        """Get all analysis-related event types"""
        return [
            cls.ANALYSIS_REFRESH_REQUESTED,
            cls.ANALYSIS_DATA_UPDATED,
            cls.ANALYSIS_SETTINGS_CHANGED
        ] 