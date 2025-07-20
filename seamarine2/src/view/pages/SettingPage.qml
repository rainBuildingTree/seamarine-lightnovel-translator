import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Fusion
import QtQuick.Layouts

import "../components" as MyComponents
import "../utils" as MyUtils

Page {
    id: root

    property font pageFont: Qt.font()

    MyUtils.ColorLoader {
        id: colorLoader
    }
    MyUtils.ImageLoader {
        id: imageLoader
    }

    background: Rectangle {
        color: colorLoader.background
    }

    ColumnLayout {
        id: rootColumn
        anchors.horizontalCenter: parent.horizontalCenter 
        width: parent.width

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

            onClicked: settingViewModel.close()
        }

        MyComponents.SettingComponent {
            borderColor: colorLoader.shimarin_dark
            innerBorderColor: colorLoader.shimarin
            textColor: colorLoader.shimarin_dark
            imageSource: imageLoader.gemini
            text: qsTr("Google Gemini\nAPI Key 재설정")
            pageFont: root.pageFont

            Layout.preferredWidth: 340
            Layout.preferredHeight: 128
            Layout.alignment: Qt.AlignHCenter
            Layout.margins: 4

            onClicked: settingViewModel.open_api_reset()
        }
        MyComponents.SettingComponent {
            borderColor: colorLoader.shimarin_dark
            innerBorderColor: colorLoader.shimarin
            textColor: colorLoader.shimarin_dark
            imageSource: imageLoader.pipeline
            text: qsTr("번역 파이프라인 설정")
            pageFont: root.pageFont

            Layout.preferredWidth: 340
            Layout.preferredHeight: 128
            Layout.alignment: Qt.AlignHCenter
            Layout.margins: 4

            onClicked: settingViewModel.open_pipeline_setting()
        }
        MyComponents.SettingComponent {
            borderColor: colorLoader.shimarin_dark
            innerBorderColor: colorLoader.shimarin
            textColor: colorLoader.shimarin_dark
            imageSource: imageLoader.aiapi
            text: qsTr("AI/API 세부 설정")
            pageFont: root.pageFont

            Layout.preferredWidth: 340
            Layout.preferredHeight: 128
            Layout.alignment: Qt.AlignHCenter
            Layout.margins: 4

            onClicked: settingViewModel.open_ai_setting()
        }
        MyComponents.SettingComponent {
            borderColor: colorLoader.shimarin_dark
            innerBorderColor: colorLoader.shimarin
            textColor: colorLoader.shimarin_dark
            imageSource: imageLoader.info
            text: qsTr("프로그램 정보")
            pageFont: root.pageFont

            Layout.preferredWidth: 340
            Layout.preferredHeight: 128
            Layout.alignment: Qt.AlignHCenter
            Layout.margins: 4

            onClicked: settingViewModel.open_about()
        }
    }
}