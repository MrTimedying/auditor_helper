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
- **Undockable Widgets**: Flexible UI with ability to rearrange or float widgets

## Requirements

- Python 3.7+
- PySide6

## Installation

1. Clone this repository
2. Install the required dependencies:

```
pip install PySide6
```

3. Run the application:

```
python main.py
```

## Usage

### Managing Weeks

1. Use the Week widget to create new week entries by selecting a date range
2. Select a week to view and manage tasks for that period
3. Use the "Delete Week" button to remove a week and all its tasks

### Managing Tasks

1. Select a week in the Week widget
2. Click "Add New Task" to create a new task
3. Edit task details directly in the grid by double-clicking cells
4. Use the "Edit" button to edit detailed feedback in a separate dialog
5. Use the "Delete" button to remove a task

### Data Analysis

View aggregated statistics for the selected week in the Data Analysis widget, including:
- Total time spent on tasks
- Average time per task
- Percentage of time limit used
- Fail rate (percentage of tasks with scores 1 or 2)

## Database

Tasks and weeks are stored in a SQLite database (`tasks.db`) in the application directory. 