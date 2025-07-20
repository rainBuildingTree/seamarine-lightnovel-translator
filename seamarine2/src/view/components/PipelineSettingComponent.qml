import QtQuick
import QtQuick.Layouts

import "." as MyComponents

Rectangle {
    id: root

    property color backgroundColor
    property color borderColor
    property color buttonBaseColor
    property color buttonCheckColor
    property color buttonHoverColor
    property color buttonColor
    property int buttonBorderWidth
    property font pageFont
    property string text
    property string number
    property bool checked

    color: backgroundColor
    border.color: borderColor
    border.width: 3
    radius: Math.min(width, height) / 2

    signal clicked()

    RowLayout {
        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter
        spacing: 0

        MyComponents.CircularButton {
            id: processNumber
            isButton: false

            buttonColor: root.buttonColor
            borderColor: root.borderColor
            borderWidth: 3
            hoverScale: 1.0

            text: root.number
            textFont: root.pageFont
            textPixelSize: 18
            textColor: "white"
            textBold: true

            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            Layout.alignment: Qt.AlignVCenter
            Layout.leftMargin: 6
            Layout.rightMargin: 6
        }

        Text {
            text: root.text
            font.family: root.pageFont.family
            color: "white"
            font.pixelSize: 16
            font.bold: true
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignLeft
            Layout.preferredHeight: 38
            Layout.preferredWidth: 160
            Layout.alignment: Qt.AlignVCenter | Qt.AlignLeft
        }

        Item {
            id: spacer

            Layout.preferredWidth: 86
            Layout.preferredHeight: 38
            Layout.alignment: Qt.AlignVCenter
            Layout.leftMargin: 6
            Layout.rightMargin: 6
        }

        MyComponents.CircularCheckbox {
            id: startButton
            isButton: true

            baseColor: root.buttonBaseColor
            checkColor: root.buttonCheckColor
            hoverColor: root.buttonHoverColor
            borderColor: root.borderColor
            borderWidth: root.buttonBorderWidth

            checked: root.checked

            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
            Layout.leftMargin: 0
            Layout.rightMargin: 6

            onClicked: root.clicked()
        }
    }
}