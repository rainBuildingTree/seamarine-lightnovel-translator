import QtQuick
import QtQuick.Controls.Fusion

pragma ComponentBehavior: Bound

Rectangle {
    id: root

    property bool isButton: true

    property color checkColor: "blue"
    property color baseColor: "white"
    property color hoverColor: "gray"
    property color borderColor: "lightgray"
    property int borderWidth: 3

    property bool checked

    signal clicked()

    radius: Math.min(width, height) / 2
    color: checked ? checkColor : baseColor
    border.color: root.borderColor
    border.width: borderWidth
    scale: 1.0

    MouseArea {
        enabled: root.isButton
        anchors.fill: parent
        onClicked: {
            root.clicked()
        }
    }
}