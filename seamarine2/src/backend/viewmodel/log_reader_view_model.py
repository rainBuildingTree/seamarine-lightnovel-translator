# LogReader.py (PySide6 버전)
import os
# ## 변경된 부분 ##: PyQt5 -> PySide6 임포트
from PySide6.QtCore import QObject, Signal, QTimer, Property, Slot, QUrl, QStandardPaths
from logger_config import setup_logger
from backend.model import RuntimeData, ConfigData
from utils.config import get_default_config

class LogReader(QObject):
    """
    주기적으로 로그 파일을 읽고, 새로운 내용이 추가될 때 QML로 신호를 보내는 클래스.
    """
    # ## 변경된 부분 ##: pyqtSignal -> Signal
    logContentChanged = Signal(str)
    logFilePathChanged = Signal()
    
    def __init__(self, config_data, runtime_data, parent=None):
        super().__init__(parent)
        self._logger = setup_logger()
        self._config_data: ConfigData = config_data
        self._runtime_data: RuntimeData = runtime_data
        self._log_length: int = len(self._runtime_data.translate_log)
        self._timer = QTimer(self)
        self._timer.setInterval(1000) # 1초마다 체크
        self._timer.timeout.connect(self._read_log_periodically)
        
        self._last_position = 0
        self._last_inode = None
        self._current_file_handle = None
    
    # ## 변경된 부분 ##: pyqtSlot -> Slot
    @Slot()
    def startReading(self):
        self._log_length = 0
        self._read_log_periodically()
        self._timer.start()
    @Slot()
    def stopReading(self):
        self._timer.stop()

    def reset_reader(self):
        """리더의 상태를 초기화합니다."""
        if self._current_file_handle:
            self._current_file_handle.close()
            self._current_file_handle = None
        self._last_position = 0
        self._last_inode = None
        self._logger.info(f"LogReader 상태 초기화: {self._log_file_path}")

# LogReader.py의 _read_log_periodically 메소드 수정 (inode 체크 제거 버전)

    def _read_log_periodically(self):
        try:
            new_log_length = len(self._runtime_data.translate_log)
            if new_log_length > self._log_length:
                for i in range(self._log_length, new_log_length):
                    self.logContentChanged.emit(self._runtime_data.translate_log[i])
                self._log_length = new_log_length
        except Exception as e:
            self._logger.error(str(self) + str(e))
