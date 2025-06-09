# CHANGESLOG

## v0.16.14-beta
- **Analysis Widget - Intelligent Variable Suggestion System:**
    - **Smart Variable Recommendations**: Implemented comprehensive suggestion engine that provides context-aware recommendations for variable selection based on data characteristics, semantic meaning, and chart type compatibility.
    - **Dynamic Suggestion Indicators**: Added visual indicators (⭐ = Highly Recommended, ✨ = Recommended, ⚠️ = Warning) that appear next to variables in the Available Variables list with explanatory tooltips.
    - **Contextual Awareness**: Suggestions update in real-time based on current X/Y variable selections and chosen chart type, providing progressively smarter recommendations as users build their charts.
    - **Data-Driven Analysis**: Advanced variable analyzer examines data patterns including cardinality, distribution, null rates, outliers, and temporal characteristics to make informed suggestions.
    - **Semantic Intelligence**: Recognition of variable meaning based on names (performance metrics, financial data, time series) with appropriate color coding and role suggestions.
    - **Chart Type Compatibility**: Intelligent chart type suggestions with suitability scores and detailed reasoning based on selected variables and their characteristics.
    - **Progressive User Guidance**: Real-time chart type recommendations panel showing top 3 suitable chart types with confidence scores and explanatory reasons.
    - **Educational Tooltips**: Detailed hover information explaining why specific variables are recommended, with actionable suggestions for improvement.
    - **Performance Considerations**: Efficient suggestion updates triggered only when variable selections change, maintaining smooth user experience.

## v0.16.13-beta
- **Analysis Widget - Enhanced Chart Styling System & Code Architecture:**
    - **Professional Chart Theming**: Implemented comprehensive theming system with 4 built-in themes:
        - **Professional (Default)**: Clean business theme with Nord color palette and balanced typography
        - **Dark Mode**: Modern dark theme optimized for low-light environments with enhanced contrast
        - **Minimal Clean**: Apple-inspired minimal design with subtle styling and reduced visual clutter
        - **High Contrast**: Accessibility-focused theme with bold colors and increased text sizes for visually impaired users
    - **Responsive Chart Design**: Adaptive layouts that automatically scale typography, margins, and sizing based on container dimensions with mobile, tablet, desktop, and large screen breakpoints.
    - **Advanced Accessibility Features**: High contrast modes, colorblind-safe color palettes, and pattern fill options for enhanced accessibility compliance.
    - **Live Theme Switching**: Instant chart regeneration when themes are changed through intuitive UI dropdown in chart controls.
    - **Modular Code Architecture**: Major refactoring into focused, maintainable modules:
        - `chart_validation.py`: Isolated validation logic (ValidationIssue, ChartValidationEngine)
        - `chart_styling.py`: Complete styling system (ChartStyleManager, ResponsiveChartManager, ChartTheme)
        - `chart_manager.py`: Streamlined chart coordination integrating styling and validation systems
    - **Enhanced Color Management**: Seamless integration of semantic color system with theme-based palettes ensuring consistent variable colors across all themes.
    - **Improved Code Maintainability**: Clear separation of concerns, comprehensive type hints, and detailed documentation throughout the styling system for easier future development.

## v0.16.12-beta
- **Analysis Widget - Comprehensive Error Handling & Validation System:**
    - **Chart Validation Engine**: Implemented comprehensive validation system that checks data quality, variable combinations, chart type compatibility, and performance considerations before chart generation.
    - **Progressive Error Disclosure**: Enhanced user experience with informative error messages, warnings, and actionable suggestions instead of generic "failed" messages.
    - **Smart Validation Rules**: Added chart-specific validation (e.g., Pie charts require categorical X-axis and single Y variable, Scatter plots work better with quantitative variables).
    - **Data Quality Checks**: Automatic detection of empty datasets, null variables, extreme outliers, and insufficient data with specific guidance for each issue.
    - **Pre-generation Guidance**: Shows warnings for potentially problematic combinations (too many Y variables, inappropriate chart types) with option to proceed.
    - **Enhanced User Feedback**: Replaced basic error dialogs with detailed messages including specific suggestions, alternative approaches, and educational content.
    - **Loading States**: Added visual feedback during chart generation with progress indicators and button state management.
    - **Graceful Error Recovery**: Comprehensive exception handling ensures the application remains stable even when unexpected errors occur.

## v0.16.11-beta
- **Analysis Widget - Semantic Color Management System:**
    - **Intelligent Color Assignment**: Implemented semantic color management system that assigns meaningful, consistent colors to chart variables based on their semantic meaning.
    - **Semantic Mappings**: Variables now get appropriate colors - Red for failure metrics (fail_rate, error_rate), Green for financial metrics (total_earnings, revenue), Blue for time metrics (duration, total_time), Orange for performance scores, Purple for counts, and Dark Orange for percentages.
    - **Consistency Across Charts**: Each variable maintains the same color across all chart types and sessions, improving user recognition and mental model building.
    - **Accessibility-Friendly Fallback**: Variables without semantic meaning use a curated, color-blind accessible palette ensuring good visual distinction.
    - **Enhanced Visual Quality**: Improved line chart visibility with slightly thicker lines (2px) and better color contrast.

## v0.16.10-beta
- **Analysis Widget - Charting Fixes (Week & Composite Variables):**
    - **Week Selection Charting Fix**: Resolved issue where charts would not display data when selecting a specific week. The date parsing logic in `analysis_module/data_manager.py` was updated to correctly handle week labels formatted with hyphens (`dd-MM-yyyy`) in addition to slashes (`dd/MM/yyyy`).
    - **Composite Metric X-Axis Fix**: Fixed a critical bug where selecting a composite metric (e.g., "Total Time", "Fail Rate") as the X-axis variable would cause SQL errors and prevent charts from rendering. The `get_aggregated_chart_data` method in `analysis_module/data_manager.py` now correctly identifies and handles these composite metrics by grouping by `date_audited` and calculating the X-axis values for display.
    - **Improved Error Logging**: Added `analysis_module/common_errors_log.md` to document common issues, their root causes, and solutions for easier debugging and maintenance.

## v0.16.9-beta
- **Timer Dialog - Real-time Time Limit Alert:**
    - Implemented a real-time alert system in the `TimerDialog` that triggers when the timer reaches 90% of the `Time Limit` set in the `TaskGrid`.
    - **Real-time Updates:** The `TimerDialog` now dynamically updates its alert threshold if the `Time Limit` is changed in the `TaskGrid` while the timer is running, using `TaskGrid`'s new `timeLimitChanged` signal.
    - **Visual Alert:** The `TimerDialog`'s background and button styles change to a prominent red color upon alert.
    - **Audio Alert:** A distinct beep sound plays when the 90% threshold is reached.
    - **Robust Handling:** Addresses edge cases for empty/invalid time limits (no alert triggered), manual time edits (alert state re-evaluated), and timer resets (alert state and styling reset).

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

