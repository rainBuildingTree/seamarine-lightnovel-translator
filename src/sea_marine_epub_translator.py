import sys
import os
import json
import csv
import asyncio
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QComboBox, QSpinBox, QTextEdit, QPushButton,
    QProgressBar, QFileDialog, QDialog, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, pyqtSlot, QUrl
from PyQt5.QtGui import QFont, QPixmap, QDesktopServices
from extractor import ProperNounExtractor

class TranslationWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, input_path, output_path, max_concurrent,
                 gemini_model, chunk_size, custom_prompt, api_key, delay,
                 dual_language=False, complete_mode=True, proper_nouns=None, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.max_concurrent = max_concurrent
        self.gemini_model = gemini_model
        self.chunk_size = chunk_size
        self.custom_prompt = custom_prompt
        self.api_key = api_key
        self.delay = delay
        self.dual_language = dual_language
        self.complete_mode = complete_mode
        self.proper_nouns = proper_nouns

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
                proper_nouns=self.proper_nouns  # <-- proper nouns passed here
            ))
            self.progress_signal.emit(100)
            self.finished_signal.emit(self.output_path)
        except Exception as e:
            self.log_signal.emit(f"에러로 인한 번역 실패: {e}")

class ExtractionWorker(QThread):
    progress_signal = pyqtSignal(int)
    log_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str)

    def __init__(self, input_path, output_path, api_key, gemini_model, delay, parent=None):
        super().__init__(parent)
        self.input_path = input_path
        self.output_path = output_path
        self.api_key = api_key
        self.gemini_model = gemini_model
        self.delay = delay

    def run(self):
        try:
            from google import genai
            from google.genai.types import HttpOptions
            from extractor import ProperNounExtractor
            client = genai.Client(api_key=self.api_key, http_options=HttpOptions(timeout=10 * 60 * 1000))
            extractor = ProperNounExtractor(self.input_path, client, self.gemini_model)
            extractor.run_extraction(delay=self.delay,progress_callback=self.progress_signal.emit)
            extractor.save_to_csv(self.output_path)
            self.finished_signal.emit(self.output_path)
        except Exception as e:
            self.log_signal.emit(f"Proper noun extraction failed: {e}")

class EasterEggDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("시마 린 Epub 번역기")
        self.setMinimumSize(400, 300)
        layout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
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
        api_layout = QHBoxLayout()
        api_label = QLabel("Gemini API 키:")
        api_label.setFont(self.font)
        self.api_entry = QLineEdit()
        self.api_entry.setEchoMode(QLineEdit.Password)
        self.api_entry.setFont(self.font)
        self.api_entry.setFixedWidth(300)
        self.api_link_button = QPushButton("API 발급/확인 하러가기")
        self.api_link_button.setFont(self.font)
        self.api_link_button.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl("https://aistudio.google.com/app/apikey"))
        )
        api_layout.addWidget(api_label)
        api_layout.addWidget(self.api_entry)
        api_layout.addWidget(self.api_link_button)
        main_layout.addLayout(api_layout)
        model_layout = QHBoxLayout()
        model_label = QLabel("Gemini 모델:")
        model_label.setFont(self.font)
        self.model_combobox = QComboBox()
        self.model_combobox.setFont(self.font)
        self.model_combobox.setEditable(True)
        self.model_combobox.addItems([
            "Gemini 2.5 Pro Experimental",
            "Gemini 2.0 Flash",
            "Gemini 1.5 Pro"
        ])
        self.model_combobox.setCurrentText("Gemini 2.0 Flash")
        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combobox)
        main_layout.addLayout(model_layout)
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
        prompt_label = QLabel("커스텀 프롬프트 (비워두면 기본값 사용, 길다면 청크 사이즈 줄일 것):")
        prompt_label.setFont(self.font)
        self.prompt_text = QTextEdit()
        self.prompt_text.setFont(self.font)
        main_layout.addWidget(prompt_label)
        main_layout.addWidget(self.prompt_text)
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
        dual_language_layout = QHBoxLayout()
        self.dual_language_checkbox = QCheckBox("원문과 번역문 같이 표시")
        self.dual_language_checkbox.setFont(self.font)
        dual_language_layout.addWidget(self.dual_language_checkbox)
        main_layout.addLayout(dual_language_layout)
        completion_mode_layout = QHBoxLayout()
        self.completion_mode_checkbox = QCheckBox("컴플리트 모드 (마지막에 한번 더 일본어를 찾아서 번역하는 모드, AI 사용량 높음)")
        self.completion_mode_checkbox.setFont(self.font)
        completion_mode_layout.addWidget(self.completion_mode_checkbox)
        main_layout.addLayout(completion_mode_layout)
        file_layout = QHBoxLayout()
        self.select_button = QPushButton("EPUB파일 선택")
        self.select_button.setFont(self.font)
        self.select_button.clicked.connect(self.select_file)
        self.file_label = QLabel("선택된 파일: 없음")
        self.file_label.setFont(self.font)
        file_layout.addWidget(self.select_button)
        file_layout.addWidget(self.file_label)
        main_layout.addLayout(file_layout)
        self.extract_button = QPushButton("고유명사 추출")
        self.extract_button.setFont(self.font)
        self.extract_button.clicked.connect(self.start_extraction)
        main_layout.addWidget(self.extract_button)
        self.translate_button = QPushButton("번역 시작")
        self.translate_button.setFont(self.font)
        self.translate_button.clicked.connect(self.start_translation)
        self.translate_button.setEnabled(False)
        main_layout.addWidget(self.translate_button)
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
        self.log_text = QTextEdit()
        self.log_text.setFont(self.font)
        self.log_text.setReadOnly(True)
        main_layout.addWidget(self.log_text)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFont(self.font)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        self.worker = None
        self.extraction_worker = None
        self.load_settings()

    def settings_file_path(self):
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

    def save_settings(self):
        settings = {
            "api_key": self.api_entry.text(),
            "gemini_model": self.model_combobox.currentText(),
            "chunk_size": self.chunk_spinbox.value(),
            "custom_prompt": self.prompt_text.toPlainText(),
            "max_concurrent": self.concurrent_spinbox.value(),
            "translation_delay": self.delay_spinbox.value(),
            "dual_language": self.dual_language_checkbox.isChecked(),
            "complete_mode": self.completion_mode_checkbox.isChecked()
        }
        try:
            with open(self.settings_file_path(), "w", encoding="utf-8") as f:
                json.dump(settings, f, indent=4, ensure_ascii=False)
            self.append_log("설정이 저장되었습니다.")
        except Exception as e:
            self.append_log(f"설정 저장 중 오류 발생: {e}")

    def load_settings(self):
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
                self.completion_mode_checkbox.setChecked(settings.get("complete_mode", True))
                self.append_log("설정이 불러와졌습니다.")
            else:
                self.append_log("저장된 설정 파일이 없습니다.")
        except Exception as e:
            self.append_log(f"설정 불러오기 오류: {e}")

    def show_easter_egg(self):
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
            self.extract_button.setEnabled(True)

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
        model_mapping = {
            "Gemini 2.5 Pro Experimental": "gemini-2.5-pro-exp-03-25",
            "Gemini 2.0 Flash": "gemini-2.0-flash",
            "Gemini 1.5 Pro": "gemini-1.5-pro"
        }
        selected_model = self.model_combobox.currentText().strip()
        gemini_model = model_mapping.get(selected_model, selected_model)
        chunk_size = self.chunk_spinbox.value()
        custom_prompt = self.prompt_text.toPlainText().strip() or ''
        delay = self.delay_spinbox.value()
        dual_language = self.dual_language_checkbox.isChecked()
        complete_mode = self.completion_mode_checkbox.isChecked()
        dir_name = os.path.dirname(self.input_path)
        base_name = os.path.splitext(os.path.basename(self.input_path))[0]
        self.output_path = os.path.join(dir_name, base_name + "_translated.epub")

        # --- New feature: Read proper noun CSV ---
        pn_csv_path = os.path.join(dir_name, base_name + "_proper_nouns.csv")
        proper_nouns = None
        if os.path.exists(pn_csv_path):
            proper_nouns = {}
            try:
                with open(pn_csv_path, "r", newline="", encoding="utf-8-sig") as csvfile:
                    reader = csv.reader(csvfile)
                    header = next(reader, None)  # Skip header if exists
                    for row in reader:
                        if len(row) >= 3 and row[2].strip().lower() == 'y':
                            proper_nouns[row[0]] = row[1]
            except Exception as e:
                self.append_log(f"Proper noun CSV 읽기 오류: {e}")
        # --- End new feature ---

        self.translate_button.setEnabled(False)
        self.select_button.setEnabled(False)
        self.extract_button.setEnabled(False)
        self.append_log("번역을 시작합니다...")
        self.update_progress(0)
        self.worker = TranslationWorker(
            input_path=self.input_path,
            output_path=self.output_path,
            max_concurrent=max_concurrent,
            gemini_model=gemini_model,
            chunk_size=chunk_size,
            custom_prompt=custom_prompt,
            api_key=api_key,
            delay=delay,
            dual_language=dual_language,
            complete_mode=complete_mode,
            proper_nouns=proper_nouns  # Pass proper nouns dictionary (or None)
        )
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.translation_finished)
        self.worker.start()

    def start_extraction(self):
        if not self.input_path:
            self.append_log("먼저 EPUB 파일을 선택해 주세요!")
            return
        api_key = self.api_entry.text().strip()
        if not api_key:
            self.append_log("API Key를 입력해 주세요!")
            return
        model_mapping = {
            "Gemini 2.5 Pro Experimental": "gemini-2.5-pro-exp-03-25",
            "Gemini 2.0 Flash": "gemini-2.0-flash",
            "Gemini 1.5 Pro": "gemini-1.5-pro"
        }
        selected_model = self.model_combobox.currentText().strip()
        gemini_model = model_mapping.get(selected_model, selected_model)
        base_name = os.path.splitext(os.path.basename(self.input_path))[0]
        self.output_path = os.path.join(os.path.dirname(self.input_path), base_name + "_proper_nouns.csv")
        self.translate_button.setEnabled(False)
        self.extract_button.setEnabled(False)
        self.select_button.setEnabled(False)
        self.append_log("고유명사 추출을 시작합니다...")
        self.update_progress(0)
        self.extraction_worker = ExtractionWorker(
            input_path=self.input_path,
            output_path=self.output_path,
            api_key=api_key,
            gemini_model=gemini_model,
            delay=self.delay_spinbox.value()
        )
        self.extraction_worker.progress_signal.connect(self.update_progress)
        self.extraction_worker.log_signal.connect(self.append_log)
        self.extraction_worker.finished_signal.connect(self.extraction_finished)
        self.extraction_worker.start()

    @pyqtSlot(str)
    def translation_finished(self, output_path):
        if output_path:
            self.append_log(f"번역 완료! 파일: {output_path}")
        else:
            self.append_log("번역 실패!")
        self.translate_button.setEnabled(True)
        self.extract_button.setEnabled(True)
        self.select_button.setEnabled(True)

    @pyqtSlot(str)
    def extraction_finished(self, output_path):
        if output_path:
            self.append_log(f"고유명사 추출 완료! 파일: {output_path}")
        else:
            self.append_log("고유명사 추출 실패!")
        self.translate_button.setEnabled(True)
        self.extract_button.setEnabled(True)
        self.select_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranslatorGUI()
    window.show()
    sys.exit(app.exec_())
