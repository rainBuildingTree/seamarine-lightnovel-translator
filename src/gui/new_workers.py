import asyncio
from PyQt5.QtCore import QThread, pyqtSignal
from new_epub_processor import EPUBProcessor

# 공통 기능을 담당하는 기본 워커 클래스 (이미 정의된 BaseTranslatorWorker)
class BaseTranslatorWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, input_path, output_path, api_key, gemini_model,
                 chunk_size, custom_prompt, delay, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.api_key = api_key
        self.gemini_model = gemini_model
        self.chunk_size = chunk_size
        self.custom_prompt = custom_prompt
        self.delay = delay
        self.epub_processor = EPUBProcessor(self.input_path)

    def setup_client(self):
        # 공통: 클라이언트 및 translator_core 초기화
        from google import genai
        from google.genai.types import HttpOptions
        import translator_core
        self.client = genai.Client(
            api_key=self.api_key,
            http_options=HttpOptions(timeout=10 * 60 * 1000)
        )
        translator_core.set_client(self.client)
        translator_core.set_llm_model(self.gemini_model)
        translator_core.set_chunk_size(self.chunk_size)
        translator_core.set_custom_prompt(self.custom_prompt)
        translator_core.set_llm_delay(self.delay)
        translator_core.set_japanese_char_threshold(int(self.chunk_size / 50.0))
        self.translator_core = translator_core

    def run(self):
        try:
            self.setup_client()
            # 자식 클래스에서 비동기 작업 실행 로직 구현
            self.async_execute()
            self.progress_signal.emit(100)
            self.finished_signal.emit(self.output_path)
        except Exception as e:
            self.log_signal.emit(f"에러로 인한 번역 실패: {e}")

    def async_execute(self):
        raise NotImplementedError("자식 클래스에서 async_execute를 구현해야 합니다.")


# 기존 TranslationWorker는 EPUB 전체 번역을 수행합니다.
class TranslationWorker(BaseTranslatorWorker):
    def __init__(self, input_path, output_path, max_concurrent, api_key, gemini_model,
                 chunk_size, custom_prompt, delay,
                 dual_language_mode=False, completion_mode=False, image_annotation_mode=False,
                 proper_nouns=None, parent=None):
        super().__init__(input_path, output_path, api_key, gemini_model,
                         chunk_size, custom_prompt, delay, parent)
        self.max_concurrent = max_concurrent
        self.dual_language = dual_language_mode
        self.complete_mode = completion_mode
        self.image_annotation_mode = image_annotation_mode
        self.proper_nouns = proper_nouns

    def async_execute(self):
        asyncio.run(self.epub_processor.translate_epub_async(
            output_path=self.output_path,
            max_concurrent_requests=self.max_concurrent,
            complete_mode=self.complete_mode,
            progress_callback=self.progress_signal.emit,
            proper_nouns=self.proper_nouns,
        ))


# DualLanguageApplyWorker는 번역이 완료된 EPUB 파일에 대해 
# 원본과 번역문을 병합하여 dual language 형태로 적용하는 역할을 합니다.
class DualLanguageApplyWorker(BaseTranslatorWorker):
    def __init__(self, input_path, output_path, api_key, gemini_model,
                 chunk_size, custom_prompt, delay, parent=None):
        super().__init__(input_path, output_path, api_key, gemini_model,
                         chunk_size, custom_prompt, delay, parent)
    
    def async_execute(self):
        # apply_dual_language_async를 호출하여 dual language 기능을 수행합니다.
        # 내부에서는 load_original_chapters()를 통해 원본 챕터를 로드하고,
        # 결합 과정 중 원본 챕터가 없으면 ValueError를 발생시킵니다.
        asyncio.run(self.epub_processor.apply_dual_language_async(
            output_path=self.output_path,
            progress_callback=self.progress_signal.emit
        ))


# 2. ProofreadingWorker : 번역 보완 작업용
class ProofreadingWorker(BaseTranslatorWorker):
    def __init__(self, input_path, output_path, max_concurrent, api_key, gemini_model,
                 chunk_size, custom_prompt, delay,
                 dual_language_mode=False, completion_mode=False, image_annotation_mode=False,
                 proper_nouns=None, parent=None):
        super().__init__(input_path, output_path, api_key, gemini_model,
                         chunk_size, custom_prompt, delay, parent)
        self.max_concurrent = max_concurrent
        self.dual_language = dual_language_mode
        self.complete_mode = completion_mode
        self.image_annotation_mode = image_annotation_mode
        self.proper_nouns = proper_nouns

    def async_execute(self):
        asyncio.run(self.epub_processor.translate_completion_async(
            output_path=self.output_path,
            max_concurrent_requests=self.max_concurrent,
            progress_callback=self.progress_signal.emit,
        ))


# 3. ImageAnnotationWorker : 이미지 어노테이션 작업용
class ImageAnnotationWorker(BaseTranslatorWorker):
    def __init__(self, input_path, output_path, max_concurrent, api_key, gemini_model,
                 chunk_size, custom_prompt, delay,
                 dual_language_mode=False, completion_mode=False, image_annotation_mode=False,
                 proper_nouns=None, parent=None):
        super().__init__(input_path, output_path, api_key, gemini_model,
                         chunk_size, custom_prompt, delay, parent)
        self.max_concurrent = max_concurrent
        self.dual_language = dual_language_mode
        self.complete_mode = completion_mode
        self.image_annotation_mode = image_annotation_mode
        self.proper_nouns = proper_nouns

    def async_execute(self):
        asyncio.run(self.epub_processor.annotate_images_async(
            output_path=self.output_path,
            max_concurrent_requests=self.max_concurrent,
            progress_callback=self.progress_signal.emit,
        ))


# 4. TocTranslationWorker : 목차 등 기타 번역 작업용
class TocTranslationWorker(BaseTranslatorWorker):
    def __init__(self, input_path, output_path, api_key, gemini_model,
                 chunk_size, custom_prompt, delay, parent=None):
        super().__init__(input_path, output_path, api_key, gemini_model,
                         chunk_size, custom_prompt, delay, parent)

    def async_execute(self):
        asyncio.run(self.epub_processor.translate_miscellaneous_async(
            output_path=self.output_path,
            progress_callback=self.progress_signal.emit,
        ))


# 5. ExtractionWorker : 고유명사 추출 작업 (기본 번역 로직과는 별도)
class ExtractionWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, input_path, output_path, api_key, gemini_model, delay,
                 max_concurrent_requests, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.api_key = api_key
        self.gemini_model = gemini_model
        self.delay = delay
        self.max_concurrent_requests = max_concurrent_requests

    def run(self):
        try:
            from google import genai
            from google.genai.types import HttpOptions
            from extractor import ProperNounExtractor
            client = genai.Client(api_key=self.api_key, http_options=HttpOptions(timeout=10 * 60 * 1000))
            extractor = ProperNounExtractor(self.input_path, client, self.gemini_model)
            extractor.run_extraction(
                delay=self.delay,
                max_concurrent_requests=self.max_concurrent_requests,
                progress_callback=self.progress_signal.emit
            )
            extractor.save_to_csv(self.output_path)
            self.finished_signal.emit(self.output_path)
        except Exception as e:
            self.log_signal.emit(f"Proper noun extraction failed: {e}")


# 6. RubyRemoverWorker : EPUB 파일 내 루비 텍스트 제거 작업용
class RubyRemoverWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, input_path, parent=None):
        super().__init__(parent)
        self.input_path = input_path

    def run(self):
        try:
            from ruby_remover import remove_ruby_from_epub
            remove_ruby_from_epub(
                epub_path=self.input_path,
                progress_callback=self.progress_signal.emit,
                log_callback=self.log_signal.emit
            )
            self.finished_signal.emit(self.input_path)
        except Exception as e:
            self.log_signal.emit(f"루비 제거 실패: {e}")
