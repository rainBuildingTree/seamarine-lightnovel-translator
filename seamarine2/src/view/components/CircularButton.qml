import QtQuick
import QtQuick.Shapes

pragma ComponentBehavior: Bound

Rectangle {
    id: root

    property bool isButton: true

    property color buttonColor: "gray"
    property color borderColor: "lightgray"
    property int borderWidth: 3
    property real hoverScale: 1.25

    property bool arcActive: false
    property color arcColor: "white"
    property int arcWidth: 3
    property int arcLengthDegrees: 90
    property int arcRotationDuration: 1000

    property font textFont: Qt.font()
    property string text: ""
    property int textPixelSize: 10
    property color textColor: "white"
    property bool textBold: false

    signal clicked()

    radius: Math.min(width, height) / 2
    color: root.buttonColor
    border.color: root.borderColor
    border.width: borderWidth
    scale: 1.0

    Shape {
        id: rotatingArc
        anchors.fill: root
        antialiasing: true
        visible: root.arcActive

        ShapePath {
            strokeColor: root.arcColor
            strokeWidth: root.arcWidth
            fillColor: "transparent"

            PathAngleArc {
                id: testing
                centerX: rotatingArc.width / 2
                centerY: rotatingArc.height / 2
                radiusX: root.radius
                radiusY: root.radius
                startAngle: 0
                sweepAngle: root.arcLengthDegrees

                Behavior on startAngle {
                    NumberAnimation {
                        duration: 1000
                    }
                }
            }
        }
        Timer {
            interval: 1000
            running: true
            repeat: true
            onTriggered: {
                testing.startAngle = testing.startAngle + (360 * 1000 / root.arcRotationDuration)
            }
        }
    }

    Text {
        text: root.text
        font.family: root.textFont.family
        color: root.textColor
        font.pixelSize: root.textPixelSize
        font.bold: root.textBold
        anchors.centerIn: parent
    }

    MouseArea {
        enabled: root.isButton
        anchors.fill: parent
        hoverEnabled: true
        onEntered: root.scale = root.hoverScale
        onExited: root.scale = 1.0
        onClicked: {
            root.clicked()
        }
    }

    Behavior on scale {
        NumberAnimation {
            duration: 200
            easing.type: Easing.InOutQuad
        }
    }
}