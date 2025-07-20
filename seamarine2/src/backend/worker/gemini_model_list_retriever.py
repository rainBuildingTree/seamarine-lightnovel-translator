from PySide6.QtCore import Signal, QThread
import asyncio
from backend.core import TranslateCore

class GeminiModelListRetriever(QThread):
    retrieved = Signal(list)

    def __init__(self, core: TranslateCore, key: str):
        super().__init__()
        self._core = core
        self._key = key
        
    def run(self):
        asyncio.run(self._async_execute())

    async def _async_execute(self):
        self._core.register_key(self._key)
        model_list = self._core.get_model_list()
        self.retrieved.emit(model_list)
        self.finished.emit()
