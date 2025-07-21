pragma ComponentBehavior: Bound

import QtCore
import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Controls.Fusion
import QtQuick.Layouts
import QtQuick.Dialogs

import "../components" as MyComponents
import "../utils" as MyUtils

Page {
    id: root

    property font pageFont: Qt.font()
    property string selectedFilePath: ""
    property bool isWorking: false
    property int workingProgress: 0

    background: Rectangle {
        color: colorLoader.background
    }

    Behavior on workingProgress {
        NumberAnimation {
            duration: 100
        }
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

                onClicked: advancedModeViewModel.close()
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

                onClicked: advancedModeViewModel.open_guide_link()
            }
        }

        MyComponents.AdvancedModeComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("루비 제거")
            number: "1"

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4

            arcActive: advancedModeViewModel.rubyRemovalRunning
            arcColor: colorLoader.nadeshiko
            arcWidth: 3

            onClicked: advancedModeViewModel.run_ruby_removal()
        }

        MyComponents.AdvancedModeComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("고유명사 추출")
            number: "2"

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4

            arcActive: advancedModeViewModel.pnExtractRunning
            arcColor: colorLoader.nadeshiko
            arcWidth: 3

            onClicked: advancedModeViewModel.run_pn_extract()
        }

        MyComponents.AdvancedModeComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("고유명사 사전 수정")
            number: "3"

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4

            onClicked: advancedModeViewModel.run_pn_dict_edit()
        }

        MyComponents.AdvancedModeComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("전체 번역")
            number: "4"

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4

            arcActive: advancedModeViewModel.mainTranslateRunning
            arcColor: colorLoader.nadeshiko
            arcWidth: 3

            onClicked: advancedModeViewModel.run_main_translate()
        }

        MyComponents.AdvancedModeComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("제목/목차 번역")
            number: "5"

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4

            arcActive: advancedModeViewModel.tocTranslateRunning
            arcColor: colorLoader.nadeshiko
            arcWidth: 3

            onClicked: advancedModeViewModel.run_toc_translate()
        }

        MyComponents.AdvancedModeComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("검수 번역 진행")
            number: "6"

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4

            arcActive: advancedModeViewModel.reviewRunning
            arcColor: colorLoader.nadeshiko
            arcWidth: 3

            onClicked: advancedModeViewModel.run_review()
        }

        MyComponents.AdvancedModeComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("원어 병기")
            number: "7"

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4

            arcActive: advancedModeViewModel.dualLanguageRunning
            arcColor: colorLoader.nadeshiko
            arcWidth: 3

            onClicked: advancedModeViewModel.run_dual_language()
        }

        MyComponents.AdvancedModeComponent {
            backgroundColor: colorLoader.shimarin_light
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            pageFont: root.pageFont
            text: qsTr("이미지 번역")
            number: "8"

            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.alignment: Qt.AlignHCenter
            Layout.leftMargin: 4
            Layout.rightMargin: 4

            arcActive: advancedModeViewModel.imageTranslateRunning
            arcColor: colorLoader.nadeshiko
            arcWidth: 3

            onClicked: advancedModeViewModel.run_image_translate()
        }

        TextField {
            id: selectedFileNameTextField
            Layout.preferredWidth: 300
            Layout.preferredHeight: 30
            Layout.alignment: Qt.AlignHCenter
            Layout.topMargin: 5
            font.pixelSize: 12
            leftPadding: 10
            rightPadding: 10
            verticalAlignment: Text.AlignVCenter
            horizontalAlignment: Text.AlignHCenter

            readOnly: true

            background: Rectangle {
                id: selectedFileNameTextFieldBackground
                width: 300
                height: 30
                radius: 15
                color: "white"
                border.color: colorLoader.shimarin_dark
                border.width: 3
            }

            Text {
                id: customPlaceholder
                anchors.fill: parent
                verticalAlignment: Text.AlignVCenter
                horizontalAlignment: Text.AlignHCenter
                text: (advancedModeViewModel.file.length === 0) ? qsTr("선택된 파일이 없습니다.") : advancedModeViewModel.filename
                font.family: root.pageFont.family
                font.pixelSize: 12
                color: (advancedModeViewModel.file.length === 0) ? "grey" : colorLoader.shimarin_dark
                elide: ElideMiddle

                visible: selectedFileNameTextField.text.length === 0
            }
        }

        MyComponents.CircularButton {
            id: selectFileButton

            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            borderWidth: 3
            hoverScale: 1.25

            textFont: root.pageFont
            text: qsTr("파일 선택")
            textPixelSize: 12
            textColor: "white"
            textBold: true

            Layout.preferredWidth: 60
            Layout.preferredHeight: 30
            Layout.alignment: Qt.AlignHCenter

            onClicked: advancedModeViewModel.select_file()
        }

        Rectangle {
            id: progressBox
            Layout.fillWidth: true
            Layout.preferredHeight: 80
            Layout.alignment: Qt.AlignBottom
            color: colorLoader.shimarin_dark

            ColumnLayout {
                anchors.fill: parent

                Text {
                    Layout.alignment: Qt.AlignTop | Qt.AlignHCenter
                    Layout.preferredWidth: 32
                    Layout.preferredHeight: 32
                    verticalAlignment: Text.AlignVCenter
                    horizontalAlignment: Text.AlignHCenter
                    text: qsTr("진행도")
                    font.family: root.pageFont.family
                    font.pixelSize: 16
                    font.bold: true
                    color: colorLoader.white
                }

                RowLayout {
                    id: progressLayout

                    Layout.alignment: Qt.AlignBottom | Qt.AlignHCenter
                    Layout.bottomMargin: 10
                    spacing: 6

                    MyComponents.CircularButton {
                        id: progressTextBox

                        isButton: false
                        buttonColor: colorLoader.shimarin_light
                        borderColor: colorLoader.shimarin
                        borderWidth: 3

                        text: "%1%".arg(advancedModeViewModel.progress)
                        textFont: root.pageFont
                        textPixelSize: 14
                        textColor: "white"
                        textBold: true

                        Layout.preferredWidth: 48
                        Layout.preferredHeight: 32
                        Layout.alignment: Qt.AlignLeft | Qt.AlignVCenter
                    }

                    Rectangle {
                        id: progressBarBox
                        property int percentage: 48
                        Layout.preferredWidth: 236
                        Layout.preferredHeight: 32
                        Layout.alignment: Qt.AlignCenter
                        radius: height / 2
                        color: colorLoader.shimarin
                        border.color: colorLoader.shimarin_light
                        border.width: 3

                        Item {
                            id: progressRect
                            anchors.bottom: parent.bottom
                            anchors.top: parent.top
                            anchors.left: parent.left
                            width: parent.width * advancedModeViewModel.progress / 100
                            clip: true

                            Rectangle { id: rectbox
                                width: progressBarBox.width                  
                                height: progressBarBox.height 
                                radius: height / 2
                                anchors.bottom: parent.bottom
                                anchors.left: parent.left
                                color: colorLoader.shimarin_light
                            }
                            Behavior on width {
                                NumberAnimation {
                                    duration: 100
                                    easing.type: Easing.InOutQuad
                                }
                            }
                        }
                    }

                    MyComponents.CircularButton {
                        id: progressDetailButton

                        buttonColor: colorLoader.shimarin_light
                        borderColor: colorLoader.shimarin
                        borderWidth: 3
                        hoverScale: 1.25

                        textFont: root.pageFont
                        text: qsTr("로그")
                        textPixelSize: 14
                        textColor: "white"
                        textBold: true

                        Layout.preferredWidth: 48
                        Layout.preferredHeight: 32
                        Layout.alignment: Qt.AlignLeft | Qt.AlignVCenter

                        onClicked: {
                            var component = Qt.createComponent("../logWindow.qml")
                            var window = component.createObject(parent)
                            window.show()
                        }
                    }
                }
            }
        }
    }
}