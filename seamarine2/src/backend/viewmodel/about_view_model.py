from PySide6.QtCore import QObject, Slot
from backend.controller.app_controller import AppController
from logger_config import setup_logger

class AboutViewModel(QObject):
    def __init__(self, config_data, runtime_data, app_controller, parent=None):
        super().__init__(parent)
        self.logger = setup_logger()
        try:
            self.config_data = config_data
            self.runtime_data = runtime_data
            self.app_controller: AppController = app_controller
            self.logger.info(str(self) + ".__init__")
        except Exception as e:
            self.logger.error(str(self) + str(e))
    
    @Slot()
    def open_guide_link(self):
        pass
    
    @Slot()
    def close(self):
        try:
            self.app_controller.popCurrentPage.emit()
            self.logger.info(str(self) + ".close")
        except Exception as e:
            self.logger.error(str(self) + str(e))            