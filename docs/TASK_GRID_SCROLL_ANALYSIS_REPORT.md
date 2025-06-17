# TaskGridView Scroll Behavior Analysis Report

## Executive Summary

This report analyzes the TaskGridView QML component and related files to identify the root cause of the "grid refreshes to top" behavior when adding new tasks, and provides multiple solution approaches to improve the user experience.

## Current Behavior Analysis

### 1. Problem Description
When the "Add New Task" button is pressed:
1. A new task is created at the bottom of the list (due to `ORDER BY id ASC`)
2. The grid refreshes completely and jumps to the top
3. Users must manually scroll down to find the newly created task
4. This creates a frustrating UX, especially with large task lists

### 2. Root Cause Analysis

#### The Culprit: Model Reset Pattern
The issue stems from the data flow in `qml_task_grid.py` → `qml_task_model.py`:

**In `qml_task_grid.py` (lines 175-220):**
```python
def create_task_in_week(self, week_id):
    # ... task creation logic ...
    
    # THIS IS THE CULPRIT: Full refresh after creation
    self.refresh_tasks(week_id)
```

**In `qml_task_model.py` (lines 233-250):**
```python
def refreshTasks(self, weekId):
    """Refresh tasks for a specific week"""
    self.beginResetModel()  # <-- FULL MODEL RESET
    self.current_week_id = weekId
    self.selected_tasks.clear()
    
    # Re-fetch ALL tasks from database
    with get_db_connection() as conn:
        c = conn.cursor()
        c.execute("""SELECT ... FROM tasks WHERE week_id = ? ORDER BY id ASC""", (weekId,))
        self.tasks = c.fetchall()
    
    self.endResetModel()  # <-- TRIGGERS COMPLETE VIEW REFRESH
```

#### Why Scroll Position Is Lost
The `beginResetModel()` and `endResetModel()` calls trigger a complete reconstruction of the QML ListView, which:
1. Destroys all existing delegates
2. Recreates the entire view structure
3. Resets scroll position to 0 (top)
4. The scroll position preservation logic in TaskGridView.qml fails because it only works for regular data changes, not model resets

### 3. Current Scroll Preservation Logic Analysis

**In TaskGridView.qml (lines 257-287):**
```qml
Component.onCompleted: {
    // Connect to model's aboutToBeReset signal to save scroll position
    if (root.model && root.model.modelAboutToBeReset) {
        root.model.modelAboutToBeReset.connect(function() {
            if (scrollView.ScrollBar.vertical) {
                root.savedScrollPosition = scrollView.ScrollBar.vertical.position
                root.preserveScrollPosition = true
            }
        })
    }
}

onCountChanged: {
    // Restore scroll position if needed
    if (root.preserveScrollPosition && count > 0) {
        Qt.callLater(function() {
            if (scrollView.ScrollBar.vertical) {
                scrollView.ScrollBar.vertical.position = root.savedScrollPosition
                root.preserveScrollPosition = false
            }
        })
    }
}
```

**Issue:** The `QMLTaskModel` doesn't emit `modelAboutToBeReset` signal - it uses Qt's built-in `beginResetModel()` which emits `modelAboutToBeReset()` but the connection pattern in the QML might not be working correctly.

## Solution Approaches

### Solution 1: Smart Scroll to New Task (Recommended)

**Approach:** Instead of preserving scroll position, automatically scroll to the newly created task.

#### Implementation Plan:

**Step 1:** Add signals and properties to track new task creation
```python
# In qml_task_model.py - Add new signal
taskAdded = QtCore.Signal(int)  # task_id

# In create_task_in_week method, emit signal with new task ID
def create_task_in_week(self, week_id):
    # ... existing creation logic ...
    task_id = self.task_dao.create_task(...)
    
    # Instead of immediate refresh, emit signal first
    self.new_task_created.emit(task_id)
    self.refresh_tasks(week_id)
```

**Step 2:** Add scroll-to-task functionality in QML
```qml
// In TaskGridView.qml - Add new functions
function scrollToTask(taskId) {
    for (var i = 0; i < taskListView.count; i++) {
        var task = root.model.getTaskIdForRow(i)
        if (task === taskId) {
            taskListView.positionViewAtIndex(i, ListView.Center)
            // Optional: Highlight the new task briefly
            highlightNewTask(i)
            break
        }
    }
}

function highlightNewTask(index) {
    // Add visual highlight for 2-3 seconds
    var item = taskListView.itemAtIndex(index)
    if (item) {
        item.temporaryHighlight = true
        highlightTimer.start()
    }
}

Timer {
    id: highlightTimer
    interval: 2500
    onTriggered: {
        // Remove highlight
        for (var i = 0; i < taskListView.count; i++) {
            var item = taskListView.itemAtIndex(i)
            if (item) item.temporaryHighlight = false
        }
    }
}

// Connect to model's taskAdded signal
Connections {
    target: root.model
    function onTaskAdded(taskId) {
        Qt.callLater(function() {
            scrollToTask(taskId)
        })
    }
}
```

**Step 3:** Update TaskRowDelegate.qml for highlighting
```qml
// Add temporary highlight property
property bool temporaryHighlight: false

// Update background color calculation
color: {
    if (temporaryHighlight) return "#4a5a3a"  // Green highlight for new task
    if (isSelected) return "#3a3b35"
    return (index % 2 === 0 ? "#232423" : "#282928")
}

Behavior on color {
    ColorAnimation { duration: 300 }
}
```

### Solution 2: Auto-Open Dialog (Alternative)

**Approach:** Automatically open the edit dialog after creating a new task.

#### Implementation Plan:

**Step 1:** Add settings option
```python
# In global_settings.py
AUTO_EDIT_NEW_TASKS = "auto_edit_new_tasks"  # Boolean setting
```

**Step 2:** Modify task creation flow
```python
# In qml_task_grid.py
def create_task_in_week(self, week_id):
    # ... existing creation logic ...
    task_id = self.task_dao.create_task(...)
    
    # Refresh first
    self.refresh_tasks(week_id)
    
    # Check setting for auto-edit
    if global_settings.get_setting(GlobalSettings.AUTO_EDIT_NEW_TASKS, False):
        # Open edit dialog automatically
        QtCore.QTimer.singleShot(200, lambda: self.open_task_edit_dialog(task_id))
```

**Step 3:** Add UI toggle in settings
```python
# In options dialog - add checkbox
self.auto_edit_checkbox = QtWidgets.QCheckBox("Auto-edit new tasks")
self.auto_edit_checkbox.setToolTip("Automatically open edit dialog when creating new tasks")
```

### Solution 3: Improved Scroll Preservation (Backup)

**Approach:** Fix the existing scroll preservation logic.

#### Implementation Plan:

**Step 1:** Add proper model signals
```python
# In qml_task_model.py
modelAboutToBeReset = QtCore.Signal()
modelReset = QtCore.Signal()

def refreshTasks(self, weekId):
    # Emit custom signal before reset
    self.modelAboutToBeReset.emit()
    
    self.beginResetModel()
    # ... existing logic ...
    self.endResetModel()
    
    # Emit custom signal after reset
    self.modelReset.emit()
```

**Step 2:** Update QML connections
```qml
Connections {
    target: root.model
    function onModelAboutToBeReset() {
        root.saveScrollPosition()
    }
    function onModelReset() {
        Qt.callLater(function() {
            root.restoreScrollPosition()
        })
    }
}
```

### Solution 4: Hybrid Approach (Best UX)

Combine multiple solutions:
1. **Default:** Scroll to new task + brief highlight
2. **Optional:** Auto-edit setting for power users
3. **Fallback:** Improved scroll preservation for other model updates

## Implementation Priority

### Phase 1: Core Fix (Solution 1)
- ✅ High impact, addresses core UX issue
- ✅ Visually guides user to new content
- ✅ Minimal complexity

### Phase 2: User Options (Solution 2)
- ✅ Accommodates different workflows
- ✅ Power user feature
- ✅ Easy to implement

### Phase 3: General Improvements (Solution 3)
- ✅ Fixes scroll preservation for all model updates
- ✅ Benefits other operations (delete, edit, etc.)

## Additional UX Improvements

### 1. Smart Task Ordering
Consider adding tasks at the top instead of bottom:
```sql
-- Change from ORDER BY id ASC to ORDER BY id DESC
-- Or add timestamp and sort by creation time descending
```

### 2. Batch Operations
For users who create multiple tasks:
```python
# Add "Add Multiple Tasks" button
def add_multiple_tasks(self, count=5):
    task_ids = []
    for i in range(count):
        task_id = self.create_task_in_week_silent(self.current_week_id)
        task_ids.append(task_id)
    
    # Single refresh at the end
    self.refresh_tasks(self.current_week_id)
    
    # Scroll to first new task
    if task_ids:
        self.scroll_to_task(task_ids[0])
```

### 3. Visual Feedback
- Loading indicators during task creation
- Success animations
- Toaster notifications with "Go to task" button

## Testing Considerations

### Test Cases:
1. **Basic:** Add task → verify scroll to new task
2. **Multiple:** Add several tasks rapidly
3. **Large dataset:** Test with 100+ tasks
4. **Performance:** Measure scroll animation smoothness
5. **Settings:** Test auto-edit toggle functionality
6. **Edge cases:** Empty list, single task, maximum tasks

### Performance Impact:
- Minimal: Only affects task creation flow
- No impact on existing scroll operations
- Single database query remains unchanged

## Conclusion

The root cause is the `beginResetModel()`/`endResetModel()` pattern that completely destroys and recreates the view. The recommended solution is to implement **Solution 1** (Smart Scroll to New Task) as it:

1. **Solves the core problem** - Users immediately see their new task
2. **Improves UX** - No manual scrolling required
3. **Provides visual feedback** - Temporary highlighting shows what was created
4. **Low complexity** - Minimal code changes required
5. **Future-proof** - Can be extended with additional features

The hybrid approach (combining Solutions 1, 2, and 3) would provide the most comprehensive improvement to the user experience while maintaining flexibility for different user workflows. 