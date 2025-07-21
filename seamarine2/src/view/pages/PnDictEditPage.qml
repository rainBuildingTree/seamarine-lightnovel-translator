pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Fusion
import QtQuick.Layouts
import QtQml

import "../components" as MyComponents
import "../utils" as MyUtils

Page {
    id: root

    property font pageFont: Qt.font()

    MyUtils.ColorLoader { id: colorLoader }
    MyUtils.ImageLoader { id: imageLoader }

    background: Rectangle { color: colorLoader.background }

    Component.onCompleted: {
        pnDictEditViewModel.lazy_init()
        dictListView.model = []
        dictListView.model = pnDictEditViewModel.data
    }

    ColumnLayout {
        id: rootColumn
        anchors.fill: parent
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
                onClicked: pnDictEditViewModel.close()
            }
            Item { Layout.fillWidth: true; Layout.preferredHeight: 1 }
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
                onClicked: pnDictEditViewModel.save_csv()
            }
        }

        Text {
            id: titleText
            Layout.alignment: Qt.AlignLeft
            Layout.fillWidth: true
            Layout.margins: 10
            text: qsTr("고유명사 사전 수정")
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
            Layout.bottomMargin: 2
            border.width: 0
            color: colorLoader.shimarin
        }

        ListView {
            id: dictListView
            Layout.fillWidth: true
            Layout.fillHeight: true
            Layout.margins: 10
            Layout.bottomMargin: 2
            Layout.topMargin: 2
            model: pnDictEditViewModel.data
            clip: true
            spacing: 10

            delegate: Rectangle {
                id: listElement
                required property string from
                required property string to
                required property int index
                radius: 24
                border.width: 3
                border.color: colorLoader.shimarin_dark

                color: colorLoader.shimarin_light
                implicitHeight: 48
                implicitWidth: dictListView.width

                RowLayout {
                    anchors.left: parent.left
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    Item {
                        Layout.preferredHeight: 1
                        Layout.preferredWidth: 2
                    }
                    TextField { id: fromField
                        Layout.preferredWidth: 120
                        Layout.preferredHeight: 36
                        Layout.alignment: Qt.AlignVCenter
                        font.family: root.pageFont.family
                        font.pixelSize: 12
                        color: colorLoader.shimarin_dark
                        leftPadding: 10
                        rightPadding: 10
                        placeholderText: qsTr("원어")
                        text: listElement.from
                        background: Rectangle {
                            width: 120
                            height: 36
                            radius: 18
                            border.color: colorLoader.shimarin_dark
                            border.width: 3
                            color: "white"
                        }

                        onTextEdited: {
                            pnDictEditViewModel.update_data(listElement.index, "from", text)
                        }
                    }
                    Text {
                        Layout.preferredWidth: 30
                        Layout.preferredHeight: 36
                        Layout.alignment: Qt.AlignVCenter

                        verticalAlignment: Text.AlignVCenter
                        font.family: root.pageFont.family
                        font.bold: true
                        font.pixelSize: 32
                        color: colorLoader.shimarin_dark
                        text: "→"
                    }
                    TextField {
                        Layout.preferredWidth: 120
                        Layout.preferredHeight: 36
                        Layout.alignment: Qt.AlignVCenter
                        font.family: root.pageFont.family
                        font.pixelSize: 12
                        color: colorLoader.shimarin_dark
                        leftPadding: 10
                        rightPadding: 2
                        placeholderText: qsTr("번역")
                        text: listElement.to
                        background: Rectangle {
                            width: 120
                            height: 36
                            radius: 18
                            border.color: colorLoader.shimarin_dark
                            border.width: 3
                            color: "white"
                        }
                        onTextEdited: {
                            pnDictEditViewModel.update_data(listElement.index, "to", text)
                        }
                    }

                    MyComponents.CircularButton {
                        id: removeButton
                        Layout.alignment: Qt.AlignVCenter
                        Layout.preferredWidth: 40
                        Layout.preferredHeight: 40
                        Layout.leftMargin: 4
                        radius: 20

                        isButton: true
                        buttonColor: colorLoader.nadeshiko
                        borderColor: colorLoader.nadeshiko_dark
                        borderWidth: 3
                        hoverScale: 1.1

                        text: "x"
                        textFont: root.pageFont
                        textPixelSize: 24
                        textColor: colorLoader.nadeshiko_light
                        textBold: true

                        onClicked: {
                            pnDictEditViewModel.remove_row(listElement.index)
                            dictListView.model = []
                            dictListView.model = pnDictEditViewModel.data
                            dictListView.positionViewAtIndex(listElement.index - 1, ListView.Center)
                        }
                    }
                }
            }
        }

        MyComponents.CircularButton {
            id: addButton
            Layout.alignment: Qt.AlignVCenter
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.margins: 10
            Layout.topMargin: 2
            Layout.bottomMargin: 2
            radius: 24

            isButton: true
            buttonColor: colorLoader.shimarin_dark
            borderColor: colorLoader.shimarin_light
            borderWidth: 3
            hoverScale: 0.9

            text: "+"
            textFont: root.pageFont
            textPixelSize: 36
            textColor: colorLoader.white
            textBold: true

            onClicked: {
                pnDictEditViewModel.add_row()
                dictListView.model = []
                dictListView.model = pnDictEditViewModel.data
                dictListView.positionViewAtEnd()
            }
        }


    }
}
