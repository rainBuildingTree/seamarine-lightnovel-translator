import sys
import os
import json
import asyncio
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QTextEdit, QPushButton,
    QProgressBar, QFileDialog, QDialog, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QUrl
from PyQt5.QtGui import QFont, QPixmap, QDesktopServices

# Worker Thread for translation (기존 코드와 동일하되, delay 값과 dual_language 플래그 추가)
class TranslationWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, input_path, output_path, max_concurrent,
                 gemini_model, chunk_size, custom_prompt, api_key, delay, dual_language=False, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.max_concurrent = max_concurrent
        self.gemini_model = gemini_model
        self.chunk_size = chunk_size
        self.custom_prompt = custom_prompt
        self.api_key = api_key
        self.delay = delay  # 번역 요청간 딜레이 값 (초)
        self.dual_language = dual_language

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

            def progress_callback(percent):
                self.progress_signal.emit(int(percent))

            # dual_language 플래그를 translate_epub_async 함수에 전달 (해당 함수가 dual_language 처리를 지원한다고 가정)
            from epub_processor import translate_epub_async
            asyncio.run(translate_epub_async(
                self.input_path,
                self.output_path,
                self.max_concurrent,
                dual_language=self.dual_language,
                progress_callback=progress_callback,
            ))
            self.progress_signal.emit(100)
            self.finished_signal.emit(self.output_path)
        except Exception as e:
            self.log_signal.emit(f"에러로 인한 번역 실패: {e}")


class EasterEggDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("시마 린 Epub 번역기")
        self.setMinimumSize(400, 300)
        layout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        
        # JPG 파일 경로 설정
        jpg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "very_important_folder", "very_important_file.jpg")
        if os.path.exists(jpg_path):
            pixmap = QPixmap(jpg_path)
            self.label.setPixmap(pixmap)
        else:
            self.label.setText("파일을 찾을 수 없습니다.")


class TranslatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        # 시스템에 설치된 한글 지원 폰트 사용 (예: "Malgun Gothic")
        self.font = QFont("Malgun Gothic", 12)
        self.setFont(self.font)

        self.setWindowTitle("Sea Marine EPUB 번역기")
        self.setGeometry(100, 100, 800, 750)
        self.input_path = None
        self.output_path = None

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # API Key 입력 + 링크 버튼
        api_layout = QHBoxLayout()
        api_label = QLabel("Gemini API 키:")
        api_label.setFont(self.font)

        self.api_entry = QLineEdit()
        self.api_entry.setEchoMode(QLineEdit.Password)
        self.api_entry.setFont(self.font)
        self.api_entry.setFixedWidth(300)  # 텍스트 입력창 너비 조절

        self.api_link_button = QPushButton("API 발급/확인 하러가기")
        self.api_link_button.setFont(self.font)
        self.api_link_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://aistudio.google.com/app/apikey"))
        )

        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_entry)
        api_layout.addWidget(self.api_link_button)
        main_layout.addLayout(api_layout)

        # Gemini 모델 선택 (콤보박스를 편집 가능하게 설정)
        model_layout = QHBoxLayout()
        model_label = QLabel("Gemini 모델:")
        model_label.setFont(self.font)
        self.model_combobox = QComboBox()
        self.model_combobox.setFont(self.font)
        self.model_combobox.setEditable(True)  # 사용자가 직접 입력할 수 있도록 설정
        self.model_combobox.addItems([
            "Gemini 2.5 Pro Experimental",
            "Gemini 2.0 Flash",
            "Gemini 1.5 Pro"
        ])
        self.model_combobox.setCurrentText("Gemini 2.0 Flash")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combobox)
        main_layout.addLayout(model_layout)

        # 청크 사이즈 입력
        chunk_layout = QHBoxLayout()
        chunk_label = QLabel("청크 사이즈 (커질수록 문맥을 길게 보지만, 빠지는게 생기고 실패율 올라감):")
        chunk_label.setFont(self.font)
        self.chunk_spinbox = QSpinBox()
        self.chunk_spinbox.setFont(self.font)
        self.chunk_spinbox.setRange(1000, 100000)
        self.chunk_spinbox.setValue(3000)
        chunk_layout.addWidget(chunk_label)
        chunk_layout.addWidget(self.chunk_spinbox)
        main_layout.addLayout(chunk_layout)

        # 유저 커스텀 프롬프트 입력
        prompt_label = QLabel("커스텀 프롬프트 (비워두면 기본값 사용, 길다면 청크 사이즈 줄일 것):")
        prompt_label.setFont(self.font)
        self.prompt_text = QTextEdit()
        self.prompt_text.setFont(self.font)
        main_layout.addWidget(prompt_label)
        main_layout.addWidget(self.prompt_text)

        # 최대 동시 요청 수 설정
        concurrent_layout = QHBoxLayout()
        concurrent_label = QLabel("최대 동시 요청 수 (1-100, 커질수록 번역이 빨라짐, 단 너무 크면 번역 실패율 오름):")
        concurrent_label.setFont(self.font)
        self.concurrent_spinbox = QSpinBox()
        self.concurrent_spinbox.setFont(self.font)
        self.concurrent_spinbox.setRange(1, 100)
        self.concurrent_spinbox.setValue(1)
        concurrent_layout.addWidget(concurrent_label)
        concurrent_layout.addWidget(self.concurrent_spinbox)
        main_layout.addLayout(concurrent_layout)

        # 번역 요청간 기본 딜레이 항목 추가 (딜레이 값 입력: 초 단위)
        delay_layout = QHBoxLayout()
        delay_label = QLabel("번역 요청 딜레이 (초, 동시 요청이 1인데 실패시 설정해볼 것)")
        delay_label.setFont(self.font)
        self.delay_spinbox = QSpinBox()
        self.delay_spinbox.setFont(self.font)
        self.delay_spinbox.setRange(0, 100)
        self.delay_spinbox.setValue(0)
        delay_layout.addWidget(delay_label)
        delay_layout.addWidget(self.delay_spinbox)
        main_layout.addLayout(delay_layout)

        # Dual Language 모드 체크박스 추가
        dual_language_layout = QHBoxLayout()
        self.dual_language_checkbox = QCheckBox("원문과 번역문 같이 표시")
        self.dual_language_checkbox.setFont(self.font)
        dual_language_layout.addWidget(self.dual_language_checkbox)
        main_layout.addLayout(dual_language_layout)

        # EPUB 파일 선택 버튼 및 선택된 파일 표시
        file_layout = QHBoxLayout()
        self.select_button = QPushButton("EPUB파일 선택")
        self.select_button.setFont(self.font)
        self.select_button.clicked.connect(self.select_file)
        self.file_label = QLabel("선택된 파일: 없음")
        self.file_label.setFont(self.font)
        file_layout.addWidget(self.select_button)
        file_layout.addWidget(self.file_label)
        main_layout.addLayout(file_layout)

        # 번역 시작 버튼
        self.translate_button = QPushButton("번역 시작")
        self.translate_button.setFont(self.font)
        self.translate_button.clicked.connect(self.start_translation)
        self.translate_button.setEnabled(False)
        main_layout.addWidget(self.translate_button)

        # 설정 저장 및 이스터 에그 버튼 추가 (로드 버튼 제거)
        settings_layout = QHBoxLayout()
        self.save_settings_button = QPushButton("현재 설정 저장")
        self.save_settings_button.setFont(self.font)
        self.save_settings_button.clicked.connect(self.save_settings)
        self.easter_egg_button = QPushButton("이 프로그램의 진짜 이름")
        self.easter_egg_button.setFont(self.font)
        self.easter_egg_button.clicked.connect(self.show_easter_egg)
        settings_layout.addWidget(self.save_settings_button)
        settings_layout.addWidget(self.easter_egg_button)
        main_layout.addLayout(settings_layout)

        # 진행 상황 표시용 로그 텍스트
        self.log_text = QTextEdit()
        self.log_text.setFont(self.font)
        self.log_text.setReadOnly(True)
        main_layout.addWidget(self.log_text)

        # 진행바
        self.progress_bar = QProgressBar()
        self.progress_bar.setFont(self.font)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        self.worker = None

        # 프로그램 시작 시 자동으로 설정 불러오기
        self.load_settings()

    def settings_file_path(self):
        """현재 프로그램이 있는 위치에 settings.json 파일 경로를 반환."""
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

    def save_settings(self):
        """현재 GUI 설정을 settings.json 파일에 저장."""
        settings = {
            "api_key": self.api_entry.text(),
            "gemini_model": self.model_combobox.currentText(),
            "chunk_size": self.chunk_spinbox.value(),
            "custom_prompt": self.prompt_text.toPlainText(),
            "max_concurrent": self.concurrent_spinbox.value(),
            "translation_delay": self.delay_spinbox.value(),
            "dual_language": self.dual_language_checkbox.isChecked()
        }
        try:
            with open(self.settings_file_path(), "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            self.append_log("설정이 저장되었습니다.")
        except Exception as e:
            self.append_log(f"설정 저장 중 오류 발생: {e}")

    def load_settings(self):
        """settings.json 파일이 있으면 GUI 설정을 불러옴."""
        try:
            file_path = self.settings_file_path()
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)
                self.api_entry.setText(settings.get("api_key", ""))
                model = settings.get("gemini_model", "Gemini 2.0 Flash")
                index = self.model_combobox.findText(model)
                if index >= 0:
                    self.model_combobox.setCurrentIndex(index)
                else:
                    self.model_combobox.setCurrentText(model)
                self.chunk_spinbox.setValue(settings.get("chunk_size", 3000))
                self.prompt_text.setPlainText(settings.get("custom_prompt", ""))
                self.concurrent_spinbox.setValue(settings.get("max_concurrent", 1))
                self.delay_spinbox.setValue(settings.get("translation_delay", 0))
                self.dual_language_checkbox.setChecked(settings.get("dual_language", False))
                self.append_log("설정이 불러와졌습니다.")
            else:
                self.append_log("저장된 설정 파일이 없습니다.")
        except Exception as e:
            self.append_log(f"설정 불러오기 오류: {e}")

    def show_easter_egg(self):
        """이스터 에그 버튼 클릭 시 very_important_file.gif 애니메이션을 보여줌."""
        dialog = EasterEggDialog(self)
        dialog.exec_()

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select EPUB File", "", "EPUB Files (*.epub);;All Files (*)"
        )
        if file_path:
            self.input_path = file_path
            self.file_label.setText(f"Selected File: {os.path.basename(file_path)}")
            self.translate_button.setEnabled(True)

    def append_log(self, message):
        self.log_text.append(message)

    def update_progress(self, value):
        self.progress_bar.setValue(value)

    def start_translation(self):
        if not self.input_path:
            self.append_log("먼저 EPUB 파일을 선택해 주세요!")
            return

        api_key = self.api_entry.text().strip()
        if not api_key:
            self.append_log("API Key를 입력해 주세요!")
            return

        max_concurrent = self.concurrent_spinbox.value()

        # Gemini 모델 선택 및 매핑
        model_mapping = {
            "Gemini 2.5 Pro Experimental": "gemini-2.5-pro-exp-03-25",
            "Gemini 2.0 Flash": "gemini-2.0-flash",
            "Gemini 1.5 Pro": "gemini-1.5-pro"
        }
        selected_model = self.model_combobox.currentText().strip()
        # 매핑에 없으면 사용자가 직접 입력한 값을 그대로 사용
        gemini_model = model_mapping.get(selected_model, selected_model)

        chunk_size = self.chunk_spinbox.value()
        custom_prompt = self.prompt_text.toPlainText().strip() or None
        delay = self.delay_spinbox.value()  # 번역 요청 딜레이 값 (초)
        dual_language = self.dual_language_checkbox.isChecked()

        # 출력 파일 경로 설정
        dir_name = os.path.dirname(self.input_path)
        base_name = os.path.splitext(os.path.basename(self.input_path))[0]
        self.output_path = os.path.join(dir_name, base_name + "_translated.epub")

        # 버튼 비활성화
        self.translate_button.setEnabled(False)
        self.select_button.setEnabled(False)
        self.append_log("번역을 시작합니다...")
        self.update_progress(0)

        # Worker 생성 후 실행 (별도 스레드)
        self.worker = TranslationWorker(
            input_path=self.input_path,
            output_path=self.output_path,
            max_concurrent=max_concurrent,
            gemini_model=gemini_model,
            chunk_size=chunk_size,
            custom_prompt=custom_prompt,
            api_key=api_key,
            delay=delay,
            dual_language=dual_language
        )
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.translation_finished)
        self.worker.start()

    @pyqtSlot(str)
    def translation_finished(self, output_path):
        if output_path:
            self.append_log(f"번역 완료! 파일: {output_path}")
        else:
            self.append_log("번역 실패!")
        self.translate_button.setEnabled(True)
        self.select_button.setEnabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranslatorGUI()
    window.show()
    sys.exit(app.exec_())
