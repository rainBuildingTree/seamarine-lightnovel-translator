pragma ComponentBehavior: Bound

import QtCore
import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Dialogs

import "../components" as MyComponents
import "../utils" as MyUtils

Page {
    id: root

    property font pageFont: Qt.font()
    property bool isTranslating: false
    property int workingProgress: 0
    property var owner

    onFocusChanged: homeViewModel.lazy_init()

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
        anchors.horizontalCenter: parent.horizontalCenter
        spacing: 4
        width: parent.width

        MyComponents.CircularIconButton {
            id: configureButton

            isButton: true
            iconSource: imageLoader.setting
            buttonColor: colorLoader.shimarin_dark
            borderColor: colorLoader.shimarin_dark
            borderWidth: 3
            hoverScale: 1.25

            Layout.preferredWidth: 50
            Layout.preferredHeight: 50
            Layout.alignment: Qt.AlignVCenter
            Layout.margins: 10
            
            onClicked: homeViewModel.open_setting()
        }

        Item {
            id: spacer4
            Layout.preferredHeight: 40
            Layout.fillWidth: true
        }

        MyComponents.CircularIconButton {
            id: translateButton

            iconSource: imageLoader.translate
            buttonColor: colorLoader.shimarin_light
            borderColor: colorLoader.shimarin_light
            borderWidth: 4

            arcColor: colorLoader.shimarin_light
            arcWidth: 6

            Layout.preferredWidth: 120
            Layout.preferredHeight: 120
            Layout.alignment: Qt.AlignHCenter

            arcActive: homeViewModel.translating

            onClicked: homeViewModel.start_translate()
        }

        Text {
            id: startTranslateText
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true

            text: (root.isTranslating === false) ? qsTr("번역 시작") : qsTr("번역 중지")
            font.family: root.pageFont.family
            font.pixelSize: 16
            color: colorLoader.shimarin_dark
            horizontalAlignment: Text.AlignHCenter
        }

        Item {
            id: spacer1
            Layout.preferredHeight: 10
            Layout.fillWidth: true
        }

        MyComponents.CircularIconButton {
            id: advancedModeButton

            iconSource: imageLoader.advanced
            borderColor: colorLoader.shimarin_light
            borderWidth: 3

            Layout.preferredWidth: 60
            Layout.preferredHeight: 60
            Layout.alignment: Qt.AlignHCenter

            onClicked: homeViewModel.open_advanced_mode()
        }

        Text {
            id: advancedModeText
            Layout.alignment: Qt.AlignHCenter
            Layout.fillWidth: true

            text: qsTr("고급 번역 모드")
            font.family: root.pageFont.family
            font.pixelSize: 16
            color: colorLoader.shimarin_dark
            horizontalAlignment: Text.AlignHCenter
        }

        Item {
            id: spacer2
            Layout.preferredHeight: 15
            Layout.fillWidth: true
        }

        TextField {
            id: selectedFileNameTextField
            Layout.preferredWidth: 300
            Layout.preferredHeight: 30
            Layout.alignment: Qt.AlignHCenter
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
                text: (homeViewModel.file.length === 0) ? qsTr("선택된 파일이 없습니다.") : homeViewModel.filename
                font.family: root.pageFont.family
                font.pixelSize: 12
                color: (homeViewModel.file.length === 0) ? "grey" : colorLoader.shimarin_dark
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

            onClicked: {
                homeViewModel.select_file()
            }
        }

        Item {
            id: spacer5
            Layout.preferredHeight: 110
            Layout.fillWidth: true
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

                        text: "%1%".arg(homeViewModel.progress)
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
                            width: parent.width * homeViewModel.progress / 100
                            clip: true

                            Rectangle {
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