# CHANGESLOG
## v0.16.8-beta
- **Options/Preferences Window:**
    - Implemented a new Preferences dialog accessible from `File > Preferences`.
    - The dialog features a sidebar for category selection (General, Appearance, Export/Import).
    - Moved the application theme switcher to the "Appearance" section of the Preferences dialog.

## v0.16.7-beta
- **Theming System Refactor:**
    - Centralized all theme (dark/light mode) logic into a new `theme_manager.py` file, moving palette and stylesheet definitions from `main.py`.
    - Removed redundant `analysis_module/styles.py` file.
    - Eliminated inline `setStyleSheet` calls from `analysis_widget.py` and `task_grid.py` to ensure global theme inheritance.
    - Implemented distinct styling for `QTableWidget` instances in `analysis_widget.py` and `task_grid.py` using `objectName` properties (`AnalysisTable` and `TaskTable`).
    - Corrected `QHeaderView::section` selectors in `theme_manager.py` to correctly apply header styles to specific tables using `QTableWidget#ObjectName QHeaderView::section`.

## v0.16.6-beta
- **Week Widget - Date Parsing Improvement:**
    - Enhanced week label parsing in `WeekWidget.parse_start_date` to support `dd-MM-yyyy` format, resolving issues with older week entries not sorting correctly.
    - Extended date parsing improvements to `analysis_module/data_manager.py` to ensure consistent chronological sorting in the analysis widget's week selection dropdown.

## v0.16.5-beta
- **Week Widget Sidebar Enhancements:**
    - Implemented a toggle button in the top bar to show/hide the Weeks sidebar.
    - Added a smooth slide-in/slide-out animation for the Weeks sidebar using `QPropertyAnimation`.
    - Resolved `AttributeError: 'NoneType' object has no attribute 'isVisible'` by ensuring `self.week_dock` is initialized before related components are set up.
    - Fixed `RuntimeWarning: Failed to disconnect` messages by refining animation signal management to prevent attempts at disconnecting un-connected signals.
    - Restored the Weeks sidebar toggle action in the "View" menu.

## v0.16.4-beta
- **Analysis Widget Modularization:**
    - Refactored `analysis_widget.py` into a modular structure.
    - Extracted `DragDropListWidget` into `analysis_module/drag_drop_list_widget.py`.
    - Extracted data management and calculation logic into `analysis_module/data_manager.py`.
    - Extracted chart generation and management logic into `analysis_module/chart_manager.py`.
    - Extracted stylesheet into `analysis_module/styles.py`.
    - Updated `analysis_widget.py` to import and utilize the new modules.
    - **Further Refinement**: Ensured all chart creation and management methods are fully delegated to `ChartManager`, removing duplicate implementations from `analysis_widget.py` and updating method calls to use `self.chart_manager`.
    - **Bug Fix - Daily Project Data**: Fixed daily project data not displaying by correcting the `get_tasks_data_for_daily_project` method to return the complete data structure expected by `calculate_project_statistics` and simplifying the time range query logic.
- **UI/UX Improvement - Project-Based Breakdown Layout**: Arranged 'Time Range Aggregate Project Data' and 'Daily Project Data' tables side-by-side to save vertical space and improve layout in the 'Numerical Statistics' tab.
- **Architectural Change - Convert to QMainWindow**: Transformed `analysis_widget.py` from `QWidget` to `QMainWindow` to establish it as a primary application window, incorporating a central widget to house its existing UI elements.

## v0.16.3-beta
- **Analysis Widget Charting & UI/UX Improvements:**
    - **Data Conversion**: Ensured all raw data (e.g., 'duration', 'time_limit' strings) is correctly converted to numeric values for plotting across all chart data retrieval paths.
    - **Chart Clearing**: Enhanced `clear_chart()` to completely reset the graph, removing all series and axes, and displaying a "Select variables and click 'Generate Chart'" message when variables are modified (added, removed, or dragged).
    - **Line Thickness**: Made line chart lines thinner for improved visual clarity.
    - **Chart Styling**: Applied dark theme colors to chart axis labels, titles, and lines for better readability.
    - **Layout Optimization**: Redesigned the "Graphs" tab layout to be more space-efficient, stacking controls vertically on the left and allowing the chart to expand horizontally. Reduced sizes and spacing for various UI elements in this tab.
    - **Categorical Axis Handling**: Ensured categorical X-axis variables are plotted with proper text labels using `QBarCategoryAxis` instead of numeric indices.

## v0.16.2-beta
- **Analysis Widget Charting Fixes:**
    - **Database Schema Mismatch:** Resolved "no such column: start_date" error by parsing start and end dates from the `week_label` string in the `weeks` table.
    - **Date Selection State Management:** Improved mutual exclusivity between week and date range selections to prevent conflicting queries and ensure correct data loading.

## v0.16.1-beta
- **Analysis Widget UI Fixes:**
    - **Table Editability:** Fixed all tables in analysis widget to be completely non-editable (including empty cells).
    - **Chart Background:** Fixed white chart background issue - charts now use the dark theme background color (#2a2b2a).
    - **Container Styling:** Improved container title spacing and removed bold formatting for better visual hierarchy.
    - **Variable Management:** Added ability to remove variables from X/Y axis lists using Delete or Backspace keys.

## v0.16.0-beta
- **Analysis Widget Overhaul:** Complete redesign of the data analysis interface.
    - **New Tab Structure:** Replaced "Weekly Overview" and "Daily Overview" with "Numerical Statistics" and "Graphs" tabs.
    - **Independent Data Selection:** Added time range selection (calendar) and specific week selection with mutual exclusivity.
    - **Numerical Statistics Tab:** Implemented comprehensive data grids showing aggregate and daily statistics, plus project-based breakdowns.
    - **UI Improvements:** Added scrollable interface, proper spacing, subtle borders, and professional styling.
    - **Week Selection Independence:** Analysis widget no longer automatically updates when selecting weeks in the week widget - users must manually select data ranges.
    - **Week Synchronization:** Week dropdown in analysis widget mirrors weeks created in the week widget.
    - **Hidden by Default:** Analysis widget is now hidden by default and can be accessed via the View menu.
- **Week Widget:** Fixed 'Sort Weeks' button functionality - now properly preserves selection and shows confirmation notification.

## v0.15.1-beta
- **Week Widget:** Added a 'Sort Weeks' button to manually re-sort weeks chronologically.
- **Timer Dialog:** 
    - Timer dialog title now displays week-based task numbering (e.g., 'Timer - Task #1' for the first task in a week).

## v0.15.0-beta
- **Task 1 (Task Grid Enhancements):** Added new `time_begin` and `time_end` columns to track local timestamps for task start and completion times.
- **Task 2 (Timer Functionality):** Implemented comprehensive timer dialog with start, pause, and reset buttons. Timer integrates with Duration cell and automatically updates time tracking columns.
- **Task 4 (Week Widget Sorting):** Fixed week list to display weeks in chronological order instead of lexicographical order.
- **Database Migration:** Added automatic migration to add new time tracking columns to existing databases.

## v0.14.0-beta
- Added week creation and deletion functionality with backup and toaster notifications.

## v0.13.0-beta
- Initial beta version.

