from PySide6.QtCore import QObject, Slot, Signal, Property
from backend.worker import GeminiModelListRetriever
from logger_config import setup_logger
from backend.controller import AppController
from backend.model import ConfigData, RuntimeData

class StartViewModel(QObject):
    def __init__(self, config_data: ConfigData, runtime_data: RuntimeData, app_controller: AppController, parent=None):
        super().__init__(parent)
        self.logger = setup_logger()
        try:   
            self._app_controller: AppController = app_controller             
            self._config_data: ConfigData = config_data
            self._runtime_data: RuntimeData = runtime_data
            self.is_processing: bool = False
            self.logger.info(str(self) + ".__init__")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    isProcessingChanged = Signal()
    @Property(bool, notify=isProcessingChanged)
    def isProcessing(self):
        return self.is_processing
    
    @Slot()
    def run_next_button_action(self):
        if self.is_processing:
            return
        try:
            if self._config_data.gemini_api_key == '':
                self._app_controller.popLeftCurrentPage.emit()
                self._app_controller.navigateToGeminiApiPage.emit()
            else:
                self.is_processing = True
                self.isProcessingChanged.emit()
                self.gemini_model_list_retirever = GeminiModelListRetriever(self._app_controller.translate_core, self._config_data.gemini_api_key)
                self.gemini_model_list_retirever.retrieved.connect(self.update_model_list)
                self.gemini_model_list_retirever.finished.connect(self.move_next)
                self.gemini_model_list_retirever.finished.connect(self.gemini_model_list_retirever.quit)
                self.gemini_model_list_retirever.start()
            self.logger.info(str(self) + ".run_next_button_action")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    def update_model_list(self, model_list: list[str]):
        self._runtime_data.gemini_model_list = model_list

    def move_next(self):
        try:
            self.is_processing = False
            self.isProcessingChanged.emit()
            self._app_controller.popLeftCurrentPage.emit()
            self._app_controller.navigateToHomePage.emit()
            self.logger.info(str(self) + ".move_next")
        except Exception as e:
            self.logger.error(str(self) + str(e))