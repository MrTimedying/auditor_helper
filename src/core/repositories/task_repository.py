from typing import Any, Dict, List, Optional
from datetime import datetime
from .base_repository import BaseRepository

class TaskRepository(BaseRepository):
    """Repository for task data access with Redis caching"""
    
    def create(self, week_id: int, task_name: str = "New Task", score: int = 0, 
               feedback: str = "", project: str = "", **kwargs) -> int:
        """Create a new task with default values"""
        command = """
            INSERT INTO tasks (week_id, task_name, score, feedback, project, time_begin, time_end)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        
        now = datetime.now().isoformat()
        params = (week_id, task_name, score, feedback, project, now, now)
        
        task_id = self._execute_command(command, params)
        
        # Invalidate cache for task queries
        self.clear_cache()
        
        return task_id
    
    def get_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """Get task by ID with caching"""
        query = "SELECT * FROM tasks WHERE id = ?"
        
        # Use longer cache TTL for individual tasks (they don't change frequently)
        results = self._execute_query(query, (task_id,), use_cache=True, cache_ttl=1800)  # 30 minutes
        
        return results[0] if results else None
    
    def get_by_week(self, week_id: int) -> List[Dict[str, Any]]:
        """Get all tasks for a specific week with caching"""
        query = "SELECT * FROM tasks WHERE week_id = ? ORDER BY id"
        
        # Use medium cache TTL for week task lists
        return self._execute_query(query, (week_id,), use_cache=True, cache_ttl=900)  # 15 minutes
    
    def get_tasks_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get tasks within a date range with caching"""
        query = """
            SELECT * FROM tasks 
            WHERE time_begin >= ? AND time_end <= ?
            ORDER BY time_begin
        """
        
        # Use medium cache TTL for date range queries
        return self._execute_query(query, (start_date, end_date), use_cache=True, cache_ttl=600)  # 10 minutes
    
    def get_tasks_by_project(self, project: str) -> List[Dict[str, Any]]:
        """Get all tasks for a specific project with caching"""
        query = "SELECT * FROM tasks WHERE project = ? ORDER BY time_begin DESC"
        
        # Use longer cache TTL for project queries (projects don't change often)
        return self._execute_query(query, (project,), use_cache=True, cache_ttl=1200)  # 20 minutes
    
    def update(self, task_id: int, **kwargs) -> bool:
        """Update task fields"""
        if not kwargs:
            return False
        
        # Build dynamic update query
        set_clauses = []
        params = []
        
        for field, value in kwargs.items():
            if field in ['task_name', 'score', 'feedback', 'project', 'time_begin', 'time_end']:
                set_clauses.append(f"{field} = ?")
                params.append(value)
        
        if not set_clauses:
            return False
        
        command = f"UPDATE tasks SET {', '.join(set_clauses)} WHERE id = ?"
        params.append(task_id)
        
        affected_rows = self._execute_command(command, tuple(params))
        
        # Invalidate cache after update
        self.clear_cache()
        
        return affected_rows > 0
    
    def delete(self, task_id: int) -> bool:
        """Delete a task"""
        command = "DELETE FROM tasks WHERE id = ?"
        affected_rows = self._execute_command(command, (task_id,))
        
        # Invalidate cache after deletion
        self.clear_cache()
        
        return affected_rows > 0
    
    def delete_multiple(self, task_ids: List[int]) -> int:
        """Delete multiple tasks in a transaction"""
        if not task_ids:
            return 0
        
        with self.transaction():
            placeholders = ','.join(['?'] * len(task_ids))
            command = f"DELETE FROM tasks WHERE id IN ({placeholders})"
            affected_rows = self._execute_command(command, tuple(task_ids))
            
            # Invalidate cache after bulk deletion
            self.clear_cache()
            
            return affected_rows
    
    def update_duration_and_time(self, task_id: int, duration_minutes: float, 
                                time_begin: str, time_end: str) -> bool:
        """Update task duration and time data from timer"""
        command = """
            UPDATE tasks 
            SET duration_minutes = ?, time_begin = ?, time_end = ?
            WHERE id = ?
        """
        
        affected_rows = self._execute_command(command, (duration_minutes, time_begin, time_end, task_id))
        
        # Invalidate cache after timer update
        self.clear_cache()
        
        return affected_rows > 0
    
    def get_task_count_by_week(self, week_id: int) -> int:
        """Get count of tasks in a week with caching"""
        query = "SELECT COUNT(*) as count FROM tasks WHERE week_id = ?"
        
        # Use medium cache TTL for count queries
        results = self._execute_query(query, (week_id,), use_cache=True, cache_ttl=600)  # 10 minutes
        
        return results[0]['count'] if results else 0
    
    def get_completed_tasks_count(self, week_id: int) -> int:
        """Get count of completed tasks (score > 0) in a week with caching"""
        query = "SELECT COUNT(*) as count FROM tasks WHERE week_id = ? AND score > 0"
        
        # Use medium cache TTL for completion stats
        results = self._execute_query(query, (week_id,), use_cache=True, cache_ttl=600)  # 10 minutes
        
        return results[0]['count'] if results else 0
    
    def search_tasks(self, search_term: str, week_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """Search tasks by name, feedback, or project with caching"""
        base_query = """
            SELECT * FROM tasks 
            WHERE (task_name LIKE ? OR feedback LIKE ? OR project LIKE ?)
        """
        
        params = [f"%{search_term}%", f"%{search_term}%", f"%{search_term}%"]
        
        if week_id is not None:
            base_query += " AND week_id = ?"
            params.append(week_id)
        
        base_query += " ORDER BY id DESC"
        
        # Use shorter cache TTL for search results (more dynamic)
        return self._execute_query(base_query, tuple(params), use_cache=True, cache_ttl=300)  # 5 minutes 