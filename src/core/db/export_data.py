import os
import sqlite3
import pandas as pd
from datetime import datetime

DB_FILE = "tasks.db"

def get_week_label(week_id):
    """Get the week label for a given week ID"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT week_label FROM weeks WHERE id=?", (week_id,))
    result = c.fetchone()
    conn.close()
    if result:
        return result[0]
    return None

def get_tasks_for_week(week_id):
    """Get all tasks for a given week"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        SELECT 
            attempt_id, duration, project_id, project_name, 
            operation_id, time_limit, date_audited, score, 
            feedback, locale
        FROM tasks 
        WHERE week_id=?
        ORDER BY id
    """, (week_id,))
    tasks = c.fetchall()
    conn.close()
    
    # Convert to DataFrame
    columns = [
        "Attempt ID", "Duration", "Project ID", "Project Name", 
        "Operation ID", "Time Limit", "Date Audited", "Score",
        "Feedback", "Locale"
    ]
    df = pd.DataFrame(tasks, columns=columns)
    return df

def get_all_weeks():
    """Get all weeks with their IDs"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, week_label FROM weeks ORDER BY week_label")
    weeks = c.fetchall()
    conn.close()
    return weeks

def export_week_to_csv(week_id, filename=None):
    """Export all tasks for a given week to CSV"""
    if not filename:
        week_label = get_week_label(week_id)
        if week_label:
            # Replace any characters that aren't good for filenames
            safe_label = week_label.replace("/", "-").replace("\\", "-").replace(":", "-")
            filename = f"auditor_tasks_{safe_label}.csv"
        else:
            filename = f"auditor_tasks_week_{week_id}.csv"
    
    # Get tasks and export
    df = get_tasks_for_week(week_id)
    df.to_csv(filename, index=False)
    return filename

def export_all_weeks_to_excel(filename=None):
    """Export all weeks to a multi-sheet Excel file"""
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"auditor_all_tasks_{timestamp}.xlsx"
    
    # Create Excel writer
    writer = pd.ExcelWriter(filename, engine='openpyxl')
    
    # Get all weeks
    weeks = get_all_weeks()
    
    # Export each week to a sheet
    for week_id, week_label in weeks:
        df = get_tasks_for_week(week_id)
        
        # Use week label as sheet name but ensure it's valid (Excel has 31 char limit)
        safe_label = week_label.replace("/", "-").replace("\\", "-").replace(":", "-")
        safe_label = safe_label[:30]  # Truncate to avoid Excel sheet name limit
        
        df.to_excel(writer, sheet_name=safe_label, index=False)
    
    # Save the Excel file
    writer.close()
    return filename 