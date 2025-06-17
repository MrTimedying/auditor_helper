from typing import Any, Dict, List, Optional
from datetime import datetime
from .base_repository import BaseRepository

class WeekRepository(BaseRepository):
    """Repository for week data access with Redis caching"""
    
    def create(self, start_date: str, end_date: str, is_bonus: bool = False, **kwargs) -> int:
        """Create a new week"""
        command = """
            INSERT INTO weeks (start_date, end_date, is_bonus, office_hour_count, created_at)
            VALUES (?, ?, ?, ?, ?)
        """
        
        office_hour_count = kwargs.get('office_hour_count', 0)
        created_at = datetime.now().isoformat()
        
        params = (start_date, end_date, is_bonus, office_hour_count, created_at)
        
        week_id = self._execute_command(command, params)
        
        # Invalidate cache for week queries
        self.clear_cache()
        
        return week_id
    
    def get_by_id(self, week_id: int) -> Optional[Dict[str, Any]]:
        """Get week by ID with caching"""
        query = "SELECT * FROM weeks WHERE id = ?"
        
        # Use longer cache TTL for individual weeks (they don't change frequently)
        results = self._execute_query(query, (week_id,), use_cache=True, cache_ttl=1800)  # 30 minutes
        
        return results[0] if results else None
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all weeks with caching"""
        query = "SELECT * FROM weeks ORDER BY start_date DESC"
        
        # Use longer cache TTL for all weeks list (changes infrequently)
        return self._execute_query(query, (), use_cache=True, cache_ttl=1200)  # 20 minutes
    
    def get_by_date_range(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get weeks within a date range with caching"""
        query = """
            SELECT * FROM weeks 
            WHERE start_date >= ? AND end_date <= ?
            ORDER BY start_date
        """
        
        # Use medium cache TTL for date range queries
        return self._execute_query(query, (start_date, end_date), use_cache=True, cache_ttl=900)  # 15 minutes
    
    def update(self, week_id: int, **kwargs) -> bool:
        """Update week fields"""
        if not kwargs:
            return False
        
        # Build dynamic update query
        set_clauses = []
        params = []
        
        for field, value in kwargs.items():
            if field in ['start_date', 'end_date', 'is_bonus', 'office_hour_count']:
                set_clauses.append(f"{field} = ?")
                params.append(value)
        
        if not set_clauses:
            return False
        
        # Add updated timestamp
        set_clauses.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        
        command = f"UPDATE weeks SET {', '.join(set_clauses)} WHERE id = ?"
        params.append(week_id)
        
        affected_rows = self._execute_command(command, tuple(params))
        
        # Invalidate cache after update
        self.clear_cache()
        
        return affected_rows > 0
    
    def delete(self, week_id: int) -> bool:
        """Delete a week"""
        command = "DELETE FROM weeks WHERE id = ?"
        affected_rows = self._execute_command(command, (week_id,))
        
        # Invalidate cache after deletion
        self.clear_cache()
        
        return affected_rows > 0
    
    def update_bonus_status(self, week_id: int, is_bonus: bool) -> bool:
        """Update bonus status for a week"""
        command = "UPDATE weeks SET is_bonus = ?, updated_at = ? WHERE id = ?"
        
        affected_rows = self._execute_command(command, (is_bonus, datetime.now().isoformat(), week_id))
        
        # Invalidate cache after bonus status update
        self.clear_cache()
        
        return affected_rows > 0
    
    def get_office_hour_count(self, week_id: int) -> int:
        """Get office hour count for a week with caching"""
        query = "SELECT office_hour_count FROM weeks WHERE id = ?"
        
        # Use medium cache TTL for office hour counts
        results = self._execute_query(query, (week_id,), use_cache=True, cache_ttl=600)  # 10 minutes
        
        return results[0]['office_hour_count'] if results else 0
    
    def update_office_hour_count(self, week_id: int, count: int) -> bool:
        """Update office hour count for a week"""
        command = "UPDATE weeks SET office_hour_count = ?, updated_at = ? WHERE id = ?"
        
        affected_rows = self._execute_command(command, (count, datetime.now().isoformat(), week_id))
        
        # Invalidate cache after office hour update
        self.clear_cache()
        
        return affected_rows > 0
    
    def add_office_hour_session(self, week_id: int) -> bool:
        """Add one office hour session to a week"""
        # Get current count
        current_count = self.get_office_hour_count(week_id)
        
        # Update with incremented count
        return self.update_office_hour_count(week_id, current_count + 1)
    
    def remove_office_hour_session(self, week_id: int) -> bool:
        """Remove one office hour session from a week"""
        # Get current count
        current_count = self.get_office_hour_count(week_id)
        
        # Don't go below 0
        new_count = max(0, current_count - 1)
        
        return self.update_office_hour_count(week_id, new_count)
    
    def get_bonus_weeks(self) -> List[Dict[str, Any]]:
        """Get all bonus weeks with caching"""
        query = "SELECT * FROM weeks WHERE is_bonus = 1 ORDER BY start_date DESC"
        
        # Use longer cache TTL for bonus weeks (changes infrequently)
        return self._execute_query(query, (), use_cache=True, cache_ttl=1200)  # 20 minutes
    
    def get_recent_weeks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get most recent weeks with caching"""
        query = "SELECT * FROM weeks ORDER BY start_date DESC LIMIT ?"
        
        # Use medium cache TTL for recent weeks
        return self._execute_query(query, (limit,), use_cache=True, cache_ttl=600)  # 10 minutes
    
    def get_week_by_date(self, date: str) -> Optional[Dict[str, Any]]:
        """Get week that contains a specific date with caching"""
        query = """
            SELECT * FROM weeks 
            WHERE ? BETWEEN start_date AND end_date
            LIMIT 1
        """
        
        # Use medium cache TTL for date lookups
        results = self._execute_query(query, (date,), use_cache=True, cache_ttl=900)  # 15 minutes
        
        return results[0] if results else None 