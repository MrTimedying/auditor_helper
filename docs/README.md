# Auditor Helper

A desktop application to help auditors track and analyze their auditing tasks across different weeks.

## Features

- **Weekly Task Management**: Organize tasks by week with date range selection
- **Detailed Task Tracking**: Track multiple fields for each task including:
  - Attempt ID
  - Duration (hh:mm:ss)
  - Project ID and Name
  - Operation ID
  - Time Limit
  - Date Audited
  - Score
  - Feedback (with markdown support)
  - Locale
- **Data Analysis**: View aggregated statistics for selected week
  - Total time worked
  - Average time per task
  - Percentage of time limit used
  - Fail rate (% of tasks with scores 1-2)
- **Export Capabilities**: Export your data in different formats
  - Export a single week to CSV
  - Export all weeks to a multi-sheet Excel file
- **Undockable Widgets**: Flexible UI with ability to rearrange or float widgets
- **Automatic Backups**: Database is automatically backed up when adding or deleting weeks

## For Users (Pre-built Application)

### Installation

1. Download the latest release from the Releases page
2. Extract the ZIP file to any location on your computer
3. Run the "Auditor Helper.exe" file inside the extracted folder

### Usage

#### Managing Weeks

1. Use the Week widget to create new week entries by selecting a date range
2. Select a week to view and manage tasks for that period
3. Use the "Delete Week" button to remove a week and all its tasks

#### Managing Tasks

1. Select a week in the Week widget
2. Click "Add New Task" to create a new task
3. Edit task details directly in the grid by double-clicking cells
4. Double-click on feedback cells to edit detailed feedback
5. Use the "Delete" button to remove a task

#### Data Analysis

View aggregated statistics for the selected week in the Data Analysis widget, including:
- Total time spent on tasks
- Average time per task
- Percentage of time limit used
- Fail rate (percentage of tasks with scores 1 or 2)

#### Exporting Data

Use the File menu to:
1. Export the current week's tasks to a CSV file (File > Export > Export Week)
2. Export all weeks to an Excel file with multiple sheets (File > Export > Export All)

#### Database Backups

The application automatically creates backups of your database in a "backups" folder whenever you add or delete a week. These backups are timestamped and can be used to recover data if needed.

## For Developers

### Requirements

- Python 3.7+
- PySide6
- pandas
- openpyxl
- Pillow (for building only)
- PyInstaller (for building only)

### Development Setup

1. Clone this repository
2. Install the required dependencies:

```
pip install PySide6 pandas openpyxl
```

3. Run the application in development mode:

```
python main.py
```

### Building the Application

To build a standalone executable:

1. Install the required build dependencies:

```
pip install pyinstaller pillow
```

2. Run the build script:

```
python build_app.py
```

3. The packaged application will be available in the `dist/Auditor Helper` directory

### Project Structure

- `main.py` - Main application entry point
- `week_widget.py` - Week management widget
- `task_grid.py` - Task grid implementation
- `analysis_widget.py` - Data analysis widget
- `export_data.py` - Data export functionality
- `db_schema.py` - Database schema definition
- `build_app.py` - Application packaging script 