from ..core.translate_core import TranslateCore
from ..model.ai_model_config import AiModelConfig
from utils.epub import Epub
from utils.translatable_xhtml import TranslatableXHTML, chunk_text_dict
from PySide6.QtCore import Signal, QThread
import logging
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import re
import time
import copy
import json
import html

class LineData:
    def __init__(self, file, original, translated):
        self.file = file
        self.original = original
        self.translated = translated

class TocTranslator(QThread):
    progress = Signal(int)
    completed = Signal(str)

    def __init__(self, core: TranslateCore, model_data: AiModelConfig, 
                 proper_noun: dict[str, str], file_path: str, save_directory: str, 
                 max_chunk_size: int, max_concurrent_request: int, request_delay: int):
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
        self._logger.info("[TocTranslator.init]: Thread Initialized")
    
    def run(self):
        self.progress.emit(0)
        try:
            self._execute()
            self.progress.emit(100)
            self._logger.info("[TocTranslator.run]: Task Completed")
        except Exception:
            self._logger.exception("[TocTranslator.run]: Task Failed")
            self.progress.emit(0)


    def _execute(self):
        ## Load Epub ##
        try:
            book = Epub(self._file_path)
            book.apply_pn_dictionary_to_toc(self._proper_noun)
            self._logger.info(f"[TocTranslator._execute]: {self._file_path} Loaded")
        except Exception:
            self._logger.exception(f"[TocTranslator._execute]: Failed To Load {self._file_path}")
            raise
        self.progress.emit(5)

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
        self._core.language_from = book.get_language()
        self._logger.info(f"[TocTranslator._execute]: TranslateCore Setup Completed")
        self.progress.emit(10)

        ## Extract Texts ##
        opf_xhtml = TranslatableXHTML(book._contents[book._opf_path])
        toc_xhtml = TranslatableXHTML(book._contents[book._toc_path], opf_xhtml.end_id+1)
        xhtmls = {
            book._opf_path: opf_xhtml,
            book._toc_path: toc_xhtml
        }
        text_dict_list = [xhtml.text_dict for xhtml in xhtmls.values()]
        text_dict = {k: self._apply_repeat_tags(v) for d in text_dict_list for k, v in d.items()}

        ## Save Extracted Texts ##
        working_dir_name, _ = os.path.splitext(os.path.basename(self._file_path))
        working_dir = os.path.join(self._save_directory, working_dir_name)
        original_dir = os.path.join(working_dir, "original")
        translated_dir = os.path.join(working_dir, "translated")
        os.makedirs(translated_dir, exist_ok=True)
        os.makedirs(original_dir, exist_ok=True)
        with open(os.path.join(original_dir, "toc_text_dict.json"), "w", encoding='utf-8') as f:
            json.dump(text_dict, f)
        self._logger.info(f"[TocTranslator._execute]: Saved Extraction")

        ## Load Prework ##
        if os.path.exists(os.path.join(translated_dir, "toc_text_dict.json")):
            with open(os.path.join(translated_dir, "toc_text_dict.json"), "r", encoding='utf-8') as f:
                translated_text_dict = json.load(f)
        else:
            translated_text_dict = {}

        ## Load Unfinished Work ##
        untranslated_text_dict = {k: v for k, v in text_dict.items() if k not in translated_text_dict.keys()}

        ## Chunking ##
        text_dict_chunks = chunk_text_dict(untranslated_text_dict, self._max_chunk_size)

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
                self.progress.emit(int(completed / len(text_dict_chunks) * 95))
                translated_text_dict = dict(sorted(translated_text_dict.items()))
                ## Save Middle Translated Lines ##
                with open(os.path.join(translated_dir, "toc_text_dict.json"), "w", encoding='utf-8') as f:
                    json.dump(translated_text_dict, f)
        
        translated_text_dict = dict(sorted(translated_text_dict.items()))

        ## Update Epub Contents ##
        for file in [book._opf_path, book._toc_path]:
            xhtmls[file].update_texts(translated_text_dict)
            dat = xhtmls[file].get_translated_html()
            dat = self._restore_repeat_tags(dat)
            book._contents[file] = dat.encode('utf-8')
            print(dat.encode('utf-8'))

        ## Save Translated Epub ##
        save_path = self._file_path
        book.save(save_path)
        self.completed.emit(save_path)

        ## Save Final Translated Lines ##
        with open(os.path.join(translated_dir, "toc_text_dict.json"), "w", encoding='utf-8') as f:
            json.dump(translated_text_dict, f)

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

    def _translate_toc(self, data: list[LineData], save_path: str, original_path: str):
        is_suceed: bool = True

        ## Load Saved Chunk Data ##
        if os.path.exists(save_path):
            self._logger.info(f"Try To Load Existing Data From {save_path}")
            with open(save_path, "r", encoding="utf-8") as f:
                loaded_lines = f.readlines()
            if len(loaded_lines) == len(data) and re.sub(r'^\[\d+\]\s*', '', loaded_lines[-1]).strip() != "":
                for i, line in enumerate(loaded_lines):
                    data[i].translated = re.sub(r'^\[\d+\]\s*', '', line).strip()
                self._logger.info(f"Successfully Loaded Data From {save_path}")
                return is_suceed
            self._logger.info(f"""
                Failed To Load Data:
                len(loaded_lines)={len(loaded_lines)}, len(data)={len(data)} {re.sub(r'^\[\d+\]\s*', '', loaded_lines[-1] if loaded_lines else "No line found").strip()}
                """.strip())
        
            os.remove(save_path)
        
        ## Load Contents For Gemini ##
        with open(original_path, "r", encoding="utf-8") as f:
            llm_contents = f.read()
        self._logger.info(f"Load Gemini Contents From {original_path}\n")

        ## Translation ##
        translated_lines = []
        for i in range(3):
            try:
                self._logger.info(f"Translation (Try {i+1})")
                response_text = self._core.generate_content(llm_contents)
                translated_lines = response_text.splitlines(keepends=True)
                if len(translated_lines) != len(data) or re.sub(r'^\[\d+\]\s*', '', translated_lines[-1]).strip() == "":
                    self._logger.info(
                        f"Failed To Parse Translated Response (Try {i+1})\n" + \
                        f"len(loaded_lines)={len(translated_lines)}, len(data)={len(data)} {re.sub(r'^\[\d+\]\s*', '', translated_lines[-1] if translated_lines else "No line found").strip()}"
                        )
                    if i == 2:
                        self._logger.warning(f"Final Failiure In Translation")
                        is_suceed = False
                    continue
            
                ## Save Translated Chunk ##
                with open(save_path, "w", encoding="utf-8") as f:
                    f.writelines(translated_lines)
                    f.flush()
                    os.fsync(f.fileno())
                self._logger.info(f"Saved Data To {save_path}")

                ## Update Chunk's Translated Fields ##
                for i, line in enumerate(translated_lines):
                    data[i].translated = re.sub(r'^\[\d+\]\s*', '', line).strip()
                self._logger.info(f"Updated Data")
                time.sleep(self._request_delay)
                return is_suceed
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
        unescaped_html = html_content
        
        pattern = re.compile(r'&lt;repeat\s+time=&quot;(\d+)&quot;&gt;(.*?)&lt;/repeat&gt;', re.DOTALL)
        
        while True:
            match = pattern.search(unescaped_html)
            if not match:
                break
            
            count = int(match.group(1))
            content = match.group(2)
            repeated_content = content * count
            
            unescaped_html = unescaped_html[:match.start()] + repeated_content + unescaped_html[match.end():]
        
        return unescaped_html