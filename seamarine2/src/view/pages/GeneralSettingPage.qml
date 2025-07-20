pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts

import "../components" as MyComponents
import "../utils" as MyUtils

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
        height: root.height

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

                onClicked: generalSettingViewModel.close()
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

                onClicked: generalSettingViewModel.open_guide_link()
            }
            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
            }

            MyComponents.CircularButton {
                id: saveButton

                isButton: true
                buttonColor: colorLoader.shimarin
                borderColor: colorLoader.shimarin_dark
                borderWidth: 3
                hoverScale: 1.25

                text: qsTr("저장")
                textFont: root.pageFont
                textPixelSize: 20
                textColor: colorLoader.white
                textBold: true

                Layout.preferredWidth: 64
                Layout.preferredHeight: 38
                Layout.alignment: Qt.AlignVCenter
                Layout.rightMargin: 8
                Layout.topMargin: 8

                onClicked: generalSettingViewModel.save_data(chunkSizeSet.fieldText, maxConcurrentRequestSet.fieldText, delaySet.fieldText)
            }
        }

        Text {
            id: titleText
            Layout.alignment: Qt.AlignLeft
            Layout.fillWidth: true
            Layout.margins: 10

            text: qsTr("일반 설정")
            font.family: root.pageFont.family
            font.pixelSize: 26
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            color: colorLoader.shimarin_dark
            lineHeight: 1.1
        }

        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            Layout.preferredHeight: 2
            Layout.margins: 10
            border.width: 0
            color: colorLoader.shimarin
        }

        MyComponents.ModelSettingComponent {
            id: chunkSizeSet
            pageFont: root.pageFont
            text: qsTr("최대 청크 사이즈")
            placeholderText: "1000-65536"
            textColor: colorLoader.shimarin_dark
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            fieldText: generalSettingViewModel.maxChunkSize
            validator: IntValidator {bottom: 1000; top: 65536}
            textFieldWidth: 90

            onClicked: {
                generalSettingViewModel.set_default("max_chunk_size")
                chunkSizeSet.fieldText = generalSettingViewModel.maxChunkSize
            }
        }

        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            Layout.preferredHeight: 2
            Layout.margins: 10
            border.width: 0
            color: colorLoader.shimarin
        }

        MyComponents.ModelSettingComponent {
            id: maxConcurrentRequestSet
            pageFont: root.pageFont
            text: qsTr("최대 동시 요청 수")
            placeholderText: "1-99"
            textColor: colorLoader.shimarin_dark
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            fieldText: generalSettingViewModel.maxConcurrentRequest
            validator: IntValidator {bottom: 1; top: 99}

            onClicked: {
                generalSettingViewModel.set_default("max_concurrent_request")
                maxConcurrentRequestSet.fieldText = generalSettingViewModel.maxConcurrentRequest
            }
        }

        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            Layout.preferredHeight: 2
            Layout.margins: 10
            border.width: 0
            color: colorLoader.shimarin
        }

        MyComponents.ModelSettingComponent {
            id: delaySet
            pageFont: root.pageFont
            text: qsTr("요청간 지연 (초)")
            placeholderText: "0-99"
            textColor: colorLoader.shimarin_dark
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            fieldText: generalSettingViewModel.requestDelay
            validator: IntValidator {bottom: 0; top: 99}

            onClicked: {
                generalSettingViewModel.set_default("request_delay")
                delaySet.fieldText = generalSettingViewModel.requestDelay
            }
        }

        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            Layout.preferredHeight: 2
            Layout.margins: 10
            border.width: 0
            color: colorLoader.shimarin
        }

        Item {
            Layout.fillHeight: true
            Layout.preferredWidth: 1
        }

        MyComponents.ModelSettingComponent {
            id: resetSetting
            pageFont: root.pageFont
            text: qsTr("프로그램 초기화\n주의: 프로그램이 종료됩니다\n되돌릴 수 없습니다")
            placeholderText: ""
            textColor: colorLoader.warning
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            validator: DoubleValidator {bottom: 0; top: 99}
            textFieldWidth: 0
            buttonText: qsTr("초기화")

            onClicked: generalSettingViewModel.reset_config()
        }


        Rectangle {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            Layout.preferredHeight: 2
            Layout.topMargin: 10
            Layout.bottomMargin: 4
            border.width: 0
            color: colorLoader.shimarin
        }

        Text {
            id: saveFailMessage
            Layout.alignment: Qt.AlignHCenter
            Layout.margins: 4
            visible: generalSettingViewModel.saveFailed
            text: qsTr("저장 실패!")
            font.family: root.pageFont.family
            font.pixelSize: 14
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            color: colorLoader.warning
            lineHeight: 1.1
        }
        Text {
            id: saveSuccessMessage
            Layout.alignment: Qt.AlignHCenter
            Layout.margins: 4
            visible: generalSettingViewModel.saveSucceed
            text: qsTr("저장 성공!")
            font.family: root.pageFont.family
            font.pixelSize: 14
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            color: colorLoader.shimarin_light
            lineHeight: 1.1
        }
    }
}