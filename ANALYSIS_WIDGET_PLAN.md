# Analysis Widget Overhaul Plan

This document will detail the redesign and implementation of the `analysis_widget.py` to include advanced data visualization.

## Brainstorming Changes:

*   **UI Layout:**
    *   Two main tabs: "Numerical Statistics" and "Graphs".
*   **Data Selection:**
    *   **Option 1: Time Range Selection:**
        *   User selects a specific date range using a calendar.
        *   All task data within this range is fetched from the database.
    *   **Option 2: Specific Week Selection:**
        *   User selects a specific week using a dedicated selector.
    *   **Mutual Exclusivity:** Selecting one option automatically resets the other to a placeholder value.
*   **Tab 1: Numerical Statistics Content:**
    *   **Layout:**
        *   **First Row:** Two separate non-modifiable data grids side-by-side.
            *   **Time Range Aggregate Data Grid:** Displays consolidated data for the selected time range.
                *   **Columns:** `Total Time`, `Average Time`, `Time Limit Usage`, `Fail Rate`, `Bonus Tasks`, `Total Earnings`.
            *   **Daily Data Grid:** Displays data for each day within the selected time range, with days as rows.
                *   **Columns:** `Date`, `Total Time`, `Average Time`, `Time Limit Usage`, `Fail Rate`, `Bonus Tasks`, `Total Earnings`.
    *   **Section B: Project-Based Breakdown (non-modifiable tables/data grids)**
        *   **Time Range Aggregate Project Data:** A single data grid showing project breakdown for the entire selected time range.
        *   **Daily Project Data:** A single data grid showing project breakdown for a specific day. This grid will be dynamically updated based on a day selected from a dropdown, positioned in the top right of this data grid. The dropdown will be populated with all days that have tasks within the currently selected time range or week.
*   **Tab 2: Graphs Content - Flexible Charting System:**
    *   **Concept:** Users can dynamically select an 'Input Variable' (X-axis) and one or more 'Output Variables' (Y-axis) from a predefined list of available data points.
    *   **UI Controls:**
        *   **Variable Selection:** Lists where users can drag and drop variables between an "Available Variables" list and "Selected X Variable" and "Selected Y Variables" lists.
        *   **Chart Type Selection:** A dropdown menu for selecting `Line charts`, `Bar charts`, `Scatter plots`, or `Pie charts`.
    *   **Charting Area:** Only one chart will be displayed at a time, dynamically updating based on the selected variables and chart type.
    *   **Interactivity (QtCharts):** Standard interactive features that enhance data inspection will be prioritized, including zoom, pan, and tooltips.
    *   **Variable Inclusion:** Only quantitative (numerical) and categorical variables will be available. Non-quantitative/non-categorical variables (e.g., `feedback`) will be excluded.
    *   **Available Variables:**
        *   **Raw Task Data (from `tasks` table):**
            *   Categorical: `project_name`, `locale`
            *   Quantitative: `duration` (in seconds), `time_limit` (in seconds), `score`, `bonus_paid` (binary: 0 or 1)
        *   **Composite Metrics (calculated):**
            *   Quantitative: `Total Time`, `Average Time`, `Time Limit Usage`, `Fail Rate`, `Bonus Tasks Count`, `Total Earnings`
            *   Categorical (for aggregation): `Date Audited` (daily), `Week ID` (weekly)
    *   **X-axis (Input Variable):**
        *   User selects a single variable.
        *   Can be categorical (e.g., `project_name`, `locale`, `Date Audited`, `Week ID`) or continuous (e.g., `date_audited` if plotted as a time series).
    *   **Y-axis (Output Variables):**
        *   User can select one or more quantitative variables.
        *   If multiple are selected, they will be plotted as multiple series on the same chart (e.g., multiple lines on a line chart, grouped bars for a bar chart).
*   **Filtering and Grouping:**
    *   By task, project, client
    *   Custom categories/tags
*   **Export Options:**
    *   CSV, PDF, Image
*   **UI/UX Considerations:**
    *   Interactive charts (zoom, pan, tooltips)
    *   Responsive design
    *   User-friendly controls for filtering and aggregation

## Next Steps:

1.  **Charting Library Selection:**
    *   **Choice:** `PySide6.QtCharts`
    *   **Reasons:**
        *   **Native Integration:** Seamlessly integrates with the PySide6 application, providing excellent performance and a consistent look and feel.
        *   **Core Chart Types:** Supports all required chart types (line, bar, scatter, pie) directly within the Qt framework.
        *   **Dynamic Capabilities:** Capable of handling dynamic data updates and managing multiple series for flexible X/Y plotting.
        *   **Simpler Deployment:** Avoids the complexities and overhead of embedding web-based charting libraries.
    *   **Secondary Consideration:** `PyQtGraph` for highly specific interactive or large-dataset scientific plotting, if `QtCharts` proves insufficient for any advanced requirements.
2.  Design the UI layout and interaction flows for both the "Numerical Statistics" and "Graphs" tabs.
3.  Break down implementation into smaller, manageable tasks. 