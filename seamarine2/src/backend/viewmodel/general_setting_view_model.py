from PySide6.QtCore import QObject, Slot, Signal, Property
from backend.controller.app_controller import AppController
from logger_config import setup_logger
from backend.model import ConfigData
from utils.config import get_default_config, save_config, load_config

class GeneralSettingViewModel(QObject):
    def __init__(self, config_data: ConfigData, runtime_data, app_controller, parent=None):
        super().__init__(parent)
        self.logger = setup_logger()
        try:
            self.config_data: ConfigData = config_data
            self.runtime_data = runtime_data
            self.app_controller: AppController = app_controller

            self.max_chunk_size = config_data.max_chunk_size
            self.max_concurrent_request = config_data.max_concurrent_request
            self.request_delay = config_data.request_delay
            self.is_save_succeed = False
            self.is_save_failed = False

            self.logger.info(str(self) + ".__init__")
        except Exception as e:
            self.logger.error(str(self) + str(e))
    
    maxChunkSizeChanged = Signal()
    @Property(int, notify=maxChunkSizeChanged)
    def maxChunkSize(self):
        return self.max_chunk_size
    
    maxConcurrentRequestChanged = Signal()
    @Property(int, notify=maxConcurrentRequestChanged)
    def maxConcurrentRequest(self):
        return self.max_concurrent_request
    
    requestDelayChanged = Signal()
    @Property(int, notify=requestDelayChanged)
    def requestDelay(self):
        return self.request_delay
    
    saveSucceedChanged = Signal()
    @Property(bool, notify=saveSucceedChanged)
    def saveSucceed(self):
        return self.is_save_succeed
    
    saveFailedChanged = Signal()
    @Property(bool, notify=saveFailedChanged)
    def saveFailed(self):
        return self.is_save_failed

    @Slot()
    def open_guide_link(self):
        pass
    @Slot(int, int, int)
    def save_data(self, chunk_size, conrequest, delay):
        try:
            if chunk_size < 1000 or chunk_size > 65536:
                raise Exception(f"Invalid max chunk size detected ({chunk_size})")
            if conrequest < 1 or conrequest > 99:
                raise Exception(f"Invalid max concurrent request detected ({conrequest})")
            if delay < 0 or delay > 99:
                raise Exception(f"Invalid request delay detected ({delay})")
            self.config_data.max_chunk_size = chunk_size
            self.config_data.max_concurrent_request = conrequest
            self.config_data.request_delay = delay
            self.max_chunk_size = chunk_size
            self.max_concurrent_request = conrequest
            self.request_delay = delay
            self.maxChunkSizeChanged.emit()
            self.maxConcurrentRequestChanged.emit()
            self.requestDelayChanged.emit()
            save_config(self.config_data.to_dict())
            self.is_save_succeed = True
            self.is_save_failed = False
            self.saveSucceedChanged.emit()
            self.saveFailedChanged.emit()
            self.logger.info(str(self) + f".save_data({chunk_size}, {conrequest}, {delay})")
        except Exception as e:
            self.is_save_succeed = False
            self.is_save_failed = True
            self.saveSucceedChanged.emit()
            self.saveFailedChanged.emit()
            self.logger.error(str(self) + str(e))
    @Slot()
    def close(self):
        try:
            self.max_chunk_size = self.config_data.max_chunk_size
            self.max_concurrent_request = self.config_data.max_concurrent_request
            self.request_delay = self.config_data.request_delay
            self.is_save_succeed = False
            self.is_save_failed = False
            self.maxChunkSizeChanged.emit()
            self.maxConcurrentRequestChanged.emit()
            self.requestDelayChanged.emit()
            self.app_controller.popCurrentPage.emit()
            self.saveSucceedChanged.emit()
            self.saveFailedChanged.emit()
            self.logger.info(str(self) + ".close")
        except Exception as e:
            self.logger.error(str(self) + str(e))      

    @Slot(str)
    def set_default(self, property: str):
        try:
            if 'chunk' in property:
                self.max_chunk_size = get_default_config().get('max_chunk_size')
                self.maxChunkSizeChanged.emit()
            elif 'con' in property:
                self.max_concurrent_request = get_default_config().get('max_concurrent_request')
                self.maxConcurrentRequestChanged.emit()
            elif 'delay' in property:
                self.request_delay = get_default_config().get('request_delay')
                self.requestDelayChanged.emit()
            else:
                raise Exception(f"Undefined behavior of defaulting property ({property})")
            self.logger.info(str(self) + f".set_default({property})")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    @Slot()
    def reset_config(self):
        self.config_data.load(get_default_config())
        save_config(self.config_data.to_dict())
        self.app_controller.exit_app()
