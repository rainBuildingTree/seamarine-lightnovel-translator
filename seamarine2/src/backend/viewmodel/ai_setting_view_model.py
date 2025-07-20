from PySide6.QtCore import QObject, Slot
from backend.controller.app_controller import AppController
import logging

class AiSettingViewModel(QObject):
    def __init__(self, config_data, runtime_data, app_controller, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger("seamarine")
        try:
            self.config_data = config_data
            self.runtime_data = runtime_data
            self.app_controller: AppController = app_controller
            self.logger.info(str(self) + ".__init__")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    
    @Slot()
    def open_general_setting(self):
        try:
            self.app_controller.navigateToGeneralSettingPage.emit()
            self.logger.info(str(self) + ".open_general_setting")
        except Exception as e:
            self.logger.error(str(self) + str(e))
    @Slot()
    def open_pn_extract_setting(self):
        try:
            self.app_controller.navigateToPnExtractSettingPage.emit()
            self.logger.info(str(self) + ".open_pn_extract_setting")
        except Exception as e:
            self.logger.error(str(self) + str(e))
    @Slot()
    def open_translate_setting(self):
        try:
            self.app_controller.navigateToTranslateSettingPage.emit()
            self.logger.info(str(self) + ".open_translate_setting")
        except Exception as e:
            self.logger.error(str(self) + str(e))
    @Slot()
    def open_toc_translate_setting(self):
        try:
            self.app_controller.navigateToTocTranslateSettingPage.emit()
            self.logger.info(str(self) + ".open_toc_translate_setting")
        except Exception as e:
            self.logger.error(str(self) + str(e))
    @Slot()
    def open_review_setting(self):
        try:
            self.app_controller.navigateToReviewSettingPage.emit()
            self.logger.info(str(self) + ".open_review_setting")
        except Exception as e:
            self.logger.error(str(self) + str(e))
    @Slot()
    def open_image_translate_setting(self):
        try:
            self.app_controller.navigateToImageTranslateSettingPage.emit()
            self.logger.info(str(self) + ".open_image_translate_setting")
        except Exception as e:
            self.logger.error(str(self) + str(e))
    @Slot()
    def close(self):
        try:
            self.app_controller.popCurrentPage.emit()
            self.logger.info(str(self) + ".close")
        except Exception as e:
            self.logger.error(str(self) + str(e))