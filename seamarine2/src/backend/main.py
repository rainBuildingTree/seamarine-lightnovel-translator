from utils.config import load_config
from PySide6.QtCore import QObject, Property, Signal, Slot, QTimer
from PySide6.QtQml import QQmlApplicationEngine
from google import genai
import os
from .controller.app_controller import AppController
from .model import *
from .viewmodel import *


class MainController(QObject):
    fileNameToTranslateChanged = Signal()
    isApiKeyInvalidChanged = Signal()
    geminiApiKeyChanged = Signal()
    geminiModelListChanged = Signal()

    advancedModeModelIndexChanged = Signal()
    properNounExtractModelIndexChanged = Signal()
    translateModelIndexChanged = Signal()
    tocTranslateModelIndexChanged = Signal()
    reviewModelIndexChanged = Signal()
    imageTranslateModelIndexChanged = Signal()


    def __init__(self, app_controller, parent=None):
        super().__init__(parent)

        '''
        self.config_data = ConfigData()
        self.config_data.load(load_config())
        self.runtime_data = RuntimeData()

        self.engine = engine
        self.app_controller = AppController()
        self.start_view_model = StartViewModel(self.config_data, self.runtime_data, self.app_controller)
        self.gemini_api_view_model = GeminiApiViewModel(self.config_data, self.runtime_data, self.app_controller)
        #self.home_view_model = None
        self.setting_view_model = SettingViewModel(self.config_data, self.runtime_data, self.app_controller)
        self.gemini_api_reset_view_model = GeminiApiResetViewModel(self.config_data, self.runtime_data, self.app_controller)
        self.pipeline_setting_view_model = PipelineSettingViewModel(self.config_data, self.runtime_data, self.app_controller)

        self.engine.rootContext().setContextProperty('AppController', self.app_controller)
        self.engine.rootContext().setContextProperty('startViewModel', self.start_view_model)
        self.engine.rootContext().setContextProperty('geminiApiViewModel', self.gemini_api_view_model)
        #self.engine.rootContext().setContextProperty('homeViewModel', self.home_view_model)
        self.engine.rootContext().setContextProperty('settingViewModel', self.setting_view_model)
        self.engine.rootContext().setContextProperty('geminiApiResetViewModel', self.gemini_api_reset_view_model)
        self.engine.rootContext().setContextProperty('pipelineSettingViewModel', self.pipeline_setting_view_model)
'''
        self.app_controller = app_controller
        self.load_time_ms = 500
        self.file_path_to_translate = ""
        self.file_name_to_translate= ""
        self.is_api_key_invalid = False
        self.gemini_client = genai.Client(api_key="AIzaSyC8i9SL_YOhUpQyFJvfNNlo6cg49opf-MU")
        self.gemini_model_list = []

        self.advanced_mode_model_index = 1
        self.proper_noun_extract_model_index = 1
        self.translate_model_index = 1
        self.toc_translate_model_index = 1
        self.image_translate_model_index = 1
        QTimer.singleShot(self.load_time_ms, self._load_application)
    

    
    @Property(str, notify=fileNameToTranslateChanged)
    def fileNameToTranslate(self):
        return self.file_name_to_translate
    
    @Property(str, notify=geminiApiKeyChanged)
    def geminiApiKey(self):
        key = self.config_data.gemini_api_key
        if key == '':
            return "No Key Found"
        else:
            return key
    
    @Property(list, notify=geminiModelListChanged)
    def geminiModelList(self):
        return self.gemini_model_list
    @Property(int, notify=advancedModeModelIndexChanged)
    def advancedModeModelIndex(self):
        return self.advanced_mode_model_index
    @Property(int, notify=properNounExtractModelIndexChanged)
    def properNounExtractModelIndex(self):
        return self.proper_noun_extract_model_index
    @Property(int, notify=translateModelIndexChanged)
    def translateModelIndex(self):
        return self.translate_model_index
    @Property(int, tocTranslateModelIndexChanged)
    def tocTranslateModelIndex(self):
        return self.toc_translate_model_index
    @Property(int, imageTranslateModelIndexChanged)
    def imageTranslateModelIndex(self):
        return self.image_translate_model_index

    @Slot()
    def _load_application(self):
        self.app_controller.navigateToStartPage.emit()
    
    @Slot()
    def open_pipeline_guide(self):
        pass
    @Slot()
    def open_model_select_guide():
        pass
    
    @Slot()
    def open_advanced_mode_page(self):
        self.app_controller.navigateToAdvancedModePage.emit()

    @Slot()
    def open_setting_page(self):
        self.app_controller.navigateToSettingPage.emit()
    
    @Slot()
    def close_current_page(self):
        self.app_controller.popCurrentPage.emit()

    @Slot(str)
    def update_file_path_to_translate(self, path: str):
        self.file_path_to_translate = path
        self.file_name_to_translate = os.path.basename(self.file_path_to_translate)
        self.fileNameToTranslateChanged.emit()
    
    @Slot()
    def open_api_reset(self):
        self.app_controller.navigateToApiResetPage.emit()
    
    @Slot()
    def open_pipeline_setting(self):
        self.app_controller.navigateToPipelineSettingPage.emit()
    @Slot(str, str)
    def open_model_select_page(self, modelFor, processNumber):
        self.app_controller.navigateToModelSelectPage.emit(modelFor, int(processNumber))
    @Slot()
    def open_ai_setting(self):
        self.app_controller.navigateToAiSettingPage.emit()
    @Slot()
    def open_pn_extract_setting(self):
        self.app_controller.navigateToPnExtractSettingPage.emit()
    @Slot()
    def open_translate_setting(self):
        self.app_controller.navigateToTranslateSettingPage.emit()
    @Slot()
    def open_toc_translate_setting(self):
        self.app_controller.navigateToTocTranslateSettingPage.emit()
    @Slot()
    def open_review_setting(self):
        self.app_controller.navigateToReviewSettingPage.emit()
    @Slot()
    def open_image_translate_setting(self):
        self.app_controller.navigateToImageTranslateSettingPage.emit()
    @Slot()
    def open_general_setting(self):
        self.app_controller.navigateToGeneralSettingPage.emit()
    @Slot()
    def open_about_page(self):
        self.app_controller.navigateToAboutPage.emit()
    @Slot()
    def open_pn_dict(self):
        self.app_controller.navigateToPnDictEditPage.emit()

    @Slot(int)
    def advanced_mode_model_index_update(self, index: int):
        self.advanced_mode_model_index = index
        self.advancedModeModelIndexChanged.emit()

