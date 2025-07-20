import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Fusion

import "." as MyComponents

Rectangle {
    id: root

    property color backgroundColor
    property color borderColor
    property color buttonColor
    property font pageFont
    property string text
    property string number
    property bool arcActive: false
    property color arcColor: "white"
    property int arcWidth: 3


    //Layout.fillWidth: true
    //Layout.preferredHeight: 48
    //Layout.alignment: Qt.AlignHCenter
    //Layout.leftMargin: 4
    //Layout.rightMargin: 4
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
            font.pixelSize: 18
            font.bold: true
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignLeft
            Layout.preferredHeight: 38
            Layout.preferredWidth: 252
            Layout.alignment: Qt.AlignVCenter | Qt.AlignLeft
        }
        
        MyComponents.CircularButton {
            id: startButton
            isButton: true

            buttonColor: root.buttonColor
            borderColor: root.borderColor
            borderWidth: 3
            hoverScale: 1.1

            text: "▶"
            textFont: root.pageFont
            textPixelSize: 18
            textColor: "white"
            textBold: true

            arcActive: root.arcActive
            arcColor: root.arcColor
            arcWidth: root.arcWidth

            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
            Layout.leftMargin: 6
            Layout.rightMargin: 6

            onClicked: root.clicked()
        }
    }
}