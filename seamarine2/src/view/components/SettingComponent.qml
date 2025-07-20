import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Fusion

import "." as MyComponents

Rectangle {
    id: root

    //Layout.preferredWidth: 340
    //Layout.preferredHeight: 128
    //Layout.alignment: Qt.AlignHCenter
    //Layout.margins: 4

    property color borderColor: "gray"
    property color innerBorderColor: "gray"
    property color textColor: "gray"
    property string imageSource: ""
    property font pageFont: Qt.font()
    property string text: ""

    radius: 25

    color: "#FCFCF8"
    border.color: borderColor
    border.width: 4

    signal clicked()

    RowLayout {
        anchors.verticalCenter: parent.verticalCenter
        height: parent.height

        MyComponents.CircularIconButton {
            isButton: false
            iconSource: root.imageSource
            buttonColor: "#FDFDFD"
            borderColor: root.innerBorderColor
            borderWidth: 4

            Layout.preferredWidth: root.height - 28
            Layout.preferredHeight: root.height - 28
            Layout.alignment: Qt.AlignVCenter
            Layout.margins: 10
            radius: 50

        }

        Text {
            text: root.text
            font.family: root.pageFont.family
            color: root.textColor
            font.pixelSize: 24
            font.bold: true
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignLeft
            lineHeight: 1.1
            Layout.preferredHeight: 38
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignVCenter | Qt.AlignLeft
        }
    }

    MouseArea {
        enabled: true
        anchors.fill: parent
        hoverEnabled: true
        onEntered: root.scale = 1.05
        onExited: root.scale = 1.0
        onClicked: root.clicked()
    }

    Behavior on scale {
        NumberAnimation {
            duration: 200
            easing.type: Easing.InOutQuad
        }
    }
}