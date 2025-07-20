pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Window
import QtQuick.Controls
import QtQuick.Layouts
import QtQml

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

                onClicked: imageTranslateSettingViewModel.close()
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

                onClicked: imageTranslateSettingViewModel.open_guide_link()
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

                onClicked: imageTranslateSettingViewModel.save_data()
            }
        }

        Text {
            id: titleText
            Layout.alignment: Qt.AlignLeft
            Layout.fillWidth: true
            Layout.margins: 10

            text: qsTr("이미지 번역 설정")
            font.family: root.pageFont.family
            font.pixelSize: 26
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            color: colorLoader.shimarin_dark
            lineHeight: 1.1
        }

        RowLayout {
            Item {
                Layout.preferredHeight: 1
                Layout.preferredWidth: 4
            }

            Text {
                id: modelSelect
                Layout.alignment: Qt.AlignLeft
                Layout.margins: 4

                text: qsTr("모델")
                font.family: root.pageFont.family
                font.pixelSize: 16
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                color: colorLoader.shimarin_dark
                lineHeight: 1.1
            }

            ComboBox {
                id: myComboBox
                Layout.alignment: Qt.AlignVCenter
                Layout.leftMargin: 4
                Layout.rightMargin: 4
                font.family: root.pageFont.family
                font.pixelSize: 12
                currentIndex: imageTranslateSettingViewModel.llmModelIndex
                background: Rectangle {
                    implicitHeight: 28
                    implicitWidth: myComboBox.width
                    color: "white"
                    border.width: 2
                    border.color: colorLoader.shimarin_dark
                    radius: 10
                }

                Layout.fillWidth: true

                model: imageTranslateSettingViewModel.llmModelList

                onActivated: (index) => {
                    imageTranslateSettingViewModel.update_model(index)
                }
            }

            MyComponents.CircularButton {
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: 60
                Layout.preferredHeight: 28
                radius: 15

                isButton: true
                buttonColor: colorLoader.shimarin
                borderColor: colorLoader.shimarin_dark
                borderWidth: 3
                hoverScale: 1.25

                text: qsTr("기본값")
                textFont: root.pageFont
                textPixelSize: 12
                textColor: "white"
                textBold: true

                onClicked: {
                    imageTranslateSettingViewModel.set_default("name")
                }
            }

            Item {
                Layout.preferredHeight: 1
                Layout.preferredWidth: 4
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

        RowLayout {
            Item {
                Layout.preferredHeight: 1
                Layout.preferredWidth: 4
            }

            Text {
                Layout.alignment: Qt.AlignLeft
                Layout.margins: 4

                text: qsTr("시스템 프롬프트")
                font.family: root.pageFont.family
                font.pixelSize: 16
                font.bold: true
                horizontalAlignment: Text.AlignVCenter
                color: colorLoader.shimarin_dark
                lineHeight: 1.1
            }

            Item {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
            }

            MyComponents.CircularButton {
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: 60
                Layout.preferredHeight: 28
                radius: 14

                isButton: true
                buttonColor: colorLoader.shimarin
                borderColor: colorLoader.shimarin_dark
                borderWidth: 3
                hoverScale: 1.25

                text: qsTr("기본값")
                textFont: root.pageFont
                textPixelSize: 12
                textColor: "white"
                textBold: true

                onClicked: imageTranslateSettingViewModel.set_default("sys prompt")
            }

            Item {
                Layout.preferredHeight: 1
                Layout.preferredWidth: 4
            }
        }

        ScrollView {
            Layout.preferredHeight: 150
            Layout.fillWidth: true
            Layout.leftMargin: 4
            Layout.rightMargin: 4
            Layout.alignment: Qt.AlignHCenter

            TextArea {
                id: systemInstruction

                wrapMode: TextArea.Wrap
                placeholderText: qsTr("여기에 시스템 프롬프트를 입력하세요")
                text: imageTranslateSettingViewModel.sysPrompt
                font.family: root.pageFont.family
                font.pixelSize: 12
                background: Rectangle { color: "white"; radius: 10; border.color: colorLoader.shimarin_dark; border.width: 2; }
                onTextEdited: imageTranslateSettingViewModel.sysPrompt = text
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
            id: tempSet
            pageFont: root.pageFont
            text: qsTr("Temperature")
            placeholderText: "0.0-2.0"
            textColor: colorLoader.shimarin_dark
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            validator: DoubleValidator {bottom: 0.0; top: 2.0}
            
            fieldText: imageTranslateSettingViewModel.temp
            onTextEdited: imageTranslateSettingViewModel.temp = fieldText
            onClicked: {
                imageTranslateSettingViewModel.set_default("temp")
                fieldText = imageTranslateSettingViewModel.temp
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
            id: topPSet
            pageFont: root.pageFont
            text: qsTr("Top P")
            placeholderText: "0.0-1.0"
            textColor: colorLoader.shimarin_dark
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            validator: DoubleValidator {bottom: 0.00; top: 1.00}

            fieldText: imageTranslateSettingViewModel.topP
            onTextEdited: imageTranslateSettingViewModel.topP = fieldText
            onClicked: {
                imageTranslateSettingViewModel.set_default("top p")
                fieldText = imageTranslateSettingViewModel.topP
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
            id: freqPenaltySet
            pageFont: root.pageFont
            text: qsTr("Frequency Penalty")
            placeholderText: "-2.0-2.0"
            textColor: colorLoader.shimarin_dark
            buttonColor: colorLoader.shimarin
            borderColor: colorLoader.shimarin_dark
            validator: DoubleValidator {bottom: -2.0; top: 2.0}

            fieldText: imageTranslateSettingViewModel.freqPenalty
            onTextEdited: imageTranslateSettingViewModel.freqPenalty = fieldText
            onClicked: {
                imageTranslateSettingViewModel.set_default("freq penalty")
                fieldText = imageTranslateSettingViewModel.freqPenalty
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

        RowLayout {
            id: thinkingBudgetSet

            Item {
                id: thinkingBudgetLeftPad
                Layout.preferredHeight: 1
                Layout.preferredWidth: 4
            }

            Text {
                id: thinkingBudgetText
                Layout.alignment: Qt.AlignLeft
                Layout.margins: 4

                text: qsTr("Thinking Budget")
                font.family: root.pageFont.family
                font.pixelSize: 16
                font.bold: true
                horizontalAlignment: Text.AlignHCenter
                color: colorLoader.shimarin_dark
                lineHeight: 1.1
            }

            Item {
                id: thinkingBudgetFill
                Layout.fillWidth: true
                Layout.preferredHeight: 1
            }

            MyComponents.CircularCheckbox {
                id: thinkingBudgetCheckbox
                isButton: true

                baseColor: colorLoader.shimarin_light
                checkColor: "#8cf062"
                borderColor: colorLoader.shimarin_dark
                borderWidth: 3

                Layout.preferredWidth: 28
                Layout.preferredHeight: 28
                Layout.alignment: Qt.AlignVCenter | Qt.AlignRight
                Layout.leftMargin: 0
                Layout.rightMargin: 6

                checked: imageTranslateSettingViewModel.useThinkingBudget
                onClicked: imageTranslateSettingViewModel.useThinkingBudget = !checked
            }

            TextField {
                id: thinkingBudgetField
                Layout.preferredWidth: 70
                Layout.preferredHeight: 32
                Layout.alignment: Qt.AlignHCenter
                font.pixelSize: 12
                leftPadding: 10
                rightPadding: 10
                placeholderText: "-1-24576"
                validator: IntValidator {bottom: -1; top: 24576}

                background: Rectangle {
                    radius: 10
                    color: "white"
                    border.color: colorLoader.shimarin_dark
                    border.width: 2
                }

                onAcceptableInputChanged:
                    color = acceptableInput ? "black" : "red";
                
                text: imageTranslateSettingViewModel.thinkingBudget
                onTextEdited: imageTranslateSettingViewModel.thinkingBudget = text
            }

            MyComponents.CircularButton {
                id: thinkingBudgetButton
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: 60
                Layout.preferredHeight: 28
                radius: 15

                isButton: true
                buttonColor: colorLoader.shimarin
                borderColor: colorLoader.shimarin_dark
                borderWidth: 3
                hoverScale: 1.25

                text: qsTr("기본값")
                textFont: root.pageFont
                textPixelSize: 12
                textColor: "white"
                textBold: true

                onClicked: {
                    imageTranslateSettingViewModel.set_default("use thinking budget")
                    imageTranslateSettingViewModel.set_default("thinking budget")
                    thinkingBudgetField.editingFinished()
                    thinkingBudgetField.focus = false
                    thinkingBudgetField.text = imageTranslateSettingViewModel.thinkingBudget
                }
            }

            Item {
                id: thinkingBudgetRightPad
                Layout.preferredHeight: 1
                Layout.preferredWidth: 4
            }
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
            id: saveMessage
            Layout.alignment: Qt.AlignHCenter
            Layout.margins: 4
            visible: imageTranslateSettingViewModel.saveFailed
            text: qsTr("저장 실패!")
            font.family: root.pageFont.family
            font.pixelSize: 14
            font.bold: true
            horizontalAlignment: Text.AlignHCenter
            color: colorLoader.warning
            lineHeight: 1.1
        }
        Text {
            id: saveSuceedMessage
            Layout.alignment: Qt.AlignHCenter
            Layout.margins: 4
            visible: imageTranslateSettingViewModel.saveSucceed
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