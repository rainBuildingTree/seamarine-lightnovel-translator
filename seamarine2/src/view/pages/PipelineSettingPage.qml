pragma ComponentBehavior: Bound

import QtCore
import QtQuick
import QtQml
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

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
        spacing: 6
        width: parent.width

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

                onClicked: pipelineSettingViewModel.close()
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

                onClicked: pipelineSettingViewModel.open_pipeline_guide()
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

                onClicked: pipelineSettingViewModel.save_pipeline()
            }
        }

        Text {
            id: titleText
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            Layout.topMargin: 2
            Layout.bottomMargin: 2

            text: qsTr("번역 시작 버튼을 눌렀을 때\n진행할 프로세스들을\n선택 해주세요 ")
            font.family: root.pageFont.family
            font.pixelSize: 26
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            color: colorLoader.shimarin_dark
            lineHeight: 1.1
        }

        RowLayout {
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true
            Layout.bottomMargin: 20

            Rectangle {
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
                radius: 12
                color: "#f05650"
                border.color: colorLoader.shimarin_dark
                border.width: 3
            }

            Text {
                Layout.alignment: Qt.AlignVCenter
                text: qsTr("진행히지 않음")
                font.family: root.pageFont.family
                font.pixelSize: 18
                verticalAlignment: Text.AlignVCenter
                color: colorLoader.shimarin
            }

            Rectangle {
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: 24
                Layout.preferredHeight: 24
                radius: 12
                color: "#8cf062"
                border.color: colorLoader.shimarin_dark
                border.width: 3
            }

            Text {
                Layout.alignment: Qt.AlignVCenter
                text: qsTr("진행함")
                font.family: root.pageFont.family
                font.pixelSize: 18
                verticalAlignment: Text.AlignVCenter
                color: colorLoader.shimarin
            }
        }

        MyComponents.PipelineSettingComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            buttonBaseColor: "#f05650"
            buttonCheckColor: "#8cf062"
            buttonHoverColor: colorLoader.shimarin_light
            buttonBorderWidth: 6

            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("루비 제거")
            number: "1"

            checked: pipelineSettingViewModel.rubyRemovalActive

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4

            onClicked: pipelineSettingViewModel.toggle_ruby_removal()
        }

        MyComponents.PipelineSettingComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            buttonBaseColor: "#f05650"
            buttonCheckColor: "#8cf062"
            buttonHoverColor: colorLoader.shimarin_light
            buttonBorderWidth: 6

            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("고유명사 추출")
            number: "2"

            checked: pipelineSettingViewModel.pnExtractActive
            onClicked: pipelineSettingViewModel.toggle_pn_extract()

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4
        }

        MyComponents.PipelineSettingComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            buttonBaseColor: "#f05650"
            buttonCheckColor: "#8cf062"
            buttonHoverColor: colorLoader.shimarin_light
            buttonBorderWidth: 6
            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("고유명사 사전 수정")
            number: "3"

            checked: pipelineSettingViewModel.pnDictEditActive
            onClicked: pipelineSettingViewModel.toggle_pn_dict_edit()

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4
        }

        MyComponents.PipelineSettingComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            buttonBaseColor: "#f05650"
            buttonCheckColor: "#8cf062"
            buttonHoverColor: colorLoader.shimarin_light
            buttonBorderWidth: 6
            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("전체 번역")
            number: "4"

            checked: pipelineSettingViewModel.mainTranslationActive
            onClicked: pipelineSettingViewModel.toggle_main_translation()

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4
        }

        MyComponents.PipelineSettingComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            buttonBaseColor: "#f05650"
            buttonCheckColor: "#8cf062"
            buttonHoverColor: colorLoader.shimarin_light
            buttonBorderWidth: 6
            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("제목/목차 번역")
            number: "5"

            checked: pipelineSettingViewModel.tocTranslationActive
            onClicked: pipelineSettingViewModel.toggle_toc_translation()

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4
        }

        MyComponents.PipelineSettingComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            buttonBaseColor: "#f05650"
            buttonCheckColor: "#8cf062"
            buttonHoverColor: colorLoader.shimarin_light
            buttonBorderWidth: 6
            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("검수 번역 진행")
            number: "6"

            checked: pipelineSettingViewModel.reviewActive
            onClicked: pipelineSettingViewModel.toggle_review()

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4
        }

        MyComponents.PipelineSettingComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            buttonBaseColor: "#f05650"
            buttonCheckColor: "#8cf062"
            buttonHoverColor: colorLoader.shimarin_light
            buttonBorderWidth: 6
            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("원어 병기")
            number: "7"

            checked: pipelineSettingViewModel.dualLanguageActive 
            onClicked: pipelineSettingViewModel.toggle_dual_language()

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4
        }

        MyComponents.PipelineSettingComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            buttonBaseColor: "#f05650"
            buttonCheckColor: "#8cf062"
            buttonHoverColor: colorLoader.shimarin_light
            buttonBorderWidth: 6
            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("이미지 번역")
            number: "8"

            checked: pipelineSettingViewModel.imageTranslationActive
            onClicked: pipelineSettingViewModel.toggle_image_translation()

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4
        }
    }
}