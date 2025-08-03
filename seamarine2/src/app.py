from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
import sys
from backend.controller.app_controller import AppController
from utils.config import load_config, CURRENT_VERSION
from logger_config import setup_logger, setup_translate_logger
from backend.model import *
from backend.viewmodel import *
from utils import paths

if __name__ == "__main__":
    app = QApplication(sys.argv)
    engine = QQmlApplicationEngine()
    logger = setup_logger()
    
    logger.info("Starting Application")

    _config_data = ConfigData()
    _runtime_data = RuntimeData()
    

    _config_data.load(load_config())
    logger.info(f"Version Detected: {_config_data.version}")
    if _config_data.version != CURRENT_VERSION:
        _config_data.load(load_config(reset=True))
    _runtime_data.save_directory = paths.get_save_directory()

    translate_logger = setup_translate_logger(_runtime_data.translate_log)

    _app_controller = AppController(app)

    _start_view_model = StartViewModel(_config_data, _runtime_data, _app_controller)
    _gemini_api_view_model = GeminiApiViewModel(_config_data, _runtime_data, _app_controller)
    _home_view_model = HomeViewModel(_config_data, _runtime_data, _app_controller)

    _setting_view_model = SettingViewModel(_config_data, _runtime_data, _app_controller)
    _advanced_mode_view_model = AdvancedModeViewModel(_config_data, _runtime_data, _app_controller)
    _pn_dict_edit_view_model = PnDictEditViewModel(_config_data, _runtime_data, _app_controller)

    _gemini_api_reset_view_model = GeminiApiResetViewModel(_config_data, _runtime_data, _app_controller)
    _user_dict_edit_view_model = UserDictEditViewModel(_config_data, _runtime_data, _app_controller)
    _pipeline_setting_view_model = PipelineSettingViewModel(_config_data, _runtime_data, _app_controller)
    _ai_setting_view_model = AiSettingViewModel(_config_data, _runtime_data, _app_controller)
    _about_view_model = AboutViewModel(_config_data, _runtime_data, _app_controller)
    
    _general_setting_view_model = GeneralSettingViewModel(_config_data, _runtime_data, _app_controller)
    _pn_extract_setting_view_model = PnExtractSettingViewModel(_config_data, _runtime_data, _app_controller)
    _translate_setting_view_model = TranslateSettingViewModel(_config_data, _runtime_data, _app_controller)
    _toc_translate_setting_view_model = TocTranslateSettingViewModel(_config_data, _runtime_data, _app_controller)
    _review_setting_view_model = ReviewSettingViewModel(_config_data, _runtime_data, _app_controller)
    _image_translate_setting_view_model = ImageTranslateSettingViewModel(_config_data, _runtime_data, _app_controller)

    _log_reader = LogReader(_config_data, _runtime_data)
    
    engine.rootContext().setContextProperty('appController', _app_controller)

    engine.rootContext().setContextProperty('startViewModel', _start_view_model)
    engine.rootContext().setContextProperty('geminiApiViewModel', _gemini_api_view_model)
    engine.rootContext().setContextProperty('homeViewModel', _home_view_model)

    engine.rootContext().setContextProperty('settingViewModel', _setting_view_model)
    engine.rootContext().setContextProperty('advancedModeViewModel', _advanced_mode_view_model)
    engine.rootContext().setContextProperty('pnDictEditViewModel', _pn_dict_edit_view_model)

    engine.rootContext().setContextProperty('geminiApiResetViewModel', _gemini_api_reset_view_model)
    engine.rootContext().setContextProperty('userDictEditViewModel', _user_dict_edit_view_model)
    engine.rootContext().setContextProperty('pipelineSettingViewModel', _pipeline_setting_view_model)
    engine.rootContext().setContextProperty('aiSettingViewModel', _ai_setting_view_model)
    engine.rootContext().setContextProperty('aboutViewModel', _about_view_model)

    engine.rootContext().setContextProperty('generalSettingViewModel', _general_setting_view_model)
    engine.rootContext().setContextProperty('pnExtractSettingViewModel', _pn_extract_setting_view_model)
    engine.rootContext().setContextProperty('translateSettingViewModel', _translate_setting_view_model)
    engine.rootContext().setContextProperty('tocTranslateSettingViewModel', _toc_translate_setting_view_model)
    engine.rootContext().setContextProperty('reviewSettingViewModel', _review_setting_view_model)
    engine.rootContext().setContextProperty('imageTranslateSettingViewModel', _image_translate_setting_view_model)

    engine.rootContext().setContextProperty('logReader', _log_reader)
    
    engine.load("./view/main.qml")
    
    if not engine.rootObjects():
        sys.exit(-1)


    sys.exit(app.exec())