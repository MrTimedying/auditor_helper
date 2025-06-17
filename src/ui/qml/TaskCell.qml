import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root
    color: backgroundColor
    border.color: "#1f201f"
    border.width: 1
    
    property string text: ""
    property string displayText: text
    property bool editable: false
    property color backgroundColor: "transparent"
    
    signal textEdited(string newText)
    signal doubleClicked()
    
    TextInput {
        id: textInput
        anchors.fill: parent
        anchors.margins: 4
        text: root.displayText
        color: "#D6D6D6"
        font.pixelSize: 11
        verticalAlignment: Text.AlignVCenter
        horizontalAlignment: Text.AlignLeft
        readOnly: !root.editable
        selectByMouse: root.editable
        selectionColor: "#33342E"
        selectedTextColor: "#D6D6D6"
        clip: true
        
        Rectangle {
            anchors.fill: parent
            anchors.margins: -2
            color: root.editable ? "#2a2b2a" : "transparent"
            border.color: root.editable ? "#1f201f" : "transparent"
            border.width: root.editable ? 1 : 0
            radius: 2
            visible: textInput.activeFocus
            z: -1
        }
        
        onEditingFinished: {
            if (root.editable && text !== root.text) {
                root.textEdited(text)
            }
        }
        
        onActiveFocusChanged: {
            if (!activeFocus && root.editable && text !== root.text) {
                root.textEdited(text)
            }
        }
    }
    
    MouseArea {
        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        onDoubleClicked: root.doubleClicked()
        onClicked: {
            if (root.editable) {
                textInput.forceActiveFocus()
                textInput.selectAll()
            }
        }
    }
} 