pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Controls.Fusion
import QtQuick.Layouts

import "../utils" as MyUtils
import "../components" as MyComponents

Page {
    id: root

    property font pageFont: Qt.font()

    background: Rectangle {
        color:colorLoader.background
    }

    MyUtils.ColorLoader {
        id: colorLoader
    }
    MyUtils.ImageLoader {
        id: imageLoader
    }

    ColumnLayout {
        id: pageColumnLayout
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        width: parent.width
        spacing: 4

        RowLayout {
            MyComponents.CircularButton {
                id: backButton

                isButton: true

                buttonColor: colorLoader.shimarin
                borderColor: colorLoader.shimarin_dark
                borderWidth: 3
                hoverScale: 1.25

                textFont: root.pageFont
                text: qsTr("←")
                textPixelSize: 16
                textColor: "white"
                textBold: true

                Layout.preferredWidth: 38
                Layout.preferredHeight: 38
                Layout.alignment: Qt.AlignTop | Qt.AlignLeft
                Layout.leftMargin: 8
                Layout.topMargin: 8

                onClicked: aboutViewModel.close()
            }
            MyComponents.CircularButton {
                id: questionButton

                isButton: true
                buttonColor: colorLoader.shimarin
                borderColor: colorLoader.shimarin_dark
                borderWidth: 3
                hoverScale: 1.25

                text: "?"
                textFont: root.pageFont
                textPixelSize: 20
                textColor: colorLoader.white
                textBold: true

                Layout.preferredWidth: 38
                Layout.preferredHeight: 38
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 8
                Layout.topMargin: 8

                onClicked: aboutViewModel.open_guide_link()
            }
        }
        
        MyComponents.CircularIconButton {
            id: logoContainer
            
            isButton: false

            iconSource: imageLoader.program
            buttonColor: colorLoader.shimarin_dark
            borderColor: colorLoader.shimarin_dark
            borderWidth: 4

            Layout.preferredWidth: 200
            Layout.preferredHeight: 200
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 20
            Layout.bottomMargin: 10
        }

        Text {
            id: titleText0
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true

            lineHeight: 1.1
            text: qsTr("SeaMarine\nAI번역 도구")
            font.family: root.pageFont.family
            font.pixelSize: 32
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            color: colorLoader.shimarin_dark
        }

        Text {
            id: titleText1
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            Layout.margins: 10

            lineHeight: 1.1
            text: qsTr("버전: 2.0.0")
            font.family: root.pageFont.family
            font.pixelSize: 20
            horizontalAlignment: Text.AlignHCenter
            color: colorLoader.shimarin_dark
        }

        Text {
            id: titleText2
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            Layout.margins: 4

            lineHeight: 1.1
            text: qsTr("By RainBuildingTree")
            font.family: root.pageFont.family
            font.pixelSize: 20
            horizontalAlignment: Text.AlignHCenter
            color: colorLoader.shimarin_dark
        }

        
    }
}
