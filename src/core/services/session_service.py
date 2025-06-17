"""
Session Service for managing user session and UI state.
Provides session persistence and user preference management.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from .data_service import DataService


class SessionService:
    """Service for managing user session and UI state"""
    
    def __init__(self, data_service: DataService = None):
        self._data_service = data_service or DataService.get_instance()
    
    def save_window_state(self, window_geometry: Dict[str, int], 
                         selected_week_id: Optional[int] = None,
                         sidebar_collapsed: bool = False):
        """Save main window state"""
        state = {
            "window_geometry": window_geometry,
            "selected_week_id": selected_week_id,
            "sidebar_collapsed": sidebar_collapsed,
            "timestamp": datetime.now().isoformat()
        }
        
        self._data_service.session_manager.save_ui_state("main_window", state)
    
    def load_window_state(self) -> Optional[Dict[str, Any]]:
        """Load main window state"""
        return self._data_service.session_manager.load_ui_state("main_window")
    
    def save_task_grid_state(self, week_id: int, selected_task_ids: List[int],
                           sort_column: str = None, sort_order: str = None):
        """Save task grid state for specific week"""
        state = {
            "selected_task_ids": selected_task_ids,
            "sort_column": sort_column,
            "sort_order": sort_order,
            "timestamp": datetime.now().isoformat()
        }
        
        self._data_service.session_manager.save_ui_state(f"task_grid_week_{week_id}", state)
    
    def load_task_grid_state(self, week_id: int) -> Optional[Dict[str, Any]]:
        """Load task grid state for specific week"""
        return self._data_service.session_manager.load_ui_state(f"task_grid_week_{week_id}")
    
    def save_analysis_preferences(self, chart_types: List[str], 
                                date_range: Dict[str, str],
                                filters: Dict[str, Any]):
        """Save analysis widget preferences"""
        prefs = self._data_service.session_manager.load_user_preferences()
        prefs.update({
            "analysis": {
                "preferred_chart_types": chart_types,
                "default_date_range": date_range,
                "default_filters": filters,
                "last_updated": datetime.now().isoformat()
            }
        })
        
        self._data_service.session_manager.save_user_preferences(prefs)
    
    def load_analysis_preferences(self) -> Dict[str, Any]:
        """Load analysis widget preferences"""
        prefs = self._data_service.session_manager.load_user_preferences()
        return prefs.get("analysis", {})
    
    def save_export_preferences(self, export_format: str, 
                              default_path: str,
                              include_analytics: bool = True):
        """Save export preferences"""
        prefs = self._data_service.session_manager.load_user_preferences()
        prefs.update({
            "export": {
                "default_format": export_format,
                "default_path": default_path,
                "include_analytics": include_analytics,
                "last_updated": datetime.now().isoformat()
            }
        })
        
        self._data_service.session_manager.save_user_preferences(prefs)
    
    def load_export_preferences(self) -> Dict[str, Any]:
        """Load export preferences"""
        prefs = self._data_service.session_manager.load_user_preferences()
        return prefs.get("export", {})
    
    def save_ui_theme_preferences(self, theme: str, font_size: int = 10):
        """Save UI theme preferences"""
        prefs = self._data_service.session_manager.load_user_preferences()
        prefs.update({
            "ui_theme": {
                "theme": theme,
                "font_size": font_size,
                "last_updated": datetime.now().isoformat()
            }
        })
        
        self._data_service.session_manager.save_user_preferences(prefs)
    
    def load_ui_theme_preferences(self) -> Dict[str, Any]:
        """Load UI theme preferences"""
        prefs = self._data_service.session_manager.load_user_preferences()
        return prefs.get("ui_theme", {"theme": "default", "font_size": 10})
    
    def save_recent_files(self, file_paths: List[str], max_recent: int = 10):
        """Save recently opened files"""
        # Limit to max_recent files
        recent_files = file_paths[:max_recent]
        
        prefs = self._data_service.session_manager.load_user_preferences()
        prefs.update({
            "recent_files": {
                "files": recent_files,
                "last_updated": datetime.now().isoformat()
            }
        })
        
        self._data_service.session_manager.save_user_preferences(prefs)
    
    def load_recent_files(self) -> List[str]:
        """Load recently opened files"""
        prefs = self._data_service.session_manager.load_user_preferences()
        recent_data = prefs.get("recent_files", {})
        return recent_data.get("files", [])
    
    def add_recent_file(self, file_path: str, max_recent: int = 10):
        """Add a file to recent files list"""
        recent_files = self.load_recent_files()
        
        # Remove if already exists
        if file_path in recent_files:
            recent_files.remove(file_path)
        
        # Add to beginning
        recent_files.insert(0, file_path)
        
        # Save updated list
        self.save_recent_files(recent_files, max_recent)
    
    def save_dialog_state(self, dialog_name: str, state: Dict[str, Any]):
        """Save dialog state (position, size, last values)"""
        self._data_service.session_manager.save_ui_state(f"dialog_{dialog_name}", {
            **state,
            "timestamp": datetime.now().isoformat()
        })
    
    def load_dialog_state(self, dialog_name: str) -> Optional[Dict[str, Any]]:
        """Load dialog state"""
        return self._data_service.session_manager.load_ui_state(f"dialog_{dialog_name}")
    
    def save_search_history(self, search_terms: List[str], max_history: int = 20):
        """Save search history"""
        # Remove duplicates while preserving order
        unique_terms = []
        for term in search_terms:
            if term not in unique_terms:
                unique_terms.append(term)
        
        # Limit to max_history
        search_history = unique_terms[:max_history]
        
        prefs = self._data_service.session_manager.load_user_preferences()
        prefs.update({
            "search_history": {
                "terms": search_history,
                "last_updated": datetime.now().isoformat()
            }
        })
        
        self._data_service.session_manager.save_user_preferences(prefs)
    
    def load_search_history(self) -> List[str]:
        """Load search history"""
        prefs = self._data_service.session_manager.load_user_preferences()
        search_data = prefs.get("search_history", {})
        return search_data.get("terms", [])
    
    def add_search_term(self, search_term: str, max_history: int = 20):
        """Add a search term to history"""
        if not search_term.strip():
            return
        
        search_history = self.load_search_history()
        
        # Remove if already exists
        if search_term in search_history:
            search_history.remove(search_term)
        
        # Add to beginning
        search_history.insert(0, search_term)
        
        # Save updated history
        self.save_search_history(search_history, max_history)
    
    def save_performance_settings(self, cache_enabled: bool = True,
                                analytics_cache_ttl: int = 3600,
                                task_cache_ttl: int = 1800):
        """Save performance-related settings"""
        prefs = self._data_service.session_manager.load_user_preferences()
        prefs.update({
            "performance": {
                "cache_enabled": cache_enabled,
                "analytics_cache_ttl": analytics_cache_ttl,
                "task_cache_ttl": task_cache_ttl,
                "last_updated": datetime.now().isoformat()
            }
        })
        
        self._data_service.session_manager.save_user_preferences(prefs)
    
    def load_performance_settings(self) -> Dict[str, Any]:
        """Load performance settings"""
        prefs = self._data_service.session_manager.load_user_preferences()
        return prefs.get("performance", {
            "cache_enabled": True,
            "analytics_cache_ttl": 3600,
            "task_cache_ttl": 1800
        })
    
    def clear_session_data(self):
        """Clear all session data (UI state, not preferences)"""
        # This would clear temporary UI state but keep user preferences
        if self._data_service.cache_manager._redis_available:
            try:
                keys = self._data_service.cache_manager._redis_client.keys("auditor_helper:ui_state:*")
                if keys:
                    self._data_service.cache_manager._redis_client.delete(*keys)
            except Exception as e:
                # Log error but don't fail
                pass
    
    def clear_all_preferences(self):
        """Clear all user preferences (use with caution)"""
        if self._data_service.cache_manager._redis_available:
            try:
                self._data_service.cache_manager._redis_client.delete("auditor_helper:user_preferences")
            except Exception as e:
                # Log error but don't fail
                pass
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get information about current session"""
        return {
            "redis_available": self._data_service.cache_manager._redis_available,
            "cache_stats": self._data_service.cache_manager.get_cache_stats(),
            "has_window_state": self.load_window_state() is not None,
            "has_preferences": bool(self._data_service.session_manager.load_user_preferences()),
            "recent_files_count": len(self.load_recent_files()),
            "search_history_count": len(self.load_search_history())
        } 