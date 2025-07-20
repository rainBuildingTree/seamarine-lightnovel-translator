// LogWindow.qml
import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

ApplicationWindow {
    id: logWindow
    visible: true
    width: 800
    height: 600
    title: qsTr("SeaMarine 번역 로그")

    onVisibleChanged: visible === true ? logReader.startReading() : logReader.stopReading()

    ScrollView {
        anchors.fill: parent
        anchors.centerIn: parent
        TextArea {
            id: logTextArea
            readOnly: true
            wrapMode: Text.Wrap 

            Connections {
                target: logReader

                function onLogContentChanged(newContent) {
                    logTextArea.append(newContent)
                }
            }
        }
    }
}