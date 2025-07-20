from PySide6.QtCore import Signal, QThread
from backend.core import TranslateCore
import logging
from backend.model import AiModelConfig, LineData, save_line_data_to_csv, load_line_data_from_csv
import utils
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import html
import time
import os
import ast
from enum import Enum

class LanguageMerger(QThread):
    progress = Signal(int)
    completed = Signal(str)

    def __init__(
            self,
            core: TranslateCore,
            model_data: AiModelConfig,
            proper_noun: dict[str, str],
            file_path: str,
            save_directory: str,
            max_chunk_size: int,
            max_concurrent_request: int,
            request_delay: int
            ):
        super().__init__()
        self._logger = logging.getLogger("seamarine_translate")
        self._core = core
        self._model_data = model_data
        self._proper_noun = proper_noun
        self._file_path = file_path
        self._save_directory = save_directory
        self._max_chunk_size = max_chunk_size
        self._max_concurrent_request = max_concurrent_request
        self._request_delay = request_delay
        self._logger.info("[LanguageMerger.init]: Thread Initialized")
        
        
    def run(self):
        self.progress.emit(0)
        try:
            self._execute()
            self.progress.emit(100)
            self._logger.info("[LanguageMerger.run]: Task Completed")
        except Exception:
            self._logger.exception("[LanguageMerger.run]: Task Failed")
            self.progress.emit(0)

    def _execute(self):
        ## Load Epub ##
        try:
            book = utils.Epub(self._file_path)
            book.update_metadata_epub()
            chapter_files = book.get_chapter_files()
            self._logger.info(f"[LanguageMerger._execute]: {self._file_path} Loaded")
        except Exception:
            self._logger.exception(f"[LanguageMerger._execute]: Failed To Load {self._file_path}")
            raise

        book.apply_dual_language()

        ## Save Translated Epub ##
        save_path = self._file_path
        book.save(save_path)
        self.completed.emit(save_path)
        
    
    def _apply_repeat_tags(self, text: str, min_repeat: int = 4, max_unit_len: int = 10) -> str:
        """
        주어진 텍스트에서 반복되는 문자열을 <repeat time="N">...<repeat> 형태로 감싸서 반환
        """
        i = 0
        result = ""
        text_len = len(text)

        while i < text_len:
            replaced = False
            for unit_len in range(max_unit_len, 0, -1):
                unit = text[i:i + unit_len]
                if not unit or i + unit_len > text_len:
                    continue

                repeat_count = 1
                while text[i + repeat_count * unit_len: i + (repeat_count + 1) * unit_len] == unit:
                    repeat_count += 1

                if repeat_count >= min_repeat:
                    result += f'<repeat time="{repeat_count}">{unit}</repeat>'
                    i += unit_len * repeat_count
                    replaced = True
                    break

            if not replaced:
                result += text[i]
                i += 1

        return result
    
    def _restore_repeat_tags(self, html_content: str) -> str:
        """
        HTML 내 이스케이프된 <repeat time="N">...</repeat> 태그를 실제 반복 문자열로 복원
        """
        unescaped_html = html.unescape(html_content)
        
        pattern = re.compile(r'<repeat\s+time="(\d+)">(.*?)</repeat>', re.DOTALL)
        
        while True:
            match = pattern.search(unescaped_html)
            if not match:
                break
            
            count = int(match.group(1))
            content = match.group(2)
            repeated_content = content * count
            
            unescaped_html = unescaped_html[:match.start()] + repeated_content + unescaped_html[match.end():]
        
        return unescaped_html