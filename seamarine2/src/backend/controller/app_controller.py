from PySide6.QtCore import QObject, Signal, QTimer
from backend.core import *

class AppController(QObject):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self._app = app
        self.translate_core: TranslateCore = TranslateCore()
        QTimer.singleShot(500, self.navigateToStartPage.emit)

    ##### SIGNALS #####
    # Initial Setup & Home #
    navigateToEmptyPage = Signal()
    navigateToStartPage = Signal()
    navigateToGeminiApiPage = Signal()
    navigateToHomePage = Signal()
    # Home #
    navigateToAdvancedModePage = Signal()
    navigateToSettingPage = Signal()
    navigateToPnDictEditPage = Signal()
    # Setting #
    navigateToApiResetPage = Signal()
    navigateToPipelineSettingPage = Signal()
    navigateToAiSettingPage = Signal()
    navigateToAboutPage = Signal()
    # AI Setting #
    navigateToGeneralSettingPage = Signal()
    navigateToPnExtractSettingPage = Signal()
    navigateToTranslateSettingPage = Signal()
    navigateToTocTranslateSettingPage = Signal()
    navigateToReviewSettingPage = Signal()
    navigateToImageTranslateSettingPage = Signal()
    # Pop Page #
    popCurrentPage = Signal()
    popLeftCurrentPage = Signal()
    
    def exit_app(self):
        self._app.exit()
