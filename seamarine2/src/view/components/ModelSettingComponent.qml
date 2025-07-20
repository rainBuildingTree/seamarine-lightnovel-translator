import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

import "." as MyComponents

RowLayout {
    id: root
    required property font pageFont
    required property string text
    required property string placeholderText

    required property color textColor
    required property color buttonColor
    required property color borderColor
    required property var validator
    property string buttonText: qsTr("기본값")
    property int textFieldWidth: 70
    property string fieldText: ""

    signal clicked()
    signal textEdited()

    Item {
        id: leftPad
        Layout.preferredHeight: 1
        Layout.preferredWidth: 4
    }

    Text {
        id: text
        Layout.alignment: Qt.AlignLeft
        Layout.margins: 4

        text: root.text
        font.family: root.pageFont.family
        font.pixelSize: 16
        font.bold: true
        horizontalAlignment: Text.AlignHCenter
        color: root.textColor
        lineHeight: 1.1
    }

    Item {
        id: fill
        Layout.fillWidth: true
        Layout.preferredHeight: 1
    }

    TextField {
        id: textField
        Layout.preferredWidth: root.textFieldWidth
        Layout.preferredHeight: 32
        Layout.alignment: Qt.AlignHCenter

        font.pixelSize: 12
        leftPadding: 10
        rightPadding: 10
        placeholderText: root.placeholderText
        validator: root.validator
        text: root.fieldText

        background: Rectangle {
            id: geminiApiTextFieldBackground
            radius: 10
            color: "white"
            border.color: root.borderColor
            border.width: 2
        }

        onAcceptableInputChanged:
            color = acceptableInput ? "black" : "red";
        onTextEdited: {
            root.fieldText = textField.text
            textField.text = root.fieldText
            root.textEdited()
        }
    }

    MyComponents.CircularButton {
        id: button
        Layout.alignment: Qt.AlignVCenter
        Layout.preferredWidth: 60
        Layout.preferredHeight: 28
        radius: 15

        isButton: true
        buttonColor: root.buttonColor
        borderColor: root.borderColor
        borderWidth: 3
        hoverScale: 1.25

        text: root.buttonText
        textFont: root.pageFont
        textPixelSize: 12
        textColor: "white"
        textBold: true

        onClicked: {
            textField.editingFinished()
            textField.focus = false
            root.clicked()
            textField.text = root.fieldText
        }
    }

    Item {
        id: rightPad
        Layout.preferredHeight: 1
        Layout.preferredWidth: 4
    }
}