"""
Week Data Access Object with intelligent caching.
Provides high-level week operations with automatic cache management.
"""

from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
from .data_service import DataService


class WeekDAO:
    """Enhanced Week Data Access Object with intelligent caching"""
    
    def __init__(self, data_service: DataService = None):
        self._data_service = data_service or DataService.get_instance()
    
    def get_all_weeks(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        """Get all weeks ordered by ID"""
        query = "SELECT * FROM weeks ORDER BY id"
        return self._data_service.execute_query(
            query, (), use_cache=use_cache, cache_ttl=3600  # 1 hour
        )
    
    def get_week_by_id(self, week_id: int) -> Optional[Dict[str, Any]]:
        """Get single week by ID"""
        query = "SELECT * FROM weeks WHERE id = ?"
        results = self._data_service.execute_query(query, (week_id,))
        return results[0] if results else None
    
    def get_week_by_label(self, week_label: str) -> Optional[Dict[str, Any]]:
        """Get week by label"""
        query = "SELECT * FROM weeks WHERE week_label = ?"
        results = self._data_service.execute_query(query, (week_label,))
        return results[0] if results else None
    
    def get_bonus_weeks(self) -> List[Dict[str, Any]]:
        """Get all bonus weeks"""
        query = "SELECT * FROM weeks WHERE is_bonus_week = 1 ORDER BY id"
        return self._data_service.execute_query(
            query, (), use_cache=True, cache_ttl=3600
        )
    
    def get_regular_weeks(self) -> List[Dict[str, Any]]:
        """Get all regular (non-bonus) weeks"""
        query = "SELECT * FROM weeks WHERE is_bonus_week = 0 ORDER BY id"
        return self._data_service.execute_query(
            query, (), use_cache=True, cache_ttl=3600
        )
    
    def get_weeks_with_task_counts(self) -> List[Dict[str, Any]]:
        """Get weeks with task counts"""
        query = """
        SELECT w.*, 
               COUNT(t.id) as task_count,
               COALESCE(AVG(t.score), 0) as avg_score,
               COALESCE(SUM(t.bonus_paid), 0) as total_bonus
        FROM weeks w 
        LEFT JOIN tasks t ON w.id = t.week_id 
        GROUP BY w.id 
        ORDER BY w.id
        """
        return self._data_service.execute_query(
            query, (), use_cache=True, cache_ttl=1800  # 30 minutes
        )
    
    def get_recent_weeks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent weeks"""
        query = "SELECT * FROM weeks ORDER BY id DESC LIMIT ?"
        return self._data_service.execute_query(
            query, (limit,), use_cache=True, cache_ttl=1800
        )
    
    def create_week(self, week_data: Dict[str, Any] = None, week_label: str = None, is_bonus_week: bool = False, **kwargs) -> int:
        """
        Create new week with automatic cache invalidation
        
        Args:
            week_data: Dictionary containing week data (preferred method)
            week_label: Week label (legacy parameter)
            is_bonus_week: Whether this is a bonus week (legacy parameter)
            **kwargs: Additional week fields
        """
        # Handle both dictionary and legacy parameter formats
        if week_data:
            # Use dictionary format (preferred)
            values = week_data.copy()
        else:
            # Use legacy parameter format for backward compatibility
            values = {
                'week_label': week_label,
                'is_bonus_week': 1 if is_bonus_week else 0,
                **kwargs
            }
        
        # Add default values if not provided
        if 'created_at' not in values:
            values['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Convert boolean to integer for is_bonus_week if needed
        if 'is_bonus_week' in values and isinstance(values['is_bonus_week'], bool):
            values['is_bonus_week'] = 1 if values['is_bonus_week'] else 0
        
        # Convert boolean to integer for is_custom_duration if needed
        if 'is_custom_duration' in values and isinstance(values['is_custom_duration'], bool):
            values['is_custom_duration'] = 1 if values['is_custom_duration'] else 0
        
        columns = ', '.join(values.keys())
        placeholders = ', '.join(['?' for _ in values])
        command = f"INSERT INTO weeks ({columns}) VALUES ({placeholders})"
        
        week_id = self._data_service.execute_command(command, tuple(values.values()))
        
        # Invalidate analytics cache when new week is created
        self._data_service.invalidate_analytics_cache()
        
        return week_id
    
    def update_week(self, week_id: int, **kwargs) -> bool:
        """Update week with cache invalidation"""
        if not kwargs:
            return True
        
        set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
        command = f"UPDATE weeks SET {set_clause} WHERE id = ?"
        params = tuple(kwargs.values()) + (week_id,)
        
        affected_rows = self._data_service.execute_command(command, params)
        
        # Invalidate analytics cache when week is updated
        if affected_rows > 0:
            self._data_service.invalidate_analytics_cache()
        
        return affected_rows > 0
    
    def delete_week(self, week_id: int, cascade: bool = False) -> bool:
        """
        Delete week with optional cascade to tasks
        
        Args:
            week_id: ID of week to delete
            cascade: If True, also delete all tasks in this week
        """
        if cascade:
            with self._data_service.transaction():
                # Delete tasks first
                self._data_service.execute_command(
                    "DELETE FROM tasks WHERE week_id = ?", (week_id,)
                )
                # Then delete week
                affected_rows = self._data_service.execute_command(
                    "DELETE FROM weeks WHERE id = ?", (week_id,)
                )
        else:
            # Check if week has tasks
            task_count_query = "SELECT COUNT(*) as count FROM tasks WHERE week_id = ?"
            result = self._data_service.execute_query(task_count_query, (week_id,))
            if result and result[0]['count'] > 0:
                raise ValueError(f"Cannot delete week {week_id}: contains {result[0]['count']} tasks. Use cascade=True to delete tasks as well.")
            
            affected_rows = self._data_service.execute_command(
                "DELETE FROM weeks WHERE id = ?", (week_id,)
            )
        
        if affected_rows > 0:
            self._data_service.invalidate_analytics_cache()
        
        return affected_rows > 0
    
    def increment_office_hours(self, week_id: int) -> bool:
        """Increment office hour count for a week with cache invalidation"""
        command = "UPDATE weeks SET office_hour_count = office_hour_count + 1 WHERE id = ?"
        affected_rows = self._data_service.execute_command(command, (week_id,))
        return affected_rows > 0
    
    def decrement_office_hours(self, week_id: int) -> bool:
        """Decrement office hour count for a week (minimum 0) with cache invalidation"""
        command = "UPDATE weeks SET office_hour_count = MAX(0, office_hour_count - 1) WHERE id = ?"
        affected_rows = self._data_service.execute_command(command, (week_id,))
        return affected_rows > 0
    
    def get_week_statistics(self, week_id: int) -> Dict[str, Any]:
        """Get comprehensive statistics for a week"""
        query = """
        SELECT 
            w.*,
            COUNT(t.id) as task_count,
            COALESCE(AVG(t.score), 0) as avg_score,
            COALESCE(MAX(t.score), 0) as max_score,
            COALESCE(MIN(t.score), 0) as min_score,
            COUNT(CASE WHEN t.score >= 3 THEN 1 END) as high_score_count,
            COALESCE(SUM(t.bonus_paid), 0) as total_bonus,
            COUNT(DISTINCT t.project_name) as unique_projects,
            COUNT(DISTINCT t.operation_id) as unique_operations
        FROM weeks w 
        LEFT JOIN tasks t ON w.id = t.week_id 
        WHERE w.id = ?
        GROUP BY w.id
        """
        results = self._data_service.execute_query(
            query, (week_id,), use_cache=True, cache_ttl=1800
        )
        return results[0] if results else {}
    
    def get_weeks_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get weeks created within date range"""
        query = """
        SELECT * FROM weeks 
        WHERE created_at BETWEEN ? AND ? 
        ORDER BY created_at DESC
        """
        return self._data_service.execute_query(
            query, (start_date, end_date), use_cache=True, cache_ttl=1800
        )
    
    def search_weeks(self, search_term: str) -> List[Dict[str, Any]]:
        """Search weeks by label"""
        query = """
        SELECT * FROM weeks 
        WHERE week_label LIKE ? 
        ORDER BY id DESC
        """
        search_pattern = f"%{search_term}%"
        return self._data_service.execute_query(
            query, (search_pattern,), use_cache=True, cache_ttl=1800
        )
    
    def get_next_week_number(self) -> int:
        """Get the next week number for creating new weeks"""
        query = "SELECT MAX(id) as max_id FROM weeks"
        results = self._data_service.execute_query(query, ())
        max_id = results[0]['max_id'] if results and results[0]['max_id'] else 0
        return max_id + 1
    
    def get_week_performance_summary(self) -> List[Dict[str, Any]]:
        """Get performance summary for all weeks"""
        query = """
        SELECT 
            w.id,
            w.week_label,
            w.is_bonus_week,
            COUNT(t.id) as task_count,
            COALESCE(AVG(t.score), 0) as avg_score,
            COUNT(CASE WHEN t.score >= 3 THEN 1 END) as high_score_count,
            COALESCE(SUM(t.bonus_paid), 0) as total_bonus,
            ROUND(
                CAST(COUNT(CASE WHEN t.score >= 3 THEN 1 END) AS FLOAT) / 
                NULLIF(COUNT(t.id), 0) * 100, 2
            ) as high_score_percentage
        FROM weeks w 
        LEFT JOIN tasks t ON w.id = t.week_id 
        GROUP BY w.id, w.week_label, w.is_bonus_week
        ORDER BY w.id DESC
        """
        return self._data_service.execute_query(
            query, (), use_cache=True, cache_ttl=3600
        )
    
    def bulk_update_weeks(self, updates: List[Dict[str, Any]]) -> int:
        """Bulk update weeks within a transaction"""
        updated_count = 0
        
        with self._data_service.transaction():
            for update in updates:
                week_id = update.pop('id')
                if self.update_week(week_id, **update):
                    updated_count += 1
        
        return updated_count
    
    def duplicate_week(self, week_id: int, new_label: str, copy_tasks: bool = False) -> Optional[int]:
        """
        Duplicate a week with optional task copying
        
        Args:
            week_id: ID of week to duplicate
            new_label: Label for the new week
            copy_tasks: If True, also copy all tasks from the original week
        """
        # Get original week
        original_week = self.get_week_by_id(week_id)
        if not original_week:
            return None
        
        # Create new week
        week_data = dict(original_week)
        week_data.pop('id')
        week_data['week_label'] = new_label
        week_data['created_at'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        new_week_id = self.create_week(**week_data)
        
        # Copy tasks if requested
        if copy_tasks and new_week_id:
            from .task_dao import TaskDAO
            task_dao = TaskDAO(self._data_service)
            
            # Get all tasks from original week
            original_tasks = task_dao.get_tasks_by_week(week_id)
            
            # Copy each task to new week
            with self._data_service.transaction():
                for task in original_tasks:
                    task_data = dict(task)
                    task_data.pop('id')
                    task_data['week_id'] = new_week_id
                    task_dao.create_task(**task_data)
        
        return new_week_id 