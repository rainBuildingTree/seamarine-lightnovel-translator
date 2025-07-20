from PySide6.QtCore import QObject, Slot, Property, Signal
from logger_config import setup_logger
from backend.worker import GeminiModelListRetriever
from backend.controller.app_controller import AppController
from utils.config import save_config
import webbrowser
from backend.model import *

class GeminiApiViewModel(QObject):
    def __init__(self, config_data, runtime_data, app_controller, parent=None):
        super().__init__(parent)
        self.logger = setup_logger()
        try:
            self._config_data: ConfigData = config_data
            self._runtime_data: RuntimeData = runtime_data
            self._app_controller: AppController = app_controller

            self.is_checking: bool = False
            self.is_api_key_invalid: bool = False
            self.is_problem_occured: bool = False
            self._temp_api_key: str = ""
            self.logger.info(str(self) + ".__init__")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    isCheckingChanged = Signal()
    @Property(bool, notify=isCheckingChanged)
    def isChecking(self):
        return self.is_checking

    isApiKeyInvalidChanged = Signal()
    @Property(bool, notify=isApiKeyInvalidChanged)
    def isApiKeyInvalid(self):
        return self.is_api_key_invalid
    
    isProblemOccuredChanged = Signal()
    @Property(bool, notify=isApiKeyInvalidChanged)
    def isProblemOccured(self):
        return self.is_problem_occured
    
    @Slot(str)
    def run_next_button_action(self, api_key: str):
        try:
            self._temp_api_key = api_key
            self.model_list_retriever = GeminiModelListRetriever(self._app_controller.translate_core, api_key)
            self.model_list_retriever.retrieved.connect(self.process_check_result)
            self.model_list_retriever.finished.connect(self.model_list_retriever.quit)
            self.model_list_retriever.start()
            self.is_checking = True
            self.isCheckingChanged.emit()
            self.logger.info(str(self) + f".run_next_button_action({api_key})")
        except Exception as e:
            self.logger.error(str(self) + str(e))
    
    @Slot()
    def open_api_link(self):
        try:
            webbrowser.open("https://aistudio.google.com/apikey")
            self.logger.info(str(self) + ".open_api_link")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    @Slot()
    def open_api_guide(self):
        pass

    @Slot()
    def close(self):
        try:
            self._app_controller.popCurrentPage.emit()
            self.logger.info(str(self) + ".close")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    def process_check_result(self, result: list[str]):
        try:
            if len(result) > 0:
                self.logger.info(f"Sucessed to validate api key")
                self.is_api_key_invalid = False
                self.isApiKeyInvalidChanged.emit()
                self.is_problem_occured = False
                self.isProblemOccuredChanged.emit()
                self._config_data.gemini_api_key = self._temp_api_key
                self._temp_api_key = ""
                save_config(self._config_data.to_dict())
                self._runtime_data.gemini_model_list = result
                self._app_controller.popLeftCurrentPage.emit()
                self._app_controller.navigateToHomePage.emit()
            else:
                self.logger.info(f"Failed to validate api key by {str(result)}")
                self.is_problem_occured = False
                self.isProblemOccuredChanged.emit()
                self.is_api_key_invalid = True
                self.isApiKeyInvalidChanged.emit()
            self.is_checking = False
            self.isCheckingChanged.emit()
            self.logger.info(str(self) + f".process_check_result({result})")
        except Exception as e:
            self.logger.error(str(self) + str(e))

            