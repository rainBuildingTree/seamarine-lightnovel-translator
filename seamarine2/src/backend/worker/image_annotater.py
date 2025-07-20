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
import posixpath
from enum import Enum
import io
from PIL import Image

class ImageAnnotater(QThread):
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
        self._logger.info("[ImageAnnotater.init]: Thread Initialized")

    def run(self):
        self.progress.emit(0)
        try:
            self._execute()
            self.progress.emit(100)
            self._logger.info("[ImageAnnotater.run]: Task Completed")
        except Exception:
            self._logger.exception("[ImageAnnotater.run]: Task Failed")
            self.progress.emit(0)

    def _execute(self):
        ## Load Epub ##
        try:
            book = utils.Epub(self._file_path)
            book.update_metadata_epub()
            chapter_files = book.get_chapter_files()
            self._logger.info(f"[ImageAnnotater._execute]: {self._file_path} Loaded")
        except Exception:
            self._logger.exception(f"[ImageAnnotater._execute]: Failed To Load {self._file_path}")
            raise

        self._core.update_model_data(self._model_data)
        self._core.language_from = book.get_language()
        self._logger.info(f"[MainTranslator._execute]: TranslateCore Setup Completed")

        for idx, chap in enumerate(chapter_files):
            try:
                html_content = book._contents[chap].decode('utf-8')
                soup = BeautifulSoup(html_content, 'lxml-xml')
                # <img> 태그와 <svg> 내의 image 태그 모두 검색
                all_images = soup.find_all('img') + soup.select('svg image')
                print(chap)
                print(all_images)
                continue
                for img in all_images:
                    src = (img.get("src") or img.get("xlink:href") or img.get("href") or
                           img.get("{http://www.w3.org/1999/xlink}href"))
                    if not src:
                        self._logger.warning(f"No valid image path in tag in {chap}")
                        continue
                    chapter_dir = posixpath.dirname(chap)
                    image_path = posixpath.normpath(posixpath.join(chapter_dir, src) if chapter_dir else src)
                    self._logger.info(f"Resolving image path: {image_path}")
                    if image_path in book._contents:
                        image_bytes = book._contents[image_path]
                        annotation = self._core.generate_content(Image.open(io.BytesIO(image_bytes)))
                        new_p = soup.new_tag("p")
                        new_p.append('[[이미지 텍스트:')
                        for line in annotation.strip().split('\n'):
                            new_p.append(soup.new_tag("br"))
                            new_p.append(line)
                        new_p.append(']]')
                        img.insert_after(new_p)
                    else:
                        self._logger.warning(f"Image not found in EPUB: {image_path}")
                book._contents[chap] = soup.prettify(formatter="minimal").encode('utf-8')
                self.progress.emit(int((idx+1) / len(chapter_files) * 95))
            except Exception as e:
                self._logger.exception(f"Failed to process {chap}: {e}")


        ## Save Translated Epub ##
        save_path = self._file_path
        book.save(save_path)
        self.completed.emit(save_path)