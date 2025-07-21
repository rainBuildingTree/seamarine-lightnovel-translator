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
        color: colorLoader.background
    }

    MyUtils.ColorLoader {
        id: colorLoader
    }
    MyUtils.ImageLoader {
        id: imageLoader
    }

    ColumnLayout {
        id: rootColumn
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        spacing: 4
        width: root.width

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

                onClicked: geminiApiResetViewModel.close()
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

                onClicked: geminiApiResetViewModel.open_api_guide()
            }
        }

        Item {
            id: spacer9
            Layout.preferredHeight: 32
            Layout.fillWidth: true
        }

        MyComponents.CircularIconButton {
            id: geminiIcon

            isButton: false

            iconSource: imageLoader.gemini
            buttonColor: colorLoader.white
            borderColor: colorLoader.shimarin_dark
            borderWidth: 4

            Layout.preferredWidth: 120
            Layout.preferredHeight: 120
            Layout.alignment: Qt.AlignHCenter
        }

        Item {
            id: spacer0
            Layout.preferredHeight: 4
            Layout.fillWidth: true
        }

        Text {
            id: titleText
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true

            text: qsTr("Google Gemini\nApi Key를\n등록하세요")
            font.family: root.pageFont.family
            font.pixelSize: 26
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            color: colorLoader.shimarin_dark
            lineHeight: 1.1
        }

        Item {
            id: spacer1
            Layout.preferredHeight: 12
            Layout.fillWidth: true
        }

        Text {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter
            
            text: qsTr("현재 API KEY: %1").arg(geminiApiResetViewModel.geminiApiKey)
            font.family: root.pageFont.family
            font.pixelSize: 12
            horizontalAlignment: Text.AlignHCenter
            color: colorLoader.shimarin_dark
        }
        TextField {
            id: geminiApiTextField
            Layout.preferredWidth: 288
            Layout.preferredHeight: 32
            Layout.alignment: Qt.AlignHCenter
            font.pixelSize: 12
            color: colorLoader.shimarin_dark
            leftPadding: 10
            rightPadding: 10

            background: Rectangle {
                id: geminiApiTextFieldBackground
                width: 288
                height: 32
                radius: 16
                color: "white"
                border.color: colorLoader.shimarin_dark
                border.width: 3
            }
            Text {
                id: customPlaceholder
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                text: qsTr("여기에 Gemini API Key를 입력하세요.")
                font.family: root.pageFont.family
                font.pixelSize: 12
                color: "grey"

                visible: geminiApiTextField.text.length === 0
            }
        }

        Text {
            id: apiValidationText
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignHCenter
            visible: geminiApiResetViewModel.isApiKeyInvalid
            
            text: qsTr("유효하지 않은 API Key입니다.")
            font.family: root.pageFont.family
            font.pixelSize: 12
            horizontalAlignment: Text.AlignHCenter
            color: colorLoader.warning
        }

        MyComponents.CircularButton {
            id: checkApiButton

            isButton: true
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            borderWidth: 3
            hoverScale: 1.25

            text: qsTr("API Key 찾기")
            textFont: root.pageFont
            textColor: "white"
            textPixelSize: 12
            textBold: true

            Layout.preferredWidth: 80
            Layout.preferredHeight: 32
            Layout.alignment: Qt.AlignHCenter

            onClicked: geminiApiResetViewModel.open_api_link()
        }

        Item {
            id: spacer2
            Layout.preferredHeight: 30
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
            arcActive: geminiApiResetViewModel.isChecking

            textFont: root.pageFont
            text: "→"
            textPixelSize: 32
            textBold: true

            Layout.preferredWidth: 80
            Layout.preferredHeight: 80
            Layout.alignment: Qt.AlignHCenter

            onClicked: geminiApiResetViewModel.run_next_button_action(geminiApiTextField.text)
        }

        Text {
            id: startText
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true

            text: qsTr("등록")
            font.family: root.pageFont.family
            font.pixelSize: 16
            color: colorLoader.shimarin_dark
            horizontalAlignment: Text.AlignHCenter
        }
    }
}