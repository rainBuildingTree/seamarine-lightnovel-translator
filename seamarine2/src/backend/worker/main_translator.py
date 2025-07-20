from PySide6.QtCore import Signal, QThread
from backend.core import TranslateCore
import logging
from backend.model import AiModelConfig, LineData, save_line_data_to_csv
import utils
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
import html
import time
import os
import json
import ast
from enum import Enum
import copy

class MainTranslator(QThread):
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
        self._logger.info("[MainTranslator.init]: Thread Initialized")
        
        
    def run(self):
        self.progress.emit(0)
        try:
            self._execute(1)
            time.sleep(10)
            self._execute(2)
            self.progress.emit(100)
            self._logger.info("[MainTranslator.run]: Task Completed")
        except Exception:
            self._logger.exception("[MainTranslator.run]: Task Failed")
            self.progress.emit(0)

    def _execute(self, attempt):
        ## Load Epub ##
        try:
            book = utils.Epub(self._file_path)
            book.update_metadata_epub(contributor="Kawaii Sea Marine" if attempt == 1 else None)
            book.update_read_direction()
            chapter_files = book.get_chapter_files()
            self._logger.info(f"[MainTranslator._execute]: {self._file_path} Loaded")
        except Exception:
            self._logger.exception(f"[MainTranslator._execute]: Failed To Load {self._file_path}")
            raise
        
        ## Set TranslateCore ##
        ai_model_data = copy.deepcopy(self._model_data)
        ai_model_data.system_prompt = \
"""
You are a highly precise translation API. Your SOLE function is to return a single, valid JSON object. Do not output any conversational text, notes, or explanations before or after the JSON. The entire response must be the JSON object itself.

The JSON object must map unique identifiers to their translated text.

**JSON Structure:**
{
  "unique_id_1": "translated text 1",
  "unique_id_2": "translated text 2"
}

**MANDATORY STRING FORMATTING RULES:**
To prevent errors, all string values inside the JSON MUST be correctly escaped.

1. Preserve every punctuation mark exactly as in the input (。,！、？：・…「」『』（） etc.)

1.  **Double Quotes (")**: Must be escaped with a backslash.
    - **BAD:** "She said "Hi!""
    - **GOOD:** "She said \\\"Hi!\\\""

1.  **Backslashes (\)**: Must be escaped with a backslash.
    - **BAD:** "Path: C:\\Temp\\file.txt"
    - **GOOD:** "Path: C:\\\\Temp\\\\file.txt"

1.  **Newlines**: Must be represented as the `\\n` character, not as a literal line break.
    - **BAD:** "Line 1
      Line 2"
    - **GOOD:** "Line 1\\nLine 2"

Before you finalize your response, double-check that the entire output is a single block of valid JSON code and that all string content adheres to these escaping rules.
""".strip() + \
"""

**Proper Noun Dictionary For Reference In Translation**
""" + str(self._proper_noun) + '\n\n' + ai_model_data.system_prompt
        self._core.update_model_data(ai_model_data)
        self._core.language_from = book.get_language()
        self._logger.info(f"[MainTranslator._execute]: TranslateCore Setup Completed")

        book.override_original_chapter()
        book.apply_pn_dictionary(self._proper_noun)

        ## Extract Texts ##
        chapter_files = book.get_chapter_files()
        xhtmls: dict[str, utils.TranslatableXHTML] = {}
        pre_file = ""
        for i, chapter_file in enumerate(chapter_files):
            if pre_file:
                xhtmls.update({chapter_file: utils.TranslatableXHTML(book._contents[chapter_file].decode(), xhtmls[pre_file].end_id+1)})
                pre_file = chapter_file
            else:
                xhtmls.update({chapter_file: utils.TranslatableXHTML(book._contents[chapter_file].decode())})
                pre_file = chapter_file
        text_dict_list = [xhtml.text_dict for xhtml in xhtmls.values()]
        text_dict = {k: self._apply_repeat_tags(v) for d in text_dict_list for k, v in d.items()}

        ## Save Extracted Texts ##
        working_dir_name, _ = os.path.splitext(os.path.basename(self._file_path))
        working_dir = os.path.join(self._save_directory, working_dir_name)
        original_dir = os.path.join(working_dir, "original")
        translated_dir = os.path.join(working_dir, "translated")
        os.makedirs(translated_dir, exist_ok=True)
        os.makedirs(original_dir, exist_ok=True)
        with open(os.path.join(original_dir, "text_dict.json"), "w") as f:
            json.dump(text_dict, f, ensure_ascii=False)
        self._logger.info(f"[MainTranslator._execute]: Saved Extraction")

        ## Load Prework ##
        if os.path.exists(os.path.join(translated_dir, "text_dict.json")):
            with open(os.path.join(translated_dir, "text_dict.json"), "r", encoding="utf-8") as f:
                translated_text_dict = json.load(f)
        else:
            translated_text_dict = {}
     
        ## Load Unfinished Work ##
        untranslated_text_dict = {k: v for k, v in text_dict.items() if k not in translated_text_dict.keys()}
        self._logger.info(f"Found {len(untranslated_text_dict)} Lines To Translate")

        ## Chunking ##
        text_dict_chunks = utils.chunk_text_dict(untranslated_text_dict, self._max_chunk_size)

        ## Chunk Translation (Thread Registration) ##
        translated_dir = os.path.join(working_dir, "translated")
        os.makedirs(translated_dir, exist_ok=True)
        with ThreadPoolExecutor(max_workers=self._max_concurrent_request) as executor:
            futures = [
                executor.submit(
                    self._translate_text_dict_chunk,
                    chunk,
                    chunk_index,
                ) for chunk_index, chunk in enumerate(text_dict_chunks)
            ]
        
            ## Chunk Translation (Update) ##
            completed = 0
            for future in as_completed(futures):
                success, chunk_index, translated_chunk = future.result()
                completed += 1
                translated_text_dict.update(translated_chunk)
                self._logger.info(f"Translation Of Chunk{chunk_index} Success: {success}")
                self.progress.emit(int(completed / len(text_dict_chunks) * 85) if attempt == 1 else 85 + int(completed / len(text_dict_chunks) * 10))
                translated_text_dict = dict(sorted(translated_text_dict.items()))
                ## Save Middle Translated Lines ##
                with open(os.path.join(translated_dir, "text_dict.json"), "w") as f:
                    json.dump(translated_text_dict, f)
        
        translated_text_dict = dict(sorted(translated_text_dict.items()))

        ## Save Final Translated Lines ##
        with open(os.path.join(translated_dir, "text_dict.json"), "w") as f:
            json.dump(translated_text_dict, f, ensure_ascii=False)
        
        ## Update Epub Contents ##
        for idx, chapter_file in enumerate(chapter_files):
            xhtmls[chapter_file].force_horizontal_writing()
            xhtmls[chapter_file].update_texts(translated_text_dict)
            dat = xhtmls[chapter_file].get_translated_html()
            dat = self._restore_repeat_tags(dat, True if idx == 8 else False)
            book._contents[chapter_file] = dat.encode('utf-8')

        ## Save Translated Epub ##
        save_path = self._file_path
        book.save(save_path)
        self.completed.emit(save_path)

    def _translate_text_dict_chunk(self, chunk: dict[int, str], chunk_index: int):
        is_suceed: bool = True
        translated_text_dict = {}
        llm_contents = json.dumps(chunk, ensure_ascii=False, indent=2)
        self._logger.info(f"Load Gemini Contents")

        for i in range(3):
            try:
                self._logger.info(f"Chunk{chunk_index} Translation (Try {i+1})")
                resp = self._core.generate_content(llm_contents)
                translated_text_dict: dict = json.loads(resp)
                if translated_text_dict.keys() != chunk.keys():
                    self._logger.info(f"Failed To Parse Translated Response Of Chunk{chunk_index} (Try {i+1})\n")
                    if i == 2:
                        self._logger.warning(f"Final Failiure In Chunk{chunk_index} Translation")
                        is_suceed = False
                    continue
                self._logger.info(f"Updated Chunks[{chunk_index}] Data")
                time.sleep(self._request_delay)
                return is_suceed, chunk_index, translated_text_dict

            except Exception as e:
                if resp:
                    self._logger.info(f"##### ORIGINAL #####\n\n{str(llm_contents)}\n\n##### RESPONSE #####\n\n{str(resp)}\n")
                self._logger.exception(str(e))
                if i < 2:
                    continue
                else:
                    return False, chunk_index, {}
        return False, chunk_index, {}
    
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
    
    def _restore_repeat_tags(self, html_content: str, debug = False) -> str:
        """
        HTML 내 이스케이프된 <repeat time="N">...</repeat> 태그를 실제 반복 문자열로 복원
        """
        unescaped_html = html_content
        if debug == True:
            print(html_content)
        pattern = re.compile(r'&lt;repeat\s+time="(\d+)"&gt;(.*?)&lt;/repeat&gt;', re.DOTALL)
        
        while True:
            match = pattern.search(unescaped_html)
            if not match:
                break
            
            count = int(match.group(1))
            content = match.group(2)
            repeated_content = content * count
            
            unescaped_html = unescaped_html[:match.start()] + repeated_content + unescaped_html[match.end():]
        
        return unescaped_html
    
    def _parse_retry_delay_from_error(self, error, extra_seconds=2) -> int:
        """
        주어진 에러 메시지에서 재시도 지연시간(초)을 추출합니다.
        에러 메시지에 "retry after <숫자>" 형태가 있다면 해당 숫자를 반환하고,
        그렇지 않으면 기본값 10초를 반환합니다.
        """
        error_str = str(error)
        start_idx = error_str.find('{')
        if start_idx == -1:
            return 0  # JSON 부분 없음
        
        dict_str = error_str[start_idx:]
        retry_seconds = 0

        try:
            # JSON이 아니라 Python dict처럼 생긴 문자열이므로 literal_eval 사용
            err_data = ast.literal_eval(dict_str)
            details = err_data.get("error", {}).get("details", [])
            for detail in details:
                if detail.get("@type") == "type.googleapis.com/google.rpc.RetryInfo":
                    retry_str = detail.get("retryDelay", "")  # 예: "39s"
                    match = re.match(r"(\d+)s", retry_str)
                    if match:
                        retry_seconds = int(match.group(1))
                        break
        except Exception as e:
            self._logger.warning(f"retryDelay 파싱 실패: {e}")
            return 10

        return retry_seconds + extra_seconds if retry_seconds > 0 else 0