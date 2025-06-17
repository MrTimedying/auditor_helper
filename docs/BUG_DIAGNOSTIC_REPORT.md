# Bug Diagnostic Report

## Introduction
This document details the diagnostic analysis of two reported bugs in the Auditor Helper application:
1.  **Task/Row Deletion Button Discrepancy:** The button displaying the number of selected tasks/rows in the task grid does not always show the correct count.
2.  **Week Selection Dropdown Issue:** The dropdown menu in the "Week Customization" section of the options dialog is not allowing week selection.

The goal of this report is to provide a complete analytical breakdown of each bug, identify the root cause, and propose potential solutions.

---

## Bug 1: Task/Row Deletion Button Discrepancy

### Description
The button responsible for deleting selected tasks/rows in the QML-based task grid (`QMLTaskGrid`) occasionally displays an incorrect count of selected items. For example, it might show "Delete Rows (0)" when multiple rows are clearly selected, or an outdated count after selection changes.

### Initial Investigation & Hypotheses
*   **Component Interaction:** The `QMLTaskGrid` (Python) uses a `QMLTaskModel` (Python) as its data model for the QML `TaskGridView.qml`. The `MainWindow` (Python) in `main.py` is responsible for updating the "Delete Rows" button based on the `selected_tasks` property of `QMLTaskGrid`, which in turn gets its data from `QMLTaskModel`.
*   **Data Flow:**
    *   `TaskGridView.qml` handles visual selection (`toggleRowSelection`, `clearSelection`, `selectAll`).
    *   `TaskGridView.qml` calls `root.model.setRowSelected(index, selected)` and `root.model.clearSelection()` to update the `QMLTaskModel`.
    *   `QMLTaskModel.setTaskSelection` and `QMLTaskModel.clearSelection` update `self.selected_tasks` (a Python set) and emit `selectionChanged` signal.
    *   `QMLTaskGrid` connects `self.task_model.selectionChanged` to `_on_selection_changed`.
    *   `QMLTaskGrid._on_selection_changed` emits `EventType.TASK_SELECTION_CHANGED` via the event bus and calls `self.main_window.update_delete_button()`.
    *   `MainWindow.update_delete_button` reads `len(self.task_grid.selected_tasks)` to set the button text.

### Detailed Analysis

#### `src/ui/qml/TaskGridView.qml` Analysis
The QML code manages its own `selectedRows` array and `selectedCount` property.
*   `toggleRowSelection(index)`: Adds/removes the row index from `selectedRows` and updates `selectedCount`. It then calls `root.model.setRowSelected(index, !currentlySelected)` and emits `selectionChanged()`.
*   `clearSelection()`: Clears `selectedRows`, sets `selectedCount` to 0, and calls `root.model.clearSelection()` and emits `selectionChanged()`.
*   `selectAll()`: Populates `selectedRows` with all row indices, updates `selectedCount`, and calls `root.model.setRowSelected(i, true)` for each row. It also emits `selectionChanged()`.

**Potential Issue:** The `selectionChanged()` signal within `TaskGridView.qml` is a *QML signal*. While `QMLTaskGrid` connects to `root_object.selectionChanged` (which is this QML signal), it also connects to `self.task_model.selectionChanged` (a Python signal). This dual notification path might introduce redundancy or out-of-sync issues if not carefully managed. More critically, the QML signal `selectionChanged()` is emitted *before* the Python model (`root.model.setRowSelected` or `root.model.clearSelection`) has finished processing all updates, especially in `selectAll()`. This means when `_on_selection_changed` in `QMLTaskGrid` is triggered by the QML signal, `self.task_model.selected_tasks` might not yet be fully updated.

#### `src/ui/qml_task_model.py` Analysis
*   `setTaskSelection(taskId, selected)`: Correctly adds/removes `taskId` from `self.selected_tasks` and then emits `self.selectionChanged.emit()`. This seems correct.
*   `clearSelection()`: Clears `self.selected_tasks`, calls `beginResetModel()`/`endResetModel()`, and then emits `self.selectionChanged.emit()`. This also seems correct.
*   `refreshTasks(weekId)`: Clears `self.selected_tasks` and then calls `beginResetModel()`/`endResetModel()`. It *does not* explicitly emit `self.selectionChanged` here. If `refreshTasks` is called, and there were previous selections, the `selected_tasks` will be cleared, but the delete button might not update immediately if `selectionChanged` isn't emitted after `endResetModel()`.

#### `src/main.py` Analysis
*   `update_delete_button()`: This method simply reads `len(self.task_grid.selected_tasks)`. This confirms that the problem is upstream: if `self.task_grid.selected_tasks` (which is `self.task_model.selected_tasks`) is incorrect, the button will display the wrong count.
*   `QMLTaskGrid._on_selection_changed`: This method is connected to `self.task_model.selectionChanged` and `root_object.selectionChanged` (QML). It calls `self.main_window.update_delete_button()`.

### Root Cause Hypothesis for Bug 1
The primary root cause is likely a timing issue or an incomplete state update when selections occur, specifically during operations like "Select All" or when the `QMLTaskModel` is reset.
1.  When `selectAll()` is called in QML, it iterates and calls `setRowSelected` for each row. Each call to `setRowSelected` in Python emits `dataChanged` and then `selectionChanged`. This could lead to `update_delete_button` being called multiple times during a single "Select All" operation, potentially with intermediate, incorrect counts.
2.  More critically, `QMLTaskGrid._on_selection_changed` is connected to *both* the Python `task_model.selectionChanged` and the QML `root_object.selectionChanged`. If the QML `selectionChanged()` signal (emitted *before* all individual `setRowSelected` calls complete in QML's `selectAll` or even before Python fully processes them) triggers `_on_selection_changed` and thus `update_delete_button`, the count will be wrong.
3.  The `refreshTasks` method in `QMLTaskModel` clears `self.selected_tasks` but does not emit `selectionChanged`. If a week change or refresh occurs, the selection count on the button might not reset to zero.

### Proposed Solution for Bug 1

1.  **Consolidate Selection Notification:**
    *   In `src/ui/qml/TaskGridView.qml`:
        *   Modify `toggleRowSelection`, `clearSelection`, and `selectAll` to *not* emit `selectionChanged()` immediately after updating `selectedRows`.
        *   Instead, ensure that `root.model.setRowSelected` and `root.model.clearSelection` are the *sole* mechanisms for updating the Python model's selection state.
    *   In `src/ui/qml_task_model.py`:
        *   Ensure that `setTaskSelection` and `clearSelection` reliably update `self.selected_tasks` and emit `self.selectionChanged`.
        *   **Crucially, in `refreshTasks`, after clearing `self.selected_tasks` and calling `endResetModel()`, explicitly emit `self.selectionChanged.emit()` to ensure the UI updates.**
    *   In `src/ui/qml_task_grid.py`:
        *   Remove the connection `root_object.selectionChanged.connect(self._on_selection_changed)` in `_setup_qml`. The `_on_selection_changed` method should *only* be triggered by `self.task_model.selectionChanged` (the Python signal). This ensures the button update happens only after the Python model's selection state is fully consistent.

2.  **Batch Updates (Optional but Recommended for Performance):** For `selectAll()` in QML, instead of calling `setRowSelected` for each individual row, consider introducing a batch selection mechanism in `QMLTaskModel` (e.g., `setMultipleTasksSelection(taskIds, selected)`). This would allow a single `selectionChanged` emit after all selections are processed, reducing redundant UI updates.

---

## Bug 2: Week Selection Dropdown Issue in Options Dialog

### Description
In the "Preferences" dialog, specifically under the "Week Customization" tab, the dropdown menu ("Select Week:") does not allow the user to select a week. It might appear unresponsive or not show the list of available weeks correctly.

### Initial Investigation & Hypotheses
*   **Relevant File:** `src/ui/options/week_customization_page.py` is responsible for this page.
*   **Key Methods:**
    *   `__init__`: Initializes `DataService` and `WeekDAO`.
    *   `setup_ui`: Creates the `QComboBox` (`self.week_combo`) and connects its `currentTextChanged` signal to `load_week_settings`.
    *   `load_settings`: Calls `load_weeks()`.
    *   `load_weeks`: Populates `self.week_combo` with weeks retrieved from `WeekDAO` or SQLite. It then calls `load_week_settings()` if items are added.
    *   `load_week_settings`: This method is expected to load and display settings for the selected week.

### Detailed Analysis

#### `src/ui/options/week_customization_page.py` Analysis

1.  **`__init__` and Data Service Initialization:**
    ```python
    # Initialize Data Service Layer
    try:
        self.data_service = DataService()
        self.week_dao = WeekDAO(self.data_service)
    except DataServiceError as e:
        print(f"Warning: Failed to initialize Data Service Layer: {e}")
        # Fallback to direct SQLite if needed
        self.data_service = None
        self.week_dao = None
    ```
    If `DataService` or `WeekDAO` initialization fails, `self.week_dao` could be `None`, leading to the fallback SQLite logic. We need to ensure that this fallback works or the primary data service is always available. The print statement `Warning: Failed to initialize Data Service Layer: {e}` would indicate issues here.

2.  **`load_weeks()` method:**
    ```python
    def load_weeks(self):
        """Load available weeks into the week combo box using Data Service Layer"""
        try:
            # Use Data Service Layer for week retrieval
            if self.week_dao:
                weeks_data = self.week_dao.get_all_weeks()
                weeks = [(week['week_label'],) for week in weeks_data]  # Convert to tuple format
            else:
                # Fallback to direct SQLite if Data Service Layer not available
                conn = sqlite3.connect('tasks.db')
                c = conn.cursor()
                c.execute("SELECT week_label FROM weeks ORDER BY id")
                weeks = c.fetchall()
                conn.close()
            
            self.week_combo.clear()
            for week in weeks:
                self.week_combo.addItem(week[0])
            
            if self.week_combo.count() > 0:
                self.load_week_settings()
                
        except (DataServiceError, Exception) as e:
            print(f"Error loading weeks: {e}")
    ```
    *   This method is responsible for populating the `week_combo`.
    *   If `weeks_data` from `self.week_dao.get_all_weeks()` is empty, or the SQLite query returns no results, the combo box will remain empty. This is a common reason for a non-selectable dropdown.
    *   The `print(f"Error loading weeks: {e}")` would be crucial for debugging if data retrieval fails.
    *   The line `weeks = [(week['week_label'],) for week in weeks_data]` assumes `weeks_data` is a list of dictionaries. If `weeks_data` is not in the expected format (e.g., list of tuples already), this conversion could cause issues. However, the `WeekDAO` is expected to return dictionaries.

3.  **`load_week_settings()` method (Not fully provided in initial context, but its role is key):**
    This method is called after weeks are loaded and when a new week is selected. If this method has an error or is not correctly retrieving/setting the UI control values based on the selected week, it could make it seem like the dropdown isn't working even if a selection is made internally. The relevant code for `load_week_settings` needs to be reviewed.

### Root Cause Hypothesis for Bug 2
The most probable root causes are:
1.  **No Weeks in Database:** The database (or the `WeekDAO`) is not returning any weeks, leading to an empty `QComboBox`.
2.  **`DataService` / `WeekDAO` Initialization Failure:** The `DataService` or `WeekDAO` might be failing to initialize, causing `self.week_dao` to be `None`, and the fallback SQLite query might also be failing or returning no data.
3.  **Issue within `load_week_settings()`:** Even if weeks are loaded into the combo box, `load_week_settings()` might be encountering an error or not correctly updating the UI elements, giving the impression that selection isn't working.

### Proposed Solution for Bug 2

1.  **Verify Data Availability:**
    *   Ensure that there are actual week entries in the `tasks.db` database. This can be checked manually or by adding a temporary debug print in `load_weeks()` to show `len(weeks_data)` or `len(weeks)`.
    *   Verify the `DataService` and `WeekDAO` initialization by checking for the "Warning: Failed to initialize Data Service Layer" print statement in the console.

2.  **Inspect `load_week_settings()`:**
    *   Add robust logging or print statements within `load_week_settings()` to verify that:
        *   It is being called when `currentTextChanged` is emitted.
        *   The `current_week_id` is correctly retrieved from the selected item.
        *   The `week_dao.get_week_by_id(week_id)` call successfully retrieves the week's settings.
        *   The UI controls (spin boxes, checkboxes, time edits) are being populated with the correct values from the loaded week settings without errors. Look for any `try-except` blocks that might be silently catching errors preventing UI updates.

3.  **Ensure Proper Fallback:** If `DataService` is intended to be the primary method, ensure that its initialization is robust. If not, confirm that the SQLite fallback in `load_weeks()` is correctly structured and accesses the database as expected.

---

## Conclusion

This report has detailed the diagnostic findings for both bugs. The task deletion button issue is likely a synchronization problem in the selection notification pipeline between QML and Python, compounded by potential missed updates during model resets. The week selection dropdown issue is most likely a data loading problem, either due to no weeks being present, a failure in data service initialization, or an error in loading settings into the UI controls.

The next steps involve implementing the proposed solutions and adding targeted debugging outputs to confirm the fixes. 