from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QUrl
from PyQt5.QtGui import QFont, QPixmap, QDesktopServices
from extractor import ProperNounExtractor
from ruby_remover import remove_ruby_from_epub
import asyncio

class TranslationWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, input_path, output_path, max_concurrent,
                 gemini_model, chunk_size, custom_prompt, api_key, delay, language='Japanese',
                 dual_language_mode=False, completion_mode=False, image_annotation_mode=False, proper_nouns=None, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.max_concurrent = max_concurrent
        self.gemini_model = gemini_model
        self.chunk_size = chunk_size
        self.custom_prompt = custom_prompt
        self.api_key = api_key
        self.delay = delay
        self.dual_language = dual_language_mode
        self.complete_mode = completion_mode
        self.proper_nouns = proper_nouns
        self.image_annotation_mode = image_annotation_mode
        self.language = language

    def run(self):
        try:
            from google import genai
            from google.genai.types import HttpOptions
            import translator_core
            global client
            client = genai.Client(api_key=self.api_key, http_options=HttpOptions(timeout=10 * 60 * 1000))
            translator_core.set_client(client)
            translator_core.set_llm_model(self.gemini_model)
            translator_core.set_chunk_size(self.chunk_size)
            translator_core.set_custom_prompt(self.custom_prompt)
            translator_core.set_llm_delay(self.delay)
            translator_core.set_japanese_char_threshold(int(self.chunk_size / 50.0))
            def progress_callback(percent):
                self.progress_signal.emit(int(percent))
            from epub_processor import translate_epub_async
            asyncio.run(translate_epub_async(
                self.input_path,
                self.output_path,
                self.max_concurrent,
                dual_language=self.dual_language,
                complete_mode=self.complete_mode,
                progress_callback=progress_callback,
                proper_nouns=self.proper_nouns,  # <-- proper nouns passed here
                image_annotation_mode=self.image_annotation_mode,
            ))
            self.progress_signal.emit(100)
            self.finished_signal.emit(self.output_path)
        except Exception as e:
            self.log_signal.emit(f"에러로 인한 번역 실패: {e}")

class CompletionTranslationWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, input_path, output_path, max_concurrent,
                 gemini_model, chunk_size, custom_prompt, api_key, delay, language='Japanese',
                 dual_language_mode=False, completion_mode=False, image_annotation_mode=False, proper_nouns=None, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.max_concurrent = max_concurrent
        self.gemini_model = gemini_model
        self.chunk_size = chunk_size
        self.custom_prompt = custom_prompt
        self.api_key = api_key
        self.delay = delay
        self.dual_language = dual_language_mode
        self.complete_mode = completion_mode
        self.proper_nouns = proper_nouns
        self.image_annotation_mode = image_annotation_mode
        self.language = language

    def run(self):
        try:
            from google import genai
            from google.genai.types import HttpOptions
            import translator_core
            global client
            client = genai.Client(api_key=self.api_key, http_options=HttpOptions(timeout=10 * 60 * 1000))
            translator_core.set_client(client)
            translator_core.set_llm_model(self.gemini_model)
            translator_core.set_chunk_size(self.chunk_size)
            translator_core.set_custom_prompt(self.custom_prompt)
            translator_core.set_llm_delay(self.delay)
            translator_core.set_japanese_char_threshold(int(self.chunk_size / 50.0))
            def progress_callback(percent):
                self.progress_signal.emit(int(percent))
            from epub_processor import translate_completion_async
            asyncio.run(translate_completion_async(
                self.input_path,
                self.output_path,
                self.max_concurrent,
                dual_language=self.dual_language,
                complete_mode=self.complete_mode,
                image_annotation_mode=self.image_annotation_mode,
                proper_nouns=self.proper_nouns,  # <-- proper nouns passed here
                progress_callback=progress_callback,
                language=self.language
            ))
            self.progress_signal.emit(100)
            self.finished_signal.emit(self.output_path)
        except Exception as e:
            self.log_signal.emit(f"에러로 인한 번역 실패: {e}")

class ImageAnnotationWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, input_path, output_path, max_concurrent,
                 gemini_model, chunk_size, custom_prompt, api_key, delay, language='Japanese',
                 dual_language_mode=False, completion_mode=False, image_annotation_mode=False, proper_nouns=None, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.max_concurrent = max_concurrent
        self.gemini_model = gemini_model
        self.chunk_size = chunk_size
        self.custom_prompt = custom_prompt
        self.api_key = api_key
        self.delay = delay
        self.dual_language = dual_language_mode
        self.complete_mode = completion_mode
        self.proper_nouns = proper_nouns
        self.image_annotation_mode = image_annotation_mode
        self.language = language

    def run(self):
        try:
            from google import genai
            from google.genai.types import HttpOptions
            import translator_core
            global client
            client = genai.Client(api_key=self.api_key, http_options=HttpOptions(timeout=10 * 60 * 1000))
            translator_core.set_client(client)
            translator_core.set_llm_model(self.gemini_model)
            translator_core.set_chunk_size(self.chunk_size)
            translator_core.set_custom_prompt(self.custom_prompt)
            translator_core.set_llm_delay(self.delay)
            translator_core.set_japanese_char_threshold(int(self.chunk_size / 50.0))
            def progress_callback(percent):
                self.progress_signal.emit(int(percent))
            from epub_processor import annotate_images
            asyncio.run(annotate_images(
                self.input_path,
                self.output_path,
                self.max_concurrent,
                dual_language=self.dual_language,
                complete_mode=self.complete_mode,
                image_annotation_mode=self.image_annotation_mode,
                proper_nouns=self.proper_nouns,  # <-- proper nouns passed here
                progress_callback=progress_callback,
            ))
            self.progress_signal.emit(100)
            self.finished_signal.emit(self.output_path)
        except Exception as e:
            raise Exception(f"에러로 인한 번역 실패: {e}")

class TocTranslationWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, input_path, output_path, max_concurrent,
                 gemini_model, chunk_size, custom_prompt, api_key, delay, language='Japanese',
                 dual_language_mode=False, completion_mode=False, image_annotation_mode=False, proper_nouns=None, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.max_concurrent = max_concurrent
        self.gemini_model = gemini_model
        self.chunk_size = chunk_size
        self.custom_prompt = custom_prompt
        self.api_key = api_key
        self.delay = delay
        self.dual_language = dual_language_mode
        self.complete_mode = completion_mode
        self.proper_nouns = proper_nouns
        self.image_annotation_mode = image_annotation_mode
        self.language = language

    def run(self):
        try:
            from google import genai
            from google.genai.types import HttpOptions
            import translator_core
            global client
            client = genai.Client(api_key=self.api_key, http_options=HttpOptions(timeout=10 * 60 * 1000))
            translator_core.set_client(client)
            translator_core.set_llm_model(self.gemini_model)
            translator_core.set_chunk_size(self.chunk_size)
            translator_core.set_custom_prompt(self.custom_prompt)
            translator_core.set_llm_delay(self.delay)
            translator_core.set_japanese_char_threshold(int(self.chunk_size / 50.0))
            def progress_callback(percent):
                self.progress_signal.emit(int(percent))
            from epub_processor import translate_miscellaneous_async
            asyncio.run(translate_miscellaneous_async(
                self.input_path,
                self.output_path,
                progress_callback=progress_callback,
            ))
            self.progress_signal.emit(100)
            self.finished_signal.emit(self.output_path)
        except Exception as e:
            self.log_signal.emit(f"에러로 인한 번역 실패: {e}")

class ExtractionWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, input_path, output_path, api_key, gemini_model, delay, max_concurrent_requests, language, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.api_key = api_key
        self.gemini_model = gemini_model
        self.delay = delay
        self.max_concurrent_requests = max_concurrent_requests
        self.language = language

    def run(self):
        try:
            from google import genai
            from google.genai.types import HttpOptions
            from extractor import ProperNounExtractor
            client = genai.Client(api_key=self.api_key, http_options=HttpOptions(timeout=10 * 60 * 1000))
            extractor = ProperNounExtractor(self.input_path, client, self.gemini_model)
            extractor.run_extraction(delay=self.delay,max_concurrent_requests=self.max_concurrent_requests,progress_callback=self.progress_signal.emit)
            extractor.save_to_csv(self.output_path)
            self.finished_signal.emit(self.output_path)
        except Exception as e:
            self.log_signal.emit(f"Proper noun extraction failed: {e}")

class RubyRemoverWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, input_path, parent=None):
        super().__init__(parent)
        self.input_path = input_path
    
    def run(self):
        try:
            remove_ruby_from_epub(epub_path=self.input_path, progress_callback=self.progress_signal.emit, log_callback=self.log_signal.emit)
            self.finished_signal.emit(self.input_path)
        except Exception as e:
            self.log_signal.emit(f"루비 제거 실패: {e}")