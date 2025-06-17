import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Layouts 1.15
import TaskModel 1.0

/*
 TaskGridView.qml
 Enhanced QML grid with unified dialog editing and improved row selection.
 Removed checkbox column, added double-click to edit, enhanced selection highlighting.
*/

Rectangle {
    id: root
    color: "#232423"  // Match TaskTable background from theme_manager.py
    
    property alias model: taskListView.model
    property int selectedCount: 0
    property var selectedRows: []
    
    // Scroll position preservation
    property real savedScrollPosition: 0.0
    property bool preserveScrollPosition: false
    
    // Signals
    signal taskDoubleClicked(int taskId)
    signal taskClicked(int taskId)
    signal selectionChanged()
    
    // Column widths (redistributed after removing 40px checkbox column)
    readonly property var columnWidths: [100, 90, 90, 160, 90, 90, 110, 70, 210, 70, 130, 130]
    //                                   ↑+20  ↑    ↑    ↑+10   ↑    ↑    ↑     ↑    ↑+10  ↑    ↑     ↑
    //                                   Att   Dur  Proj  Name   Op   Time Date  Scr  Feed  Loc  Begin End
    
    readonly property var columnNames: [
        "Attempt ID", "Duration", "Project ID", "Project Name", "Operation ID", 
        "Time Limit", "Date Audited", "Score", "Feedback", "Locale", "Time Begin", "Time End"
    ]
    
    // Computed width of all columns (used by fixed header & list view)
    readonly property real gridContentWidth: {
        var total = 0
        for (var i = 0; i < columnWidths.length; i++)
            total += columnWidths[i]
        return total
    }
    
    // Fixed header that stays visible while scrolling
    Rectangle {
        id: fixedHeader
        height: 30
        width: root.gridContentWidth
        anchors.top: parent.top
        x: -scrollView.contentItem.contentX // keep in sync with horizontal scroll
        z: 2
        color: "#1B1B1B"
        border.color: "#1f201f"
        border.width: 1

        Row {
            anchors.fill: parent
            Repeater {
                model: columnNames.length
                Rectangle {
                    width: columnWidths[index]
                    height: parent.height
                    color: "transparent"
                    border.color: "#1f201f"
                    border.width: 1

                    Text {
                        anchors.centerIn: parent
                        text: columnNames[index]
                        color: "#D6D6D6"
                        font.pixelSize: 11
                        font.bold: true
                    }
                }
            }
        }
    }
    
    // Note: Dialog handling is now done in Python via QML task grid
    
    function toggleRowSelection(index) {
        var currentlySelected = selectedRows.indexOf(index) !== -1
        
        if (currentlySelected) {
            // Remove from selection
            var newSelection = selectedRows.filter(function(i) { return i !== index })
            selectedRows = newSelection
        } else {
            // Add to selection
            selectedRows = selectedRows.concat([index])
        }
        
        selectedCount = selectedRows.length
        // Removed premature selectionChanged() - let Python model handle the signal
        
        // Update visual selection in the model
        if (root.model) {
            root.model.setRowSelected(index, !currentlySelected)
        }
    }
    
    function clearSelection() {
        selectedRows = []
        selectedCount = 0
        // Removed premature selectionChanged() - let Python model handle the signal
        
        // Clear selection in model
        if (root.model) {
            root.model.clearSelection()
        }
    }
    
    function selectAll() {
        if (root.model) {
            var rowCount = root.model.rowCount()
            selectedRows = []
            for (var i = 0; i < rowCount; i++) {
                selectedRows.push(i)
                root.model.setRowSelected(i, true)
            }
            selectedCount = selectedRows.length
            // Removed premature selectionChanged() - let Python model handle the signal
        }
    }
    
    function deleteSelectedRows() {
        if (selectedRows.length > 0 && root.model) {
            // Get task IDs for selected rows
            var taskIds = []
            for (var i = 0; i < selectedRows.length; i++) {
                var taskId = root.model.getTaskIdForRow(selectedRows[i])
                if (taskId > 0) {
                    taskIds.push(taskId)
                }
            }
            
            // Delete tasks
            if (taskIds.length > 0) {
                root.model.deleteTasksByIds(taskIds)
                clearSelection()
            }
        }
    }
    
    function saveScrollPosition() {
        if (scrollView.ScrollBar.vertical) {
            savedScrollPosition = scrollView.ScrollBar.vertical.position
            preserveScrollPosition = true
        }
    }
    
    function restoreScrollPosition() {
        if (preserveScrollPosition && scrollView.ScrollBar.vertical) {
            Qt.callLater(function() {
                scrollView.ScrollBar.vertical.position = savedScrollPosition
                preserveScrollPosition = false
            })
        }
    }
    
    function scrollToTask(taskId) {
        for (var i = 0; i < taskListView.count; i++) {
            var task = root.model.getTaskIdForRow(i)
            if (task === taskId) {
                taskListView.positionViewAtIndex(i, ListView.Center)
                // Highlight the new task briefly
                highlightNewTask(i)
                // Also select the new task for delete button logic
                root.toggleRowSelection(i)
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
    
    // Timer for removing highlight
    Timer {
        id: highlightTimer
        interval: 2500
        onTriggered: {
            // Remove highlight from all items
            for (var i = 0; i < taskListView.count; i++) {
                var item = taskListView.itemAtIndex(i)
                if (item) {
                    item.temporaryHighlight = false
                }
            }
        }
    }
    
    // Connections for handling model signals  
    Connections {
        target: root.model ? root.model : null
        ignoreUnknownSignals: true
        enabled: target !== null
        
        function onTaskAdded(taskId) {
            Qt.callLater(function() {
                scrollToTask(taskId)
            })
        }
        
        function onModelAboutToBeReset() {
            root.saveScrollPosition()
        }
        
        function onModelReset() {
            Qt.callLater(function() {
                root.restoreScrollPosition()
            })
        }
    }
    
    // Combined ScrollView for both header and content
    ScrollView {
        id: scrollView
        anchors.fill: parent
        clip: true
        
        // Custom ScrollBars for dark theme
        ScrollBar.vertical: ScrollBar {
            // Hide the vertical scrollbar while keeping vertical scrolling functional
            visible: false
            interactive: false // Ensure it does not capture mouse events

            // (anchors/size kept for completeness but width set to 0)
            anchors.right: parent.right
            anchors.top: parent.top
            anchors.bottom: parent.bottom
            width: 0
            policy: ScrollBar.AsNeeded
            
            background: Rectangle {
                implicitWidth: 0
                color: "#2B2B2B"
                radius: 0
            }
            
            contentItem: Rectangle {
                implicitWidth: 0
                radius: 4
                color: parent.pressed ? "#555555" : 
                       parent.hovered ? "#444444" : "#333333"
                
                Behavior on color {
                    ColorAnimation { duration: 150 }
                }
            }
        }
        
        ScrollBar.horizontal: ScrollBar {
            // Anchor to bottom, spanning full width
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 2

            height: 10
            policy: ScrollBar.AlwaysOn
            
            background: Rectangle {
                implicitHeight: 10
                color: "#2B2B2B"
                radius: 5
            }
            
            contentItem: Rectangle {
                implicitHeight: 6
                radius: 4
                color: parent.pressed ? "#555555" : 
                       parent.hovered ? "#444444" : "#333333"
                
                Behavior on color {
                    ColorAnimation { duration: 150 }
                }
            }
        }
        
        Column {
            width: Math.max(scrollView.width, contentWidth)
            
            // Calculate content width based on column widths
            property real contentWidth: {
                var total = 0
                for (var i = 0; i < columnWidths.length; i++) {
                    total += columnWidths[i]
                }
                return total
            }
            
            // Invisible spacer to account for fixed header height
            Rectangle {
                width: parent.contentWidth
                height: fixedHeader.height
                opacity: 0
            }
            
            // Task List
            ListView {
                id: taskListView
                width: parent.contentWidth
                height: scrollView.height - fixedHeader.height
                model: root.model
                
                // Add bottom spacing
                footer: Rectangle {
                    width: parent.width
                    height: 20
                    color: "transparent"
                }
        
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
        
        onModelChanged: {
            if (model && model.modelAboutToBeReset) {
                model.modelAboutToBeReset.connect(function() {
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
        
        delegate: TaskRowDelegate {
            width: taskListView.width
            height: 35
            
            // Delegate setup
            
            // Pass all task data to delegate
            taskId: model.taskId || 0
            attemptId: model.attemptId || ""
            duration: model.duration || ""
            projectId: model.projectId || ""
            projectName: model.projectName || ""
            operationId: model.operationId || ""
            timeLimit: model.timeLimit || ""
            dateAudited: model.dateAudited || ""
            score: model.score || ""
            feedback: model.feedback || ""
            taskLocale: model.locale || ""
            timeBegin: model.timeBegin || ""
            timeEnd: model.timeEnd || ""
            
            // Selection state
            isSelected: selectedRows.indexOf(index) !== -1
            
            // Column configuration
            columnWidths: root.columnWidths
            
            // Reference to outer grid view root
            gridRoot: root
            
            onRowClicked: function(taskId) {
                root.taskClicked(taskId)
                root.toggleRowSelection(index)
            }
            
            onRowDoubleClicked: function(taskId) {
                root.taskDoubleClicked(taskId)
                // Note: Dialog opening is handled by Python side via taskDoubleClicked signal
            }
        }
        
                // No additional scrollbar needed - handled by parent ScrollView
            }
        }
    }
    
    // Keyboard handling
    Keys.onPressed: function(event) {
        if (event.key === Qt.Key_Delete) {
            deleteSelectedRows()
            event.accepted = true
        } else if (event.key === Qt.Key_Return || event.key === Qt.Key_Enter) {
            if (selectedRows.length === 1) {
                var taskId = root.model.getTaskIdForRow(selectedRows[0])
                if (taskId > 0) {
                    openTaskEditDialog(taskId)
                }
            }
            event.accepted = true
        } else if (event.key === Qt.Key_Space) {
            if (selectedRows.length === 1) {
                var taskId = root.model.getTaskIdForRow(selectedRows[0])
                if (taskId > 0) {
                    openTaskEditDialog(taskId)
                }
            }
            event.accepted = true
        } else if (event.key === Qt.Key_Escape) {
            clearSelection()
            event.accepted = true
        } else if (event.key === Qt.Key_A && (event.modifiers & Qt.ControlModifier)) {
            selectAll()
            event.accepted = true
        }
    }
    
    // Focus handling
    focus: true
    activeFocusOnTab: true
} 