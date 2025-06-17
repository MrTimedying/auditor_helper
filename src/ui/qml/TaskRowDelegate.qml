import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: rowRoot
    width: parent.width  // CRITICAL: Set explicit width for MouseArea to work
    height: 35
    color: {
        if (temporaryHighlight) return "#4a5a3a"  // Green highlight for new task
        if (isSelected) return "#3a3b35"
        return (index % 2 === 0 ? "#232423" : "#282928")
    }
    border.color: isSelected ? "#5a5b55" : "#1a1b1a"  // Visible border for selected rows
    border.width: isSelected ? 2 : 1
    
    // Smooth color transitions
    Behavior on color {
        ColorAnimation { duration: 300 }
    }
    
    // Reference to outer grid view root for callbacks
    property var gridRoot
    
    // Properties for task data
    property int taskId: 0
    property string attemptId: ""
    property string duration: ""
    property string projectId: ""
    property string projectName: ""
    property string operationId: ""
    property string timeLimit: ""
    property string dateAudited: ""
    property string score: ""
    property string feedback: ""
    property string taskLocale: ""
    property string timeBegin: ""
    property string timeEnd: ""
    
    // Selection and interaction properties
    property bool isSelected: false
    property var columnWidths: []
    property bool temporaryHighlight: false
    
    // Signals
    signal rowClicked(int taskId)
    signal rowDoubleClicked(int taskId)
    
    // Debug: Check if delegate is created
    // TaskRowDelegate setup
    
    // Row content
    Row {
        anchors.fill: parent
        
        // Attempt ID
        TaskCell {
            width: columnWidths[0] || 100
            height: parent.height
            text: rowRoot.attemptId
            displayText: rowRoot.attemptId
        }
        
        // Duration
        TaskCell {
            width: columnWidths[1] || 90
            height: parent.height
            text: rowRoot.duration
            displayText: rowRoot.duration
            backgroundColor: rowRoot.duration === "00:00:00" ? "#4a2c2c" : "transparent"  // Special highlighting
        }
        
        // Project ID
        TaskCell {
            width: columnWidths[2] || 90
            height: parent.height
            text: rowRoot.projectId
            displayText: rowRoot.projectId
        }
        
        // Project Name
        TaskCell {
            width: columnWidths[3] || 160
            height: parent.height
            text: rowRoot.projectName
            displayText: rowRoot.projectName
        }
        
        // Operation ID
        TaskCell {
            width: columnWidths[4] || 90
            height: parent.height
            text: rowRoot.operationId
            displayText: rowRoot.operationId
        }
        
        // Time Limit
        TaskCell {
            width: columnWidths[5] || 90
            height: parent.height
            text: rowRoot.timeLimit
            displayText: rowRoot.timeLimit
            backgroundColor: rowRoot.timeLimit === "00:00:00" ? "#4a2c2c" : "transparent"  // Special highlighting
        }
        
        // Date Audited
        TaskCell {
            width: columnWidths[6] || 110
            height: parent.height
            text: rowRoot.dateAudited
            displayText: rowRoot.dateAudited
        }
        
        // Score
        TaskCell {
            width: columnWidths[7] || 70
            height: parent.height
            text: rowRoot.score
            displayText: rowRoot.score
            backgroundColor: rowRoot.score === "0" ? "#4a2c2c" : "transparent"  // Special highlighting for score 0
        }
        
        // Feedback
        TaskCell {
            width: columnWidths[8] || 210
            height: parent.height
            text: rowRoot.feedback
            displayText: rowRoot.feedback.length > 30 ? rowRoot.feedback.substring(0, 27) + "..." : rowRoot.feedback
            backgroundColor: {
                if (rowRoot.feedback === "" || rowRoot.feedback === "None") return "#4a2c2c"  // Empty feedback only
                return "transparent"
            }
        }
        
        // Locale
        TaskCell {
            width: columnWidths[9] || 70
            height: parent.height
            text: rowRoot.taskLocale
            displayText: rowRoot.taskLocale
        }
        
        // Time Begin
        TaskCell {
            width: columnWidths[10] || 130
            height: parent.height
            text: rowRoot.timeBegin
            displayText: rowRoot.timeBegin === "None" ? "" : rowRoot.timeBegin
        }
        
        // Time End
        TaskCell {
            width: columnWidths[11] || 130
            height: parent.height
            text: rowRoot.timeEnd
            displayText: rowRoot.timeEnd === "None" ? "" : rowRoot.timeEnd
        }
    }
    
    // Selection indicator (optional visual enhancement)
    Rectangle {
        id: selectionIndicator
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: 3
        color: "#5a9fd4"  // Blue selection indicator
        visible: rowRoot.isSelected
    }
    
    // Mouse interaction (placed last so it's on top and can receive events)
    MouseArea {
        anchors.fill: parent
        hoverEnabled: true
        
        onClicked: {
            rowRoot.rowClicked(rowRoot.taskId)
        }
        
        onDoubleClicked: {
            rowRoot.rowDoubleClicked(rowRoot.taskId)
        }
    }
} 