pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Window
import "utils" as MyUtils

import "pages" as Pages

ApplicationWindow {
    id: root
    title: qsTr("SeaMarine AI 번역 도구")
    width: 360
    height: 640
    maximumHeight: height
    minimumHeight: height
    maximumWidth: width
    minimumWidth: width
    visible: true

    flags: Qt.WindowMinimizeButtonHint | Qt.WindowCloseButtonHint

    MyUtils.ImageLoader {
        id: imageLoader
    }
    MyUtils.ColorLoader {
        id: colorLoader
    }
    FontLoader {
        id: fontLoader
        source: "../resources/fonts/gyeonggi_body.ttf"
    }

    Connections {
        target: appController
        function onNavigateToEmptyPage() {
            rootStack.push('pages/EmptyPage.qml', { backgroundColor: colorLoader.background })
        }
        function onNavigateToStartPage() {
            rootStack.push('pages/StartPage.qml', { pageFont: fontLoader.font });
        }
        function onNavigateToGeminiApiPage() {
            rootStack.push('pages/GeminiApiPage.qml', { pageFont: fontLoader.font })
        }
        function onNavigateToHomePage() {
            rootStack.push('pages/HomePage.qml', { pageFont: fontLoader.font, owner: root})
        }

        function onNavigateToAdvancedModePage() {
            rootStack.push('pages/AdvancedModePage.qml', { pageFont: fontLoader.font })
        }
        function onNavigateToSettingPage() {
            rootStack.push('pages/SettingPage.qml', { pageFont: fontLoader.font })
        }
        function onNavigateToPnDictEditPage() {
            rootStack.push('pages/PnDictEditPage.qml', { pageFont: fontLoader.font })
        }

        function onNavigateToApiResetPage() {
            rootStack.push('pages/GeminiApiResetPage.qml', { pageFont: fontLoader.font })
        }
        function onNavigateToPipelineSettingPage() {
            rootStack.push('pages/PipelineSettingPage.qml', { pageFont: fontLoader.font })
        }
        function onNavigateToAiSettingPage() {
            rootStack.push('pages/AiSettingPage.qml', { pageFont: fontLoader.font })
        }
        function onNavigateToAboutPage() {
            rootStack.push('pages/AboutPage.qml', { pageFont: fontLoader.font })
        }

        function onNavigateToGeneralSettingPage() {
            rootStack.push('pages/GeneralSettingPage.qml', { pageFont: fontLoader.font })
        }
        function onNavigateToPnExtractSettingPage() {
            rootStack.push('pages/PnExtractSettingPage.qml', { pageFont: fontLoader.font })
        }
        function onNavigateToTranslateSettingPage() {
            rootStack.push('pages/TranslateSettingPage.qml', { pageFont: fontLoader.font })
        }
        function onNavigateToTocTranslateSettingPage() {
            rootStack.push('pages/TocTranslateSettingPage.qml', { pageFont: fontLoader.font })
        }
        function onNavigateToReviewSettingPage() {
            rootStack.push('pages/ReviewSettingPage.qml', { pageFont: fontLoader.font })
        }
        function onNavigateToImageTranslateSettingPage() {
            rootStack.push('pages/ImageTranslateSettingPage.qml', { pageFont: fontLoader.font })
        }
        function openLogViewer() {

        }

        function onPopCurrentPage() {
            rootStack.popCurrentItem(StackView.PopTransition)
        }
        function onPopLeftCurrentPage() {
            rootStack.popCurrentItem(StackView.PushTransition)
        }
    }


    StackView {
        id: rootStack
        objectName: "rootStackView"
        anchors.fill: parent
        initialItem: Component {
            Pages.EmptyPage {
                backgroundColor: colorLoader.background
            }
        }
    }
}
