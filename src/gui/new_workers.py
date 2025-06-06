import asyncio
from PyQt5.QtCore import QThread, pyqtSignal
from new_epub_processor import EPUBProcessor

# 공통 기능을 담당하는 기본 워커 클래스 (이미 정의된 BaseTranslatorWorker)
class BaseTranslatorWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, input_path, output_path, settings, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.settings = settings
        self.epub_processor = EPUBProcessor(self.input_path)
        self.client = None # 클라이언트 인스턴스 저장
        self.translator_core = None # translator_core 모듈 저장

    def setup_client(self):
        # 공통: 클라이언트 및 translator_core 초기화
        from google import genai
        from google.genai.types import HttpOptions
        from google.oauth2 import service_account # Vertex AI용
        import json # Vertex AI용
        import os # Vertex AI용
        import translator_core

        use_vertex_ai = self.settings.get("use_vertex_ai", False)
        service_account_json_path = self.settings.get("service_account_json_path")
        gcp_project_id_setting = self.settings.get("gcp_project_id")
        gcp_location_setting = self.settings.get("gcp_location", "asia-northeast3")

        client_instance = None

        if use_vertex_ai:
            self.log_signal.emit("Vertex AI 클라이언트 사용 시도 중...")
            credentials = None
            project_id_to_use = gcp_project_id_setting
            location_to_use = gcp_location_setting

            if service_account_json_path and os.path.exists(service_account_json_path):
                try:
                    with open(service_account_json_path, 'r') as f:
                        sa_info = json.load(f)
                    credentials = service_account.Credentials.from_service_account_info(
                        sa_info,
                        scopes=['https://www.googleapis.com/auth/cloud-platform']
                    )
                    if not project_id_to_use and 'project_id' in sa_info:
                        project_id_to_use = sa_info['project_id']
                    self.log_signal.emit(f"Vertex AI: 서비스 계정 파일({service_account_json_path})에서 인증 정보 로드 완료.")
                except Exception as e:
                    self.log_signal.emit(f"Vertex AI: 서비스 계정 JSON 파일('{service_account_json_path}') 로드 오류: {e}")
            elif service_account_json_path: # 경로가 있지만 파일이 없는 경우
                self.log_signal.emit(f"Vertex AI: 서비스 계정 JSON 파일('{service_account_json_path}')을 찾을 수 없습니다. ADC(Application Default Credentials)를 시도합니다.")
            else: # 경로가 제공되지 않은 경우
                self.log_signal.emit("Vertex AI: 서비스 계정 JSON 경로가 제공되지 않았습니다. ADC를 시도합니다.")

            if not project_id_to_use: project_id_to_use = os.environ.get('GOOGLE_CLOUD_PROJECT')
            if not location_to_use: location_to_use = os.environ.get('GOOGLE_CLOUD_LOCATION', gcp_location_setting) # 설정값 > 환경변수 > 기본값 순

            if not project_id_to_use:
                raise ValueError("Vertex AI: GCP Project ID가 필요하지만 설정, 서비스 계정 파일 또는 환경 변수에서 찾을 수 없습니다.")
            if not location_to_use: # 기본값이 있으므로 이 경우는 드물지만 명시
                raise ValueError("Vertex AI: GCP Location이 필요합니다.")

            self.log_signal.emit(f"Vertex AI: Project ID: {project_id_to_use}, Location: {location_to_use}로 클라이언트 초기화 중.")
            client_instance = genai.Client(
                vertexai=True, project=project_id_to_use, location=location_to_use, credentials=credentials,
                http_options=HttpOptions(timeout=10 * 60 * 1000)
            )
            self.log_signal.emit("Vertex AI 클라이언트 초기화 성공.")
        else:
            self.log_signal.emit("표준 Gemini API 클라이언트 (API 키) 사용 중...")
            api_key = self.settings.get("api_key", "").strip()
            if not api_key: raise ValueError("표준 모드: API 키가 설정에서 누락되었습니다.")
            client_instance = genai.Client(api_key=api_key, http_options=HttpOptions(timeout=10 * 60 * 1000))
            self.log_signal.emit("표준 Gemini API 클라이언트 초기화 성공.")
        
        self.client = client_instance
        translator_core.set_client(self.client)
        translator_core.set_llm_model(self.settings.get("gemini_model", "gemini-2.0-flash"))
        translator_core.set_chunk_size(self.settings.get("chunk_size", 1800)) # dialogs.py의 기본값과 일치
        translator_core.set_custom_prompt(self.settings.get("custom_prompt", ""))
        translator_core.set_llm_delay(self.settings.get("request_delay", 0.0))
        translator_core.set_japanese_char_threshold(int(self.settings.get("chunk_size", 1800) / 50.0))
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
    def __init__(self, input_path, output_path, settings,
                 dual_language_mode=False, completion_mode=False, image_annotation_mode=False,
                 proper_nouns=None, parent=None):
        super().__init__(input_path, output_path, settings, parent)
        self.max_concurrent = max_concurrent
        self.dual_language = dual_language_mode
        self.complete_mode = completion_mode
        self.image_annotation_mode = image_annotation_mode
        self.proper_nouns = proper_nouns

    def async_execute(self):
        asyncio.run(self.epub_processor.translate_epub_async(
            output_path=self.output_path,
            max_concurrent_requests=self.settings.get("max_concurrent_requests", 1),
            complete_mode=self.complete_mode,
            progress_callback=self.progress_signal.emit,
            proper_nouns=self.proper_nouns,
        ))


# DualLanguageApplyWorker는 번역이 완료된 EPUB 파일에 대해 
# 원본과 번역문을 병합하여 dual language 형태로 적용하는 역할을 합니다.
class DualLanguageApplyWorker(BaseTranslatorWorker):
    def __init__(self, input_path, output_path, api_key, gemini_model,
                 chunk_size, custom_prompt, delay, settings, parent=None): # settings 추가
        super().__init__(input_path, output_path, settings, parent)
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
    def __init__(self, input_path, output_path, settings,
                 dual_language_mode=False, completion_mode=False, image_annotation_mode=False,
                 proper_nouns=None, parent=None):
        super().__init__(input_path, output_path, settings, parent)
        self.max_concurrent = max_concurrent
        self.dual_language = dual_language_mode
        self.complete_mode = completion_mode
        self.image_annotation_mode = image_annotation_mode
        self.proper_nouns = proper_nouns

    def async_execute(self):
        asyncio.run(self.epub_processor.translate_completion_async(
            output_path=self.output_path,
            max_concurrent_requests=self.settings.get("max_concurrent_requests", 1),
            progress_callback=self.progress_signal.emit,
        ))


# 3. ImageAnnotationWorker : 이미지 어노테이션 작업용
class ImageAnnotationWorker(BaseTranslatorWorker):
    def __init__(self, input_path, output_path, settings,
                 dual_language_mode=False, completion_mode=False, image_annotation_mode=False,
                 proper_nouns=None, parent=None):
        super().__init__(input_path, output_path, settings, parent)
        # self.max_concurrent = max_concurrent # annotate_images_async는 max_concurrent_requests를 직접 받지 않음
        self.dual_language = dual_language_mode
        self.complete_mode = completion_mode
        self.image_annotation_mode = image_annotation_mode
        self.proper_nouns = proper_nouns

    def async_execute(self):
        asyncio.run(self.epub_processor.annotate_images_async(
            output_path=self.output_path,
            max_concurrent_requests=self.settings.get("max_concurrent_requests", 1), # EPUBProcessor.annotate_images_async가 이 인자를 사용하도록 수정 필요 또는 내부적으로 설정값 사용
            progress_callback=self.progress_signal.emit,
        ))


# 4. TocTranslationWorker : 목차 등 기타 번역 작업용
class TocTranslationWorker(BaseTranslatorWorker):
    def __init__(self, input_path, output_path, settings, parent=None):
        super().__init__(input_path, output_path, settings, parent)

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

    def __init__(self, input_path, output_path, settings, delay, max_concurrent_requests, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.settings = settings
        self.delay = delay
        self.max_concurrent_requests = max_concurrent_requests

    def run(self):
        try:
            from google import genai
            from google.genai.types import HttpOptions
            from google.oauth2 import service_account # Vertex AI용
            import json # Vertex AI용
            import os # Vertex AI용
            from extractor import ProperNounExtractor

            use_vertex_ai = self.settings.get("use_vertex_ai", False)
            service_account_json_path = self.settings.get("service_account_json_path")
            gcp_project_id_setting = self.settings.get("gcp_project_id")
            gcp_location_setting = self.settings.get("gcp_location", "asia-northeast3")
            
            client_for_extractor = None

            if use_vertex_ai:
                self.log_signal.emit("ExtractionWorker: Vertex AI 클라이언트 사용 시도 중...")
                credentials = None
                project_id_to_use = gcp_project_id_setting
                location_to_use = gcp_location_setting
                if service_account_json_path and os.path.exists(service_account_json_path):
                    try:
                        with open(service_account_json_path, 'r') as f: sa_info = json.load(f)
                        credentials = service_account.Credentials.from_service_account_info(sa_info, scopes=['https://www.googleapis.com/auth/cloud-platform'])
                        if not project_id_to_use and 'project_id' in sa_info: project_id_to_use = sa_info['project_id']
                    except Exception as e: self.log_signal.emit(f"ExtractionWorker (Vertex AI): 서비스 계정 JSON 로드 오류: {e}")
                
                if not project_id_to_use: project_id_to_use = os.environ.get('GOOGLE_CLOUD_PROJECT')
                if not location_to_use: location_to_use = os.environ.get('GOOGLE_CLOUD_LOCATION', gcp_location_setting)

                if not project_id_to_use: raise ValueError("ExtractionWorker (Vertex AI): GCP Project ID가 필요합니다.")
                if not location_to_use: raise ValueError("ExtractionWorker (Vertex AI): GCP Location이 필요합니다.")
                client_for_extractor = genai.Client(vertexai=True, project=project_id_to_use, location=location_to_use, credentials=credentials, http_options=HttpOptions(timeout=10*60*1000))
            else:
                self.log_signal.emit("ExtractionWorker: 표준 Gemini API 클라이언트 (API 키) 사용 중...")
                api_key = self.settings.get("api_key", "").strip()
                if not api_key: raise ValueError("ExtractionWorker (표준 모드): API 키가 설정에서 누락되었습니다.")
                client_for_extractor = genai.Client(api_key=api_key, http_options=HttpOptions(timeout=10 * 60 * 1000))

            gemini_model = self.settings.get("gemini_model", "gemini-2.0-flash")
            extractor = ProperNounExtractor(self.input_path, client_for_extractor, gemini_model)
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
