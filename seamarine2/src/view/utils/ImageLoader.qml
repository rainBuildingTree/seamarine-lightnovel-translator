import QtQuick

QtObject {
    id: root
    
    readonly property string imageResources: "../../resources/images/"

    readonly property string translate: root.imageResources + "Translate.png"
    readonly property string setting: root.imageResources + "Setting.png"
    readonly property string gemini: root.imageResources + "Gemini.png"
    readonly property string advanced: root.imageResources + "Advanced.png"
    readonly property string about: root.imageResources + "About.png"
    readonly property string program: root.imageResources + "ProgramIcon.png"
    readonly property string pipeline: root.imageResources + "Pipeline.png"
    readonly property string aiapi: root.imageResources + "AIAPI.png"
    readonly property string info: root.imageResources + "Information.png"
}