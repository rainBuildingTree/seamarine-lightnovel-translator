from PySide6.QtCore import Signal, QThread
import logging
from backend.model import AiModelConfig
from collections import Counter
from backend.core import TranslateCore
from ebooklib import epub
import pycountry
from bs4 import BeautifulSoup
import json
import time
import re
import ast
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import csv
import copy

class PnExtractor(QThread):
    progress = Signal(int)

    def __init__(
            self, 
            core: TranslateCore, 
            model_data: AiModelConfig, 
            file_path: str, 
            save_path: str, 
            max_chunk_size: int, 
            max_concurrent_request: int, 
            request_delay: int
            ):
        super().__init__()
        self._logger = logging.getLogger("seamarine_translate")
        try:
            self._core: TranslateCore = core
            self._model_data: AiModelConfig = model_data
            self._file_path: str = file_path
            self._save_path: str = save_path
            self._max_chunk_size = max_chunk_size
            self._max_concurrent_request = max_concurrent_request
            self._request_delay = request_delay
            self._max_retries = 3
            self._proper_nouns = {}
            self._logger.info(str(self) + ".__init__")
        except Exception as e:
            self._logger.error(str(self) + ".__init__\n-> " + str(e))
        
    def run(self):
        self._logger.info(str(self) + ".run")
        try:
            self.progress.emit(0)
            self._execute()
        except Exception as e:
            self.progress.emit(0)
            self._logger.error(str(self) + ".run\n-> " + str(e))
        finally:
            self.progress.emit(100)

    def _execute(self):
        self._logger.info(str(self) + "._execute")
        try:
            self._core.update_model_data(self._model_data)
            self._core.language_from = self._get_language()
            full_text = self._extract_text()
                
            chunks = [full_text]
            chunk_count = len(chunks)
            completed = 0

            with ThreadPoolExecutor(max_workers=self._max_concurrent_request) as executor:
                futures = {
                    executor.submit(self._process_chunk, chunk): chunk
                    for chunk in chunks
                }
                for future in as_completed(futures):
                    result = future.result()
                    self._proper_nouns.update(result)
                    completed += 1
                    self.progress.emit(int(completed / chunk_count * 99))
            
            self._save_to_csv()
        except Exception as e:
            self._logger.error(str(self) + "._execute\n-> " + str(e))
            raise e

    def _get_language(self) -> str:
        self._logger.info(str(self) + "._get_language")
        try:
            book = epub.read_epub(self._file_path)
            lang_code = book.get_metadata('DC', 'language')[0][0]
            lang_code = lang_code.lower()
            self._logger.info(f"Detected Language: {lang_code}")
        
            lang = pycountry.languages.get(alpha_2=lang_code)
            if lang:
                return lang.name

            lang = pycountry.languages.get(alpha_3=lang_code)
            if lang:
                return lang.name

            for lang in pycountry.languages:
                if hasattr(lang, 'bibliographic') and lang.bibliographic == lang_code:
                    return lang.name
                if hasattr(lang, 'terminology') and lang.terminology == lang_code:
                    return lang.name
            
            raise Exception("Failed to extract text from epub")
        except Exception as e:
            self._logger.error(str(self) + "._get_language\n-> " + str(e))
            raise e

    
    def _extract_text(self) -> str:
        try:
            book = epub.read_epub(self._file_path)
            full_text = ""
            for item in book.get_items():
                if isinstance(item, epub.EpubHtml):
                    content = item.get_content().decode('utf-8')
                    soup = BeautifulSoup(content, 'lxml-xml')
                    full_text += soup.get_text() + '\n'
            self._logger.info(str(self) + f"._extract_text({self._file_path}) ->")
        except Exception as e:
            self._logger.error(str(self) + "._extract_text\n-> " + str(e))
            raise e
        
        return full_text
    
    def _split_text(self, text: str, max_length: int = 2000) -> list[str]:
        chunks = [text[i:((i+max_length) if i+max_length+10 > len(text) else i+max_length+10)] for i in range(0, len(text), max_length)]
        self._logger.info(str(self) + f"._split_text() -> " )
        return chunks
    
    def _clean_response(self, response_text: str) -> str:
        text = response_text.strip()
        if text.startswith("```json"):
            text = text[7:].strip()
        elif text.startswith("```"):
            text = text[3:].strip()
        elif text.startswith("json"):
            text = text[4:].strip()
        if text.endswith("```"):
            text = text[:-3].strip()
        self._logger.info(str(self) + f"._clean_response() ->")
        return text

    def _get_retry_delay_from_exception(self, error_str: str, extra_seconds: int = 2) -> int:
        start_idx = error_str.find('{')
        if start_idx == -1:
            return 0 
        
        dict_str = error_str[start_idx:]
        retry_seconds = 0

        try:
            err_data = ast.literal_eval(dict_str)
            details = err_data.get("error", {}).get("details", [])
            for detail in details:
                if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                    retry_str = detail.get("retryDelay", "")
                    match = re.match(r"(\d+)s", retry_str)
                    if match:
                        retry_seconds = int(match.group(1))
                        break
        except Exception as e:
            self._logger.warning(f"Failed to parse retryDelay: {e}")
            return 10

        return retry_seconds + extra_seconds if retry_seconds > 0 else 0
    
    def _process_chunk(self, chunk):
        for attempt in range(1, self._max_retries + 1):
            try:
                response = self._core.generate_content(chunk, True, True)
                if response:
                    cleaned = self._clean_response(response.strip())
                    self._logger.info(cleaned)
                    new_dict = json.loads(cleaned)
                else:
                    new_dict = {}

                time.sleep(self._request_delay)
                self._logger.info(str(self) + f"._process_chunk() -> ")
                return new_dict

            except Exception as e:
                if "429" in str(e) or "Resource exhausted" in str(e):
                    attempt -= 1
                    dynamic_delay = self._get_retry_delay_from_exception(str(e))
                    self._logger.info(str(self) + f".process_chunk\n-> 429/Resource Exhausted Detected. Retry after {dynamic_delay} seconds")
                    time.sleep(dynamic_delay)
                else:
                    self._logger.error(f"Attempt {attempt} - Failed to parse chunk: {e}")
                    time.sleep(5)

        self._logger.error("Final failure after MAX_RETRIES attempts. Returning empty dict.")
        return {}

    def _save_to_csv(self):
        try:
            save_dir = os.path.dirname(self._save_path)
            os.makedirs(save_dir, exist_ok=True)
            with open(self._save_path, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                for t_from, t_to in self._proper_nouns.items():
                    writer.writerow([t_from, t_to])
            self._logger.info(str(self) + "._save_to_csv")
        except Exception as e:
            self._logger.error(str(self) + "._save_to_csv\n->" + str(e))

    
