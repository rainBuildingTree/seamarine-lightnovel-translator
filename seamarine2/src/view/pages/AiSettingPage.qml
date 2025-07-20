import QtQuick
import QtQuick.Controls
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
            text: "←"
            textPixelSize: 16
            textColor: "white"
            textBold: true

            Layout.preferredWidth: 38
            Layout.preferredHeight: 38
            Layout.alignment: Qt.AlignTop | Qt.AlignLeft
            Layout.leftMargin: 8
            Layout.topMargin: 8

            onClicked: aiSettingViewModel.close()
        }
        MyComponents.SettingComponent {
            borderColor: colorLoader.shimarin_dark
            innerBorderColor: colorLoader.shimarin
            textColor: colorLoader.shimarin_dark
            imageSource: imageLoader.aiapi
            text: qsTr("일반 설정")
            pageFont: root.pageFont

            Layout.preferredWidth: 340
            Layout.preferredHeight: 90
            Layout.alignment: Qt.AlignHCenter
            Layout.margins: 2

            onClicked: aiSettingViewModel.open_general_setting()
        }
        MyComponents.SettingComponent {
            borderColor: colorLoader.shimarin_dark
            innerBorderColor: colorLoader.shimarin
            textColor: colorLoader.shimarin_dark
            imageSource: imageLoader.aiapi
            text: qsTr("고유명사 추출 설정")
            pageFont: root.pageFont

            Layout.preferredWidth: 340
            Layout.preferredHeight: 90
            Layout.alignment: Qt.AlignHCenter
            Layout.margins: 2

            onClicked: aiSettingViewModel.open_pn_extract_setting()
        }
        MyComponents.SettingComponent {
            borderColor: colorLoader.shimarin_dark
            innerBorderColor: colorLoader.shimarin
            textColor: colorLoader.shimarin_dark
            imageSource: imageLoader.aiapi
            text: qsTr("전체 번역 설정")
            pageFont: root.pageFont

            Layout.preferredWidth: 340
            Layout.preferredHeight: 90
            Layout.alignment: Qt.AlignHCenter
            Layout.margins: 2

            onClicked: aiSettingViewModel.open_translate_setting()
        }
        MyComponents.SettingComponent {
            borderColor: colorLoader.shimarin_dark
            innerBorderColor: colorLoader.shimarin
            textColor: colorLoader.shimarin_dark
            imageSource: imageLoader.aiapi
            text: qsTr("제목/목차 번역 설정")
            pageFont: root.pageFont

            Layout.preferredWidth: 340
            Layout.preferredHeight: 90
            Layout.alignment: Qt.AlignHCenter
            Layout.margins: 2

            onClicked: aiSettingViewModel.open_toc_translate_setting()
        }
        MyComponents.SettingComponent {
            borderColor: colorLoader.shimarin_dark
            innerBorderColor: colorLoader.shimarin
            textColor: colorLoader.shimarin_dark
            imageSource: imageLoader.aiapi
            text: qsTr("검수 번역 설정")
            pageFont: root.pageFont

            Layout.preferredWidth: 340
            Layout.preferredHeight: 90
            Layout.alignment: Qt.AlignHCenter
            Layout.margins: 2

            onClicked: aiSettingViewModel.open_review_setting()
        }
        MyComponents.SettingComponent {
            borderColor: colorLoader.shimarin_dark
            innerBorderColor: colorLoader.shimarin
            textColor: colorLoader.shimarin_dark
            imageSource: imageLoader.aiapi
            text: qsTr("이미지 번역 설정")
            pageFont: root.pageFont

            Layout.preferredWidth: 340
            Layout.preferredHeight: 90
            Layout.alignment: Qt.AlignHCenter
            Layout.margins: 2

            onClicked: aiSettingViewModel.open_image_translate_setting()
        }
    }
}