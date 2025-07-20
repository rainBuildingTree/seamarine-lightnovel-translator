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
import copy
import json
from enum import Enum

class Reviewer(QThread):
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
        self._logger.info("[Reviewer.init]: Thread Initialized")
        
        
    def run(self):
        self.progress.emit(0)
        try:
            self._execute()
            self.progress.emit(100)
            self._logger.info("[Reviewer.run]: Task Completed")
        except Exception:
            self._logger.exception("[Reviewer.run]: Task Failed")
            self.progress.emit(0)

    def _execute(self):
        ## Load Epub ##
        try:
            book = utils.Epub(self._file_path)
            book.update_metadata_epub()
            chapter_files = book.get_chapter_files()
            self._logger.info(f"[Reviewer._execute]: {self._file_path} Loaded")
        except Exception:
            self._logger.exception(f"[Reviewer._execute]: Failed To Load {self._file_path}")
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
""".strip() + "\n\n" + ai_model_data.system_prompt
        self._core.update_model_data(ai_model_data)
        self._core.language_from = book.get_original_language()
        self._logger.info(f"[Reviewer._execute]: TranslateCore Setup Completed")

        for trial in range(1, 6):
            book.override_original_chapter()
            book.apply_pn_dictionary(self._proper_noun)
            self._logger.info(f"[Reviewer._execute]: Review Try {trial}")

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

            ## Retrieve Translated Text Data ##
            working_dir_name, _ = os.path.splitext(os.path.basename(self._file_path))
            working_dir = os.path.join(self._save_directory, working_dir_name)
            original_dir = os.path.join(working_dir, "original")
            translated_dir = os.path.join(working_dir, "translated")
            if os.path.exists(os.path.join(translated_dir, "text_dict.json")):
                with open(os.path.join(translated_dir, "text_dict.json"), "r", encoding="utf-8") as f:
                    translated_text_dict: dict = json.load(f)
            else:
                raise RuntimeError("No translated text dict found")

            untranslated_text_dict = { k: text_dict[k] for k, v in translated_text_dict.items() if utils.contains_foreign(v) }
            self._logger.info(f"{len(untranslated_text_dict)} untranslated text lines found")

            ## Chunking ##
            text_dict_chunks = utils.chunk_text_dict(untranslated_text_dict, int(self._max_chunk_size / (2**trial)))
            self._logger.info(f"{len(text_dict_chunks)} chunks ready")

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
                    self.progress.emit(int(completed / len(text_dict_chunks) * 95 * 1 / 5) + int(20 * (trial-1) / 5))
                    translated_text_dict = dict(sorted(translated_text_dict.items()))
                    ## Save Middle Translated Lines ##
                    with open(os.path.join(translated_dir, "review_text_dict.json"), "w") as f:
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
                dat = self._restore_repeat_tags(dat)
                book._contents[chapter_file] = dat.encode('utf-8')

            ## Save Translated Epub ##
            save_path = self._file_path
            book.save(save_path)
            self.completed.emit(save_path)
            self._logger.info(f"trial {trial} finished")

    def _translate_chunk(self, chunk: list[LineData], chunk_index: int, save_path: str, original_path: str):
        is_suceed: bool = True
        
        ## Load Contents For Gemini ##
        with open(original_path, "r", encoding="utf-8") as f:
            llm_contents = f.read()
        self._logger.info(f"Load Gemini Contents From {original_path}\n")

        ## Translation ##
        translated_lines = []
        for i in range(3):
            try:
                self._logger.info(f"Chunk{chunk_index} Translation (Try {i+1})")
                response_text = self._core.generate_content(llm_contents)
                translated_lines = response_text.splitlines(keepends=True)
                if len(translated_lines) != len(chunk) or re.sub(r'^\[\d+\]\s*', '', translated_lines[-1]).strip() == "":
                    self._logger.info(
                        f"Failed To Parse Translated Response Of Chunk{chunk_index} (Try {i+1})\n" + \
                        f"len(loaded_lines)={len(translated_lines)}, len(chunk)={len(chunk)} {re.sub(r'^\[\d+\]\s*', '', translated_lines[-1] if translated_lines else "No line found").strip()}"
                        )
                    if i == 2:
                        self._logger.warning(f"Final Failiure In Chunk{chunk_index} Translation")
                        is_suceed = False
                    continue

                ## Update Chunk's Translated Fields ##
                for i, line in enumerate(translated_lines):
                    chunk[i].translated = self._restore_repeat_tags(re.sub(r'^\[\d+\]\s*', '', line).strip())
                self._logger.info(f"Updated Chunks[{chunk_index}] Data")
                time.sleep(self._request_delay)
                return is_suceed, chunk_index
            except Exception as e:
                self._logger.exception(str(e))
                continue
        
    
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