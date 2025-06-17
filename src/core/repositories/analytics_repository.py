from typing import Any, Dict, List, Optional
from datetime import date, datetime, timedelta
from .base_repository import BaseRepository

class AnalyticsRepository(BaseRepository):
    """Repository for analytics and statistical queries with Redis caching"""
    
    def create(self, **kwargs) -> int:
        """Not applicable for analytics repository"""
        raise NotImplementedError("Use specific analytics methods instead")
    
    def get_by_id(self, entity_id: int) -> Optional[Dict[str, Any]]:
        """Not applicable for analytics repository"""
        raise NotImplementedError("Use specific analytics methods instead")
    
    def update(self, entity_id: int, **kwargs) -> bool:
        """Not applicable for analytics repository"""
        raise NotImplementedError("Use specific analytics methods instead")
    
    def delete(self, entity_id: int) -> bool:
        """Not applicable for analytics repository"""
        raise NotImplementedError("Use specific analytics methods instead")
    
    def get_task_statistics(self, week_id: Optional[int] = None, 
                           start_date: Optional[str] = None, 
                           end_date: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive task statistics with caching"""
        
        # Build query based on filters
        base_query = """
            SELECT 
                COUNT(*) as total_tasks,
                COUNT(CASE WHEN score > 0 THEN 1 END) as completed_tasks,
                AVG(CASE WHEN score > 0 THEN score END) as avg_score,
                MAX(score) as max_score,
                MIN(CASE WHEN score > 0 THEN score END) as min_score,
                SUM(CASE WHEN duration_minutes IS NOT NULL THEN duration_minutes ELSE 0 END) as total_duration_minutes
            FROM tasks
        """
        
        conditions = []
        params = []
        
        if week_id is not None:
            conditions.append("week_id = ?")
            params.append(week_id)
        
        if start_date is not None:
            conditions.append("time_begin >= ?")
            params.append(start_date)
        
        if end_date is not None:
            conditions.append("time_end <= ?")
            params.append(end_date)
        
        if conditions:
            base_query += " WHERE " + " AND ".join(conditions)
        
        # Use longer cache TTL for statistics (they don't change frequently)
        results = self._execute_query(base_query, tuple(params), use_cache=True, cache_ttl=1800)  # 30 minutes
        
        if results:
            stats = results[0]
            # Calculate completion rate
            total = stats['total_tasks'] or 0
            completed = stats['completed_tasks'] or 0
            stats['completion_rate'] = (completed / total * 100) if total > 0 else 0
            
            # Convert duration to hours
            total_minutes = stats['total_duration_minutes'] or 0
            stats['total_duration_hours'] = total_minutes / 60.0
            
            return stats
        
        return {
            'total_tasks': 0,
            'completed_tasks': 0,
            'avg_score': 0,
            'max_score': 0,
            'min_score': 0,
            'completion_rate': 0,
            'total_duration_minutes': 0,
            'total_duration_hours': 0
        }
    
    def get_project_statistics(self, start_date: Optional[str] = None, 
                              end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get statistics grouped by project with caching"""
        
        query = """
            SELECT 
                project,
                COUNT(*) as task_count,
                COUNT(CASE WHEN score > 0 THEN 1 END) as completed_count,
                AVG(CASE WHEN score > 0 THEN score END) as avg_score,
                SUM(CASE WHEN duration_minutes IS NOT NULL THEN duration_minutes ELSE 0 END) as total_duration_minutes
            FROM tasks
            WHERE project IS NOT NULL AND project != ''
        """
        
        params = []
        
        if start_date is not None:
            query += " AND time_begin >= ?"
            params.append(start_date)
        
        if end_date is not None:
            query += " AND time_end <= ?"
            params.append(end_date)
        
        query += " GROUP BY project ORDER BY task_count DESC"
        
        # Use longer cache TTL for project statistics
        results = self._execute_query(query, tuple(params), use_cache=True, cache_ttl=1800)  # 30 minutes
        
        # Calculate additional metrics
        for result in results:
            total = result['task_count'] or 0
            completed = result['completed_count'] or 0
            result['completion_rate'] = (completed / total * 100) if total > 0 else 0
            
            total_minutes = result['total_duration_minutes'] or 0
            result['total_duration_hours'] = total_minutes / 60.0
        
        return results
    
    def get_daily_statistics(self, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """Get daily task statistics with caching"""
        
        query = """
            SELECT 
                DATE(time_begin) as date,
                COUNT(*) as task_count,
                COUNT(CASE WHEN score > 0 THEN 1 END) as completed_count,
                AVG(CASE WHEN score > 0 THEN score END) as avg_score,
                SUM(CASE WHEN duration_minutes IS NOT NULL THEN duration_minutes ELSE 0 END) as total_duration_minutes
            FROM tasks
            WHERE time_begin >= ? AND time_end <= ?
            GROUP BY DATE(time_begin)
            ORDER BY date
        """
        
        # Use medium cache TTL for daily statistics
        results = self._execute_query(query, (start_date, end_date), use_cache=True, cache_ttl=900)  # 15 minutes
        
        # Calculate additional metrics
        for result in results:
            total = result['task_count'] or 0
            completed = result['completed_count'] or 0
            result['completion_rate'] = (completed / total * 100) if total > 0 else 0
            
            total_minutes = result['total_duration_minutes'] or 0
            result['total_duration_hours'] = total_minutes / 60.0
        
        return results
    
    def get_productivity_trends(self, days: int = 30) -> Dict[str, Any]:
        """Get productivity trends over specified number of days with caching"""
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Get daily statistics for the period
        daily_stats = self.get_daily_statistics(
            start_date.strftime('%Y-%m-%d'),
            end_date.strftime('%Y-%m-%d')
        )
        
        if not daily_stats:
            return {
                'trend_direction': 'stable',
                'avg_daily_tasks': 0,
                'avg_completion_rate': 0,
                'total_productive_days': 0,
                'daily_data': []
            }
        
        # Calculate trends
        task_counts = [day['task_count'] for day in daily_stats]
        completion_rates = [day['completion_rate'] for day in daily_stats]
        
        avg_daily_tasks = sum(task_counts) / len(task_counts) if task_counts else 0
        avg_completion_rate = sum(completion_rates) / len(completion_rates) if completion_rates else 0
        
        # Simple trend calculation (comparing first half vs second half)
        mid_point = len(task_counts) // 2
        if mid_point > 0:
            first_half_avg = sum(task_counts[:mid_point]) / mid_point
            second_half_avg = sum(task_counts[mid_point:]) / (len(task_counts) - mid_point)
            
            if second_half_avg > first_half_avg * 1.1:
                trend_direction = 'improving'
            elif second_half_avg < first_half_avg * 0.9:
                trend_direction = 'declining'
            else:
                trend_direction = 'stable'
        else:
            trend_direction = 'stable'
        
        # Count productive days (days with at least one completed task)
        productive_days = sum(1 for day in daily_stats if day['completed_count'] > 0)
        
        return {
            'trend_direction': trend_direction,
            'avg_daily_tasks': round(avg_daily_tasks, 2),
            'avg_completion_rate': round(avg_completion_rate, 2),
            'total_productive_days': productive_days,
            'daily_data': daily_stats
        }
    
    def get_time_analysis_data(self, week_id: Optional[int] = None) -> Dict[str, Any]:
        """Get time analysis data for charts with caching"""
        
        base_query = """
            SELECT 
                project,
                task_name,
                score,
                duration_minutes,
                time_begin,
                time_end,
                DATE(time_begin) as date,
                strftime('%H', time_begin) as hour
            FROM tasks
            WHERE duration_minutes IS NOT NULL AND duration_minutes > 0
        """
        
        params = []
        
        if week_id is not None:
            base_query += " AND week_id = ?"
            params.append(week_id)
        
        base_query += " ORDER BY time_begin"
        
        # Use medium cache TTL for time analysis
        results = self._execute_query(base_query, tuple(params), use_cache=True, cache_ttl=900)  # 15 minutes
        
        # Process data for different chart types
        hourly_distribution = {}
        project_time_distribution = {}
        daily_time_totals = {}
        
        for task in results:
            hour = int(task['hour']) if task['hour'] else 0
            project = task['project'] or 'No Project'
            date = task['date']
            duration = task['duration_minutes'] or 0
            
            # Hourly distribution
            hourly_distribution[hour] = hourly_distribution.get(hour, 0) + duration
            
            # Project time distribution
            project_time_distribution[project] = project_time_distribution.get(project, 0) + duration
            
            # Daily totals
            daily_time_totals[date] = daily_time_totals.get(date, 0) + duration
        
        return {
            'hourly_distribution': hourly_distribution,
            'project_time_distribution': project_time_distribution,
            'daily_time_totals': daily_time_totals,
            'raw_data': results
        }
    
    def get_score_distribution(self, week_id: Optional[int] = None) -> Dict[str, Any]:
        """Get score distribution data with caching"""
        
        query = """
            SELECT 
                score,
                COUNT(*) as count
            FROM tasks
            WHERE score > 0
        """
        
        params = []
        
        if week_id is not None:
            query += " AND week_id = ?"
            params.append(week_id)
        
        query += " GROUP BY score ORDER BY score"
        
        # Use medium cache TTL for score distribution
        results = self._execute_query(query, tuple(params), use_cache=True, cache_ttl=900)  # 15 minutes
        
        # Convert to dictionary format
        distribution = {}
        total_scored_tasks = 0
        
        for result in results:
            score = result['score']
            count = result['count']
            distribution[score] = count
            total_scored_tasks += count
        
        # Calculate percentages
        percentages = {}
        for score, count in distribution.items():
            percentages[score] = (count / total_scored_tasks * 100) if total_scored_tasks > 0 else 0
        
        return {
            'distribution': distribution,
            'percentages': percentages,
            'total_scored_tasks': total_scored_tasks
        }
    
    def get_weekly_comparison(self, week_ids: List[int]) -> List[Dict[str, Any]]:
        """Compare statistics across multiple weeks with caching"""
        
        if not week_ids:
            return []
        
        placeholders = ','.join(['?'] * len(week_ids))
        query = f"""
            SELECT 
                w.id as week_id,
                w.start_date,
                w.end_date,
                w.is_bonus,
                COUNT(t.id) as total_tasks,
                COUNT(CASE WHEN t.score > 0 THEN 1 END) as completed_tasks,
                AVG(CASE WHEN t.score > 0 THEN t.score END) as avg_score,
                SUM(CASE WHEN t.duration_minutes IS NOT NULL THEN t.duration_minutes ELSE 0 END) as total_duration_minutes
            FROM weeks w
            LEFT JOIN tasks t ON w.id = t.week_id
            WHERE w.id IN ({placeholders})
            GROUP BY w.id, w.start_date, w.end_date, w.is_bonus
            ORDER BY w.start_date
        """
        
        # Use medium cache TTL for weekly comparisons
        results = self._execute_query(query, tuple(week_ids), use_cache=True, cache_ttl=900)  # 15 minutes
        
        # Calculate additional metrics
        for result in results:
            total = result['total_tasks'] or 0
            completed = result['completed_tasks'] or 0
            result['completion_rate'] = (completed / total * 100) if total > 0 else 0
            
            total_minutes = result['total_duration_minutes'] or 0
            result['total_duration_hours'] = total_minutes / 60.0
        
        return results 