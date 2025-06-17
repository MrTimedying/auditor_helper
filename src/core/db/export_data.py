"""
Enhanced export functionality using the Data Service Layer.
Provides improved performance through caching and better error handling.
"""

import os
# Lazy import for pandas - deferred until first use
from core.optimization.lazy_imports import get_lazy_manager
from datetime import datetime
from typing import Optional, List, Tuple
import logging

# Import the new Data Service Layer
from ..services import DataService, TaskDAO, WeekDAO

# Configure logging
logger = logging.getLogger(__name__)

# Legacy support - keep DB_FILE for backward compatibility
DB_FILE = "tasks.db"

class ExportManager:
    """Export manager with lazy-loaded pandas for better startup performance"""
    
    def __init__(self):
        self._lazy_manager = get_lazy_manager()
        self._setup_lazy_imports()
    
    def _setup_lazy_imports(self):
        """Setup lazy imports for heavy scientific libraries"""
        # Register pandas for lazy loading
        self._lazy_manager.register_module('pandas', 'pandas')
    
    @property
    def pd(self):
        """Lazy-loaded pandas module"""
        return self._lazy_manager.get_module('pandas')

# Global instance - created lazily when first accessed
_export_manager = None

def _get_export_manager():
    """Get the export manager instance, creating it lazily if needed"""
    global _export_manager
    if _export_manager is None:
        _export_manager = ExportManager()
    return _export_manager

def get_week_label(week_id: int) -> Optional[str]:
    """
    Get the week label for a given week ID.
    Now uses WeekDAO with caching for better performance.
    """
    try:
        week_dao = WeekDAO()
        week = week_dao.get_week_by_id(week_id)
        return week['week_label'] if week else None
    except Exception as e:
        logger.error(f"Error getting week label for week_id {week_id}: {e}")
        return None

def get_tasks_for_week(week_id: int):
    """
    Get all tasks for a given week.
    Now uses TaskDAO with intelligent caching for better performance.
    """
    try:
        task_dao = TaskDAO()
        
        # Use the cached method from TaskDAO
        tasks = task_dao.get_tasks_by_week(week_id)
        
        if not tasks:
            # Return empty DataFrame with correct columns
            columns = [
                "Attempt ID", "Duration", "Project ID", "Project Name", 
                "Operation ID", "Time Limit", "Date Audited", "Score",
                "Feedback", "Locale"
            ]
            return _get_export_manager().pd.DataFrame(columns=columns)
        
        # Convert to the expected format for export
        export_data = []
        for task in tasks:
            export_data.append([
                task.get('attempt_id', ''),
                task.get('duration', ''),
                task.get('project_id', ''),
                task.get('project_name', ''),
                task.get('operation_id', ''),
                task.get('time_limit', ''),
                task.get('date_audited', ''),
                task.get('score', ''),
                task.get('feedback', ''),
                task.get('locale', '')
            ])
        
        # Convert to DataFrame
        columns = [
            "Attempt ID", "Duration", "Project ID", "Project Name", 
            "Operation ID", "Time Limit", "Date Audited", "Score",
            "Feedback", "Locale"
        ]
        df = _get_export_manager().pd.DataFrame(export_data, columns=columns)
        
        logger.info(f"Successfully retrieved {len(df)} tasks for week {week_id}")
        return df
        
    except Exception as e:
        logger.error(f"Error getting tasks for week_id {week_id}: {e}")
        # Return empty DataFrame on error
        columns = [
            "Attempt ID", "Duration", "Project ID", "Project Name", 
            "Operation ID", "Time Limit", "Date Audited", "Score",
            "Feedback", "Locale"
        ]
        return _get_export_manager().pd.DataFrame(columns=columns)

def get_all_weeks() -> List[Tuple[int, str]]:
    """
    Get all weeks with their IDs.
    Now uses WeekDAO with caching for better performance.
    """
    try:
        week_dao = WeekDAO()
        weeks = week_dao.get_all_weeks()
        
        # Convert to the expected format (list of tuples)
        result = [(week['id'], week['week_label']) for week in weeks]
        
        logger.info(f"Successfully retrieved {len(result)} weeks")
        return result
        
    except Exception as e:
        logger.error(f"Error getting all weeks: {e}")
        return []

def get_tasks_with_analytics(week_id: Optional[int] = None):
    """
    Get tasks with additional analytics data.
    New function leveraging the enhanced TaskDAO capabilities.
    """
    try:
        task_dao = TaskDAO()
        
        # Use the analytics method from TaskDAO
        tasks = task_dao.get_tasks_with_analytics(week_id)
        
        if not tasks:
            columns = [
                "Task ID", "Week Label", "Attempt ID", "Duration", "Project Name", 
                "Score", "Is High Score", "Duration Seconds", "Date Audited", 
                "Feedback", "Bonus Week"
            ]
            return _get_export_manager().pd.DataFrame(columns=columns)
        
        # Convert to DataFrame with analytics
        export_data = []
        for task in tasks:
            export_data.append([
                task.get('id', ''),
                task.get('week_label', ''),
                task.get('attempt_id', ''),
                task.get('duration', ''),
                task.get('project_name', ''),
                task.get('score', ''),
                'Yes' if task.get('is_high_score', 0) else 'No',
                task.get('duration_seconds', 0),
                task.get('date_audited', ''),
                task.get('feedback', ''),
                'Yes' if task.get('is_bonus_week', 0) else 'No'
            ])
        
        columns = [
            "Task ID", "Week Label", "Attempt ID", "Duration", "Project Name", 
            "Score", "Is High Score", "Duration Seconds", "Date Audited", 
            "Feedback", "Bonus Week"
        ]
        df = _get_export_manager().pd.DataFrame(export_data, columns=columns)
        
        logger.info(f"Successfully retrieved {len(df)} tasks with analytics")
        return df
        
    except Exception as e:
        logger.error(f"Error getting tasks with analytics: {e}")
        return _get_export_manager().pd.DataFrame()

def export_week_to_csv(week_id: int, filename: Optional[str] = None, include_analytics: bool = False) -> str:
    """
    Export all tasks for a given week to CSV.
    Enhanced with analytics option and better error handling.
    """
    try:
        if not filename:
            week_label = get_week_label(week_id)
            if week_label:
                # Replace any characters that aren't good for filenames
                safe_label = week_label.replace("/", "-").replace("\\", "-").replace(":", "-")
                analytics_suffix = "_with_analytics" if include_analytics else ""
                filename = f"auditor_tasks_{safe_label}{analytics_suffix}.csv"
            else:
                analytics_suffix = "_with_analytics" if include_analytics else ""
                filename = f"auditor_tasks_week_{week_id}{analytics_suffix}.csv"
        
        # Get tasks (with or without analytics)
        if include_analytics:
            df = get_tasks_with_analytics(week_id)
        else:
            df = get_tasks_for_week(week_id)
        
        # Export to CSV
        df.to_csv(filename, index=False)
        
        logger.info(f"Successfully exported {len(df)} tasks to {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"Error exporting week {week_id} to CSV: {e}")
        raise

def export_all_weeks_to_excel(filename: Optional[str] = None, include_analytics: bool = False) -> str:
    """
    Export all weeks to a multi-sheet Excel file.
    Enhanced with analytics option and better error handling.
    """
    try:
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            analytics_suffix = "_with_analytics" if include_analytics else ""
            filename = f"auditor_all_tasks_{timestamp}{analytics_suffix}.xlsx"
        
        # Create Excel writer
        writer = _get_export_manager().pd.ExcelWriter(filename, engine='openpyxl')
        
        # Get all weeks using the cached method
        weeks = get_all_weeks()
        
        if not weeks:
            logger.warning("No weeks found for export")
            # Create empty workbook
            _get_export_manager().pd.DataFrame().to_excel(writer, sheet_name='No Data', index=False)
        else:
            # Export each week to a sheet
            total_tasks = 0
            for week_id, week_label in weeks:
                try:
                    # Get tasks (with or without analytics)
                    if include_analytics:
                        df = get_tasks_with_analytics(week_id)
                    else:
                        df = get_tasks_for_week(week_id)
                    
                    # Use week label as sheet name but ensure it's valid (Excel has 31 char limit)
                    safe_label = week_label.replace("/", "-").replace("\\", "-").replace(":", "-")
                    safe_label = safe_label[:30]  # Truncate to avoid Excel sheet name limit
                    
                    # Ensure unique sheet names
                    sheet_name = safe_label
                    counter = 1
                    while sheet_name in writer.sheets:
                        sheet_name = f"{safe_label[:27]}_{counter}"
                        counter += 1
                    
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    total_tasks += len(df)
                    
                    logger.debug(f"Exported {len(df)} tasks for week '{week_label}' to sheet '{sheet_name}'")
                    
                except Exception as e:
                    logger.error(f"Error exporting week {week_id} ({week_label}): {e}")
                    # Continue with other weeks
                    continue
        
        # Save the Excel file
        writer.close()
        
        logger.info(f"Successfully exported {total_tasks} total tasks from {len(weeks)} weeks to {filename}")
        return filename
        
    except Exception as e:
        logger.error(f"Error exporting all weeks to Excel: {e}")
        raise

def get_export_statistics() -> dict:
    """
    Get statistics about exportable data.
    New function leveraging Data Service performance monitoring.
    """
    try:
        data_service = DataService.get_instance()
        task_dao = TaskDAO()
        week_dao = WeekDAO()
        
        # Get performance stats
        perf_stats = data_service.get_performance_stats()
        
        # Get data statistics
        weeks = week_dao.get_all_weeks()
        total_tasks = 0
        
        for week in weeks:
            week_stats = task_dao.get_task_statistics(week['id'])
            total_tasks += week_stats.get('total_tasks', 0)
        
        return {
            'total_weeks': len(weeks),
            'total_tasks': total_tasks,
            'database_size_bytes': perf_stats.get('database_size', 0),
            'cache_available': perf_stats['cache_stats'].get('redis_available', False),
            'cache_hit_rate': perf_stats['cache_stats'].get('hit_rate', 0),
            'last_updated': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting export statistics: {e}")
        return {
            'error': str(e),
            'last_updated': datetime.now().isoformat()
        }

# Legacy function aliases for backward compatibility
def export_week_csv(week_id: int, filename: Optional[str] = None) -> str:
    """Legacy alias for export_week_to_csv"""
    return export_week_to_csv(week_id, filename)

def export_all_excel(filename: Optional[str] = None) -> str:
    """Legacy alias for export_all_weeks_to_excel"""
    return export_all_weeks_to_excel(filename) 
