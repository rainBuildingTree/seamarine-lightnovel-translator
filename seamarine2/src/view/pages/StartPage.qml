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
        anchors.centerIn: parent
        spacing: 4
        width: parent.width
        
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

        Item {
            id: spacer0
            Layout.preferredHeight: 10
            Layout.fillWidth: true
        }

        Text {
            id: greetingText
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true

            text: qsTr("안녕하세요!")
            font.family: root.pageFont.family
            font.pixelSize: 24
            horizontalAlignment: Text.AlignHCenter
            color: colorLoader.shimarin_dark
        }

        Item {
            id: spacer1
            Layout.preferredHeight: 20
            Layout.fillWidth: true
        }

        MyComponents.CircularButton {
            id: nextButton

            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_light
            borderWidth: 3
            hoverScale: 1.25

            arcColor: colorLoader.shimarin_light
            arcWidth: 6
            arcActive: startViewModel.isProcessing

            textFont: root.pageFont
            text: "→"
            textPixelSize: 32
            textBold: true

            Layout.preferredWidth: 80
            Layout.preferredHeight: 80
            Layout.alignment: Qt.AlignHCenter

            onClicked: startViewModel.run_next_button_action()
        }

        Text {
            id: startText
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true

            text: qsTr("시작하기")
            font.family: root.pageFont.family
            font.pixelSize: 16
            color: colorLoader.shimarin_dark
            horizontalAlignment: Text.AlignHCenter
        }
    }
}
