import QtQuick
import QtQuick.Shapes
import Qt5Compat.GraphicalEffects

pragma ComponentBehavior: Bound

Rectangle {
    id: root

    property bool isButton: true

    property string iconSource: ""
    property color buttonColor: "gray"
    property color borderColor: "gray"
    property int borderWidth: 0
    property real hoverScale: 1.25

    property bool arcActive: false
    property color arcColor: "white"
    property int arcWidth: 3
    property int arcLengthDegrees: 90
    property int arcRotationDuration: 1000

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

    Image {
        id: iconImage
        source: root.iconSource
        anchors.centerIn: root
        width: root.width - (2 * root.borderWidth)
        height: root.width - (2 * root.borderWidth)
        fillMode: Image.PreserveAspectCrop
        
        property int radius: width / 2
        
        layer.enabled: true
        layer.effect: OpacityMask {
            id: configureButtonOpacityMask
            maskSource: Rectangle {
                id: configureButtonMaskedRect
                width: iconImage.width
                height: iconImage.height
                radius: iconImage.radius
            }
        }
    }

    MouseArea {
        enabled: root.isButton
        anchors.fill: root
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