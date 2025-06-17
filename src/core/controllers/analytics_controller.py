from PySide6.QtCore import QObject, Slot
from typing import List, Dict, Any, Optional
import logging
from ..events.event_bus import get_event_bus
from ..events.event_types import EventType
from ..repositories.analytics_repository import AnalyticsRepository

class AnalyticsController(QObject):
    """Controller for analytics and statistical operations"""
    
    def __init__(self, analytics_repository: AnalyticsRepository, parent=None):
        super().__init__(parent)
        self._repository = analytics_repository
        self._event_bus = get_event_bus()
        self._logger = logging.getLogger(__name__)
        
        # Connect to events
        self._event_bus.connect_handler(EventType.ANALYSIS_DATA_UPDATED, self._on_analysis_data_updated)
        self._event_bus.connect_handler(EventType.ANALYSIS_REFRESH_REQUESTED, self._on_analysis_requested)
        
        # Try to import Rust Statistical Analysis Engine
        try:
            from ..performance.rust_statistical_analysis_engine import RustStatisticalAnalysisEngine
            self._rust_stats = RustStatisticalAnalysisEngine()
            self._use_rust = True
            self._logger.info("Rust Statistical Analysis Engine loaded successfully")
        except ImportError:
            self._rust_stats = None
            self._use_rust = False
            self._logger.warning("Rust Statistical Analysis Engine not available, using Python fallback")
    
    @Slot(int, result='QVariant')
    def get_task_statistics(self, week_id: int = None) -> Dict[str, Any]:
        """Get comprehensive task statistics"""
        try:
            stats = self._repository.get_task_statistics(week_id)
            
            # Enhance with Rust calculations if available
            if self._use_rust and self._rust_stats and stats:
                try:
                    enhanced_stats = self._rust_stats.calculate_statistical_summary(
                        [stats.get('total_tasks', 0), stats.get('completed_tasks', 0)]
                    )
                    stats.update(enhanced_stats)
                except Exception as e:
                    self._logger.warning(f"Rust enhancement failed: {e}")
            
            self._event_bus.emit_event(
                EventType.ANALYSIS_DATA_UPDATED,
                {'analysis_type': 'task_statistics', 'data': stats, 'week_id': week_id},
                'AnalyticsController'
            )
            
            return stats
            
        except Exception as e:
            self._logger.error(f"Failed to get task statistics: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'get_task_statistics', 'error': str(e), 'week_id': week_id},
                'AnalyticsController'
            )
            return {}
    
    @Slot(int, result='QVariant')
    def get_project_statistics(self, week_id: int = None) -> List[Dict[str, Any]]:
        """Get statistics grouped by project"""
        try:
            project_stats = self._repository.get_project_statistics(week_id)
            
            self._event_bus.emit_event(
                EventType.ANALYSIS_DATA_UPDATED,
                {'analysis_type': 'project_statistics', 'data': project_stats, 'week_id': week_id},
                'AnalyticsController'
            )
            
            return project_stats
            
        except Exception as e:
            self._logger.error(f"Failed to get project statistics: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'get_project_statistics', 'error': str(e), 'week_id': week_id},
                'AnalyticsController'
            )
            return []
    
    @Slot(str, str, result='QVariant')
    def get_daily_statistics(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get daily task statistics within date range"""
        try:
            daily_stats = self._repository.get_daily_statistics(start_date, end_date)
            
            self._event_bus.emit_event(
                EventType.ANALYSIS_DATA_UPDATED,
                {'analysis_type': 'daily_statistics', 'data': daily_stats, 'start_date': start_date, 'end_date': end_date},
                'AnalyticsController'
            )
            
            return daily_stats
            
        except Exception as e:
            self._logger.error(f"Failed to get daily statistics: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'get_daily_statistics', 'error': str(e), 'start_date': start_date, 'end_date': end_date},
                'AnalyticsController'
            )
            return []
    
    @Slot(int, result='QVariant')
    def get_productivity_trends(self, weeks_back: int = 12) -> List[Dict[str, Any]]:
        """Get productivity trends for the last N weeks"""
        try:
            trends = self._repository.get_productivity_trends(weeks_back)
            
            self._event_bus.emit_event(
                EventType.ANALYSIS_DATA_UPDATED,
                {'analysis_type': 'productivity_trends', 'data': trends, 'weeks_back': weeks_back},
                'AnalyticsController'
            )
            
            return trends
            
        except Exception as e:
            self._logger.error(f"Failed to get productivity trends: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'get_productivity_trends', 'error': str(e), 'weeks_back': weeks_back},
                'AnalyticsController'
            )
            return []
    
    @Slot()
    def refresh_all_analytics(self):
        """Refresh all analytics data"""
        try:
            self._event_bus.emit_event(
                EventType.ANALYSIS_REFRESH_REQUESTED,
                {'refresh_type': 'all'},
                'AnalyticsController'
            )
            self._logger.info("Requested refresh of all analytics data")
        except Exception as e:
            self._logger.error(f"Failed to refresh analytics: {e}")
            self._event_bus.emit_event(
                EventType.ERROR_OCCURRED,
                {'operation': 'refresh_all_analytics', 'error': str(e)},
                'AnalyticsController'
            )
    
    # Event handlers
    def _on_analysis_data_updated(self, event_data):
        """Handle analysis data updated event"""
        self._logger.debug(f"Analysis data updated: {event_data.data.get('analysis_type', 'unknown')}")
    
    def _on_analysis_requested(self, event_data):
        """Handle analysis requested event"""
        self._logger.debug(f"Analysis requested: {event_data.data.get('refresh_type', 'unknown')}") 