"""
Task Data Access Object with intelligent caching.
Provides high-level task operations with automatic cache management.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
from .data_service import DataService


class TaskDAO:
    """Enhanced Task Data Access Object with intelligent caching"""
    
    def __init__(self, data_service: DataService = None):
        self._data_service = data_service or DataService.get_instance()
    
    def get_tasks_by_week(self, week_id: int, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get all tasks for a week with caching"""
        query = "SELECT * FROM tasks WHERE week_id = ? ORDER BY id"
        
        # Use longer cache TTL for task lists (they don't change frequently)
        return self._data_service.execute_query(
            query, (week_id,), use_cache=use_cache, cache_ttl=1800  # 30 minutes
        )
    
    def get_tasks_with_analytics(self, week_id: int = None) -> List[Dict[str, Any]]:
        """Get tasks with additional analytics data"""
        if week_id:
            query = """
            SELECT t.*, w.week_label, w.is_bonus_week,
                   CASE WHEN t.score >= 3 THEN 1 ELSE 0 END as is_high_score,
                   CAST(substr(t.duration, 1, 2) AS INTEGER) * 3600 + 
                   CAST(substr(t.duration, 4, 2) AS INTEGER) * 60 + 
                   CAST(substr(t.duration, 7, 2) AS INTEGER) as duration_seconds
            FROM tasks t 
            JOIN weeks w ON t.week_id = w.id 
            WHERE t.week_id = ?
            ORDER BY t.id
            """
            params = (week_id,)
        else:
            query = """
            SELECT t.*, w.week_label, w.is_bonus_week,
                   CASE WHEN t.score >= 3 THEN 1 ELSE 0 END as is_high_score,
                   CAST(substr(t.duration, 1, 2) AS INTEGER) * 3600 + 
                   CAST(substr(t.duration, 4, 2) AS INTEGER) * 60 + 
                   CAST(substr(t.duration, 7, 2) AS INTEGER) as duration_seconds
            FROM tasks t 
            JOIN weeks w ON t.week_id = w.id 
            ORDER BY t.date_audited DESC, t.id
            """
            params = ()
        
        # Cache analytics queries for longer (they're expensive)
        return self._data_service.execute_query(
            query, params, use_cache=True, cache_ttl=3600  # 1 hour
        )
    
    def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get single task by ID"""
        query = "SELECT * FROM tasks WHERE id = ?"
        results = self._data_service.execute_query(query, (task_id,))
        return results[0] if results else None
    
    def get_tasks_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get tasks within date range"""
        query = """
        SELECT t.*, w.week_label 
        FROM tasks t 
        JOIN weeks w ON t.week_id = w.id 
        WHERE t.date_audited BETWEEN ? AND ? 
        ORDER BY t.date_audited DESC
        """
        return self._data_service.execute_query(
            query, (start_date, end_date), use_cache=True, cache_ttl=1800
        )
    
    def get_tasks_by_project(self, project_name: str) -> List[Dict[str, Any]]:
        """Get tasks by project name"""
        query = """
        SELECT t.*, w.week_label 
        FROM tasks t 
        JOIN weeks w ON t.week_id = w.id 
        WHERE t.project_name = ? 
        ORDER BY t.date_audited DESC
        """
        return self._data_service.execute_query(
            query, (project_name,), use_cache=True, cache_ttl=1800
        )
    
    def get_high_score_tasks(self, min_score: int = 3) -> List[Dict[str, Any]]:
        """Get tasks with high scores"""
        query = """
        SELECT t.*, w.week_label 
        FROM tasks t 
        JOIN weeks w ON t.week_id = w.id 
        WHERE t.score >= ? 
        ORDER BY t.score DESC, t.date_audited DESC
        """
        return self._data_service.execute_query(
            query, (min_score,), use_cache=True, cache_ttl=3600
        )
    
    def create_task(self, week_id: int, **kwargs) -> int:
        """Create new task with automatic cache invalidation"""
        default_values = {
            'attempt_id': '',
            'duration': '00:00:00',
            'project_id': '',
            'project_name': '',
            'operation_id': '',
            'time_limit': '00:00:00',
            'date_audited': datetime.now().strftime("%Y-%m-%d"),
            'score': 1,
            'feedback': '',
            'locale': '',
            'bonus_paid': 0,
            'time_begin': '',
            'time_end': ''
        }
        
        values = {**default_values, **kwargs, 'week_id': week_id}
        columns = ', '.join(values.keys())
        placeholders = ', '.join(['?' for _ in values])
        command = f"INSERT INTO tasks ({columns}) VALUES ({placeholders})"
        
        task_id = self._data_service.execute_command(command, tuple(values.values()))
        
        # Invalidate analytics cache when new task is created
        self._data_service.invalidate_analytics_cache()
        
        return task_id
    
    def update_task(self, task_id: int, **kwargs) -> bool:
        """Update task with cache invalidation"""
        if not kwargs:
            return True
        
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        command = f"UPDATE tasks SET {set_clause} WHERE id = ?"
        params = tuple(kwargs.values()) + (task_id,)
        
        affected_rows = self._data_service.execute_command(command, params)
        
        # Invalidate analytics cache when task is updated
        if affected_rows > 0:
            self._data_service.invalidate_analytics_cache()
        
        return affected_rows > 0
    
    def delete_task(self, task_id: int) -> bool:
        """Delete single task"""
        command = "DELETE FROM tasks WHERE id = ?"
        affected_rows = self._data_service.execute_command(command, (task_id,))
        
        if affected_rows > 0:
            self._data_service.invalidate_analytics_cache()
        
        return affected_rows > 0
    
    def delete_multiple_tasks(self, task_ids: List[int]) -> int:
        """Delete multiple tasks with cache invalidation"""
        if not task_ids:
            return 0
        
        placeholders = ', '.join(['?' for _ in task_ids])
        command = f"DELETE FROM tasks WHERE id IN ({placeholders})"
        deleted_count = self._data_service.execute_command(command, tuple(task_ids))
        
        # Invalidate analytics cache when tasks are deleted
        if deleted_count > 0:
            self._data_service.invalidate_analytics_cache()
        
        return deleted_count
    
    def get_task_statistics(self, week_id: int = None) -> Dict[str, Any]:
        """Get task statistics with caching"""
        if week_id:
            query = """
            SELECT 
                COUNT(*) as total_tasks,
                AVG(score) as avg_score,
                MAX(score) as max_score,
                MIN(score) as min_score,
                COUNT(CASE WHEN score >= 3 THEN 1 END) as high_score_count,
                SUM(bonus_paid) as total_bonus
            FROM tasks 
            WHERE week_id = ?
            """
            params = (week_id,)
        else:
            query = """
            SELECT 
                COUNT(*) as total_tasks,
                AVG(score) as avg_score,
                MAX(score) as max_score,
                MIN(score) as min_score,
                COUNT(CASE WHEN score >= 3 THEN 1 END) as high_score_count,
                SUM(bonus_paid) as total_bonus
            FROM tasks
            """
            params = ()
        
        results = self._data_service.execute_query(
            query, params, use_cache=True, cache_ttl=1800
        )
        return results[0] if results else {}
    
    def bulk_update_tasks(self, updates: List[Dict[str, Any]]) -> int:
        """Bulk update tasks within a transaction"""
        updated_count = 0
        
        with self._data_service.transaction():
            for update in updates:
                task_id = update.pop('id')
                if self.update_task(task_id, **update):
                    updated_count += 1
        
        return updated_count
    
    def duplicate_task(self, task_id: int, new_week_id: int = None) -> Optional[int]:
        """Duplicate an existing task"""
        # Get original task
        original_task = self.get_task_by_id(task_id)
        if not original_task:
            return None
        
        # Remove ID and update week if specified
        task_data = dict(original_task)
        task_data.pop('id')
        if new_week_id:
            task_data['week_id'] = new_week_id
        
        # Create new task
        return self.create_task(**task_data)
    
    def get_tasks_by_date(self, date: str, week_id: int = None) -> List[Dict[str, Any]]:
        """Get tasks for a specific date, optionally filtered by week"""
        if week_id:
            query = """
            SELECT duration, time_limit, score, project_name, locale, date_audited, time_begin, time_end
            FROM tasks
            WHERE week_id = ? AND date_audited = ?
            ORDER BY id
            """
            params = (week_id, date)
        else:
            query = """
            SELECT duration, time_limit, score, project_name, locale, date_audited, time_begin, time_end
            FROM tasks
            WHERE date_audited = ?
            ORDER BY id
            """
            params = (date,)
        
        return self._data_service.execute_query(
            query, params, use_cache=True, cache_ttl=1800
        ) 