import os
import textwrap
import csv
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog,
    QGraphicsDropShadowEffect, QProgressBar, QTextEdit, QLabel, QMessageBox, QSpacerItem, QSizePolicy, QFrame
)
from PyQt5.QtGui import QIcon, QDesktopServices, QFont
from PyQt5.QtCore import QSize, QUrl, Qt, pyqtSlot
from gui.dialogs import EasterEggDialog, AdvancedSettingsDialog, CSVEditorDialog
from gui.customs import RotatingButton

# Import the worker classes from the original translator GUI
from gui.workers import TranslationWorker, ExtractionWorker, RubyRemoverWorker, TocTranslationWorker, CompletionTranslationWorker, ImageAnnotationWorker

class MainWindow(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings  # Loaded from settings.py
        self.epub_file = None  # To store the selected EPUB file path
        self.translation_worker = None
        self.extraction_worker = None
        self.csv_path = None
        self.setWindowTitle("Sea Marine Epub 번역기")
        self.initUI()

    def initUI(self):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.setStyleSheet("background-color: #cbcbcb;")
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        button_layout = QHBoxLayout()
        button_layout.setSpacing(20)

        # 1. Easter Egg Button
        easter_egg_button_layout = QVBoxLayout()
        easter_egg_spacer = QSpacerItem(50, 70, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.easter_egg_button = RotatingButton("?")
        self.easter_egg_button.setMinimumSize(50, 50)
        self.easter_egg_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 25px;
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f7f7f7, stop:1 #eaeaea
                );
                color: #333;
                font-size: 10px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #eaeaea, stop:1 #dedede
                );
            }
        """)
        self.add_drop_shadow(self.easter_egg_button)
        easter_egg_button_layout.addItem(easter_egg_spacer)
        easter_egg_button_layout.addWidget(self.easter_egg_button)
        button_layout.addLayout(easter_egg_button_layout)

        self.easter_egg_button.clicked.connect(self.show_easter_egg)

        # 2. Advanced Settings Button
        advanced_setting_button_layout = QVBoxLayout()
        advanced_setting_spacer = QSpacerItem(60, 60, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.advanced_setting_button = RotatingButton("고급 설정")
        self.advanced_setting_button.setMinimumSize(60, 60)
        self.advanced_setting_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 30px;
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f7f7f7, stop:1 #eaeaea
                );
                color: #333;
                font-size: 11px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #eaeaea, stop:1 #dedede
                );
            }
        """)
        self.add_drop_shadow(self.advanced_setting_button)
        advanced_setting_button_layout.addItem(advanced_setting_spacer)
        advanced_setting_button_layout.addWidget(self.advanced_setting_button)
        button_layout.addLayout(advanced_setting_button_layout)

        self.advanced_setting_button.clicked.connect(self.show_advanced_setting)

        # 3. File Selection Button
        file_select_button_layout = QVBoxLayout()
        file_select_spacer = QSpacerItem(70, 50, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.file_select_button = QPushButton("파일 선택")
        self.file_select_button.setMinimumSize(70, 70)
        self.file_select_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 35px;
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f7f7f7, stop:1 #eaeaea
                );
                color: #333;
                font-size: 12px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #eaeaea, stop:1 #dedede
                );
            }
        """)
        self.add_drop_shadow(self.file_select_button)
        file_select_button_layout.addItem(file_select_spacer)
        file_select_button_layout.addWidget(self.file_select_button)
        button_layout.addLayout(file_select_button_layout)

        self.file_select_button.clicked.connect(self.select_epub)

        # 4. Remove Ruby Button
        remove_ruby_button_layout = QVBoxLayout()
        remove_ruby_spacer = QSpacerItem(80, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.remove_ruby_button = RotatingButton("루비 제거")
        self.remove_ruby_button.setMinimumSize(80, 80)
        self.remove_ruby_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 40px;
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f7f7f7, stop:1 #eaeaea
                );
                color: #333;
                font-size: 13px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #eaeaea, stop:1 #dedede
                );
            }
        """)
        self.add_drop_shadow(self.remove_ruby_button)
        remove_ruby_button_layout.addItem(remove_ruby_spacer)
        remove_ruby_button_layout.addWidget(self.remove_ruby_button)
        button_layout.addLayout(remove_ruby_button_layout)

        self.remove_ruby_button.clicked.connect(lambda: self.remove_ruby(self.epub_file))

        # 5. Extract Proper Nouns Button
        extract_pn_button_layout = QVBoxLayout()
        extract_pn_spacer = QSpacerItem(90, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.extract_pn_button = RotatingButton("고유명사\n추출")
        self.extract_pn_button.setMinimumSize(90, 90)
        self.extract_pn_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 45px;
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f7f7f7, stop:1 #eaeaea
                );
                color: #333;
                font-size: 14px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #eaeaea, stop:1 #dedede
                );
            }
        """)
        self.add_drop_shadow(self.extract_pn_button)
        extract_pn_button_layout.addItem(extract_pn_spacer)
        extract_pn_button_layout.addWidget(self.extract_pn_button)
        button_layout.addLayout(extract_pn_button_layout)

        self.extract_pn_button.clicked.connect(self.start_extraction)

        # 6. Edit Proper Nouns Button
        edit_pn_dict_button_layout = QVBoxLayout()
        edit_pn_dict_spacer = QSpacerItem(100, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.edit_pn_dict_button = RotatingButton("고유명사\n사전 수정")
        self.edit_pn_dict_button.setMinimumSize(100, 100)
        self.edit_pn_dict_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 50px;
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f7f7f7, stop:1 #eaeaea
                );
                color: #333;
                font-size: 15px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #eaeaea, stop:1 #dedede
                );
            }
        """)
        self.add_drop_shadow(self.edit_pn_dict_button)
        edit_pn_dict_button_layout.addItem(edit_pn_dict_spacer)
        edit_pn_dict_button_layout.addWidget(self.edit_pn_dict_button)
        button_layout.addLayout(edit_pn_dict_button_layout)

        self.edit_pn_dict_button.clicked.connect(self.show_pn_dictionary)

        # 7. Translate Button
        translate_button_layout = QVBoxLayout()
        translate_spacer = QSpacerItem(120, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.translate_button = RotatingButton("번역 실행")
        self.translate_button.setMinimumSize(120, 120)
        self.translate_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 60px;
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f7f7f7, stop:1 #eaeaea
                );
                color: #333;
                font-size: 18px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #eaeaea, stop:1 #dedede
                );
            }
        """)
        self.add_drop_shadow(self.translate_button)
        translate_button_layout.addItem(translate_spacer)
        translate_button_layout.addWidget(self.translate_button)
        button_layout.addLayout(translate_button_layout)

        self.translate_button.clicked.connect(self.start_translation)

        button_layout2 = QHBoxLayout()
        button_layout2.setSpacing(20)

        # 8. Spacer
        button_layout2_spacer = QSpacerItem(350, 120, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        button_layout2.addItem(button_layout2_spacer)

        # 9. Annoate Image Button
        annotate_image_button_layout = QVBoxLayout()
        annotate_image_spacer = QSpacerItem(90, 30, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.annotate_image_button = RotatingButton("이미지\n주석")
        self.annotate_image_button.setMinimumSize(90, 90)
        self.annotate_image_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 45px;
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f7f7f7, stop:1 #eaeaea
                );
                color: #333;
                font-size: 13px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #eaeaea, stop:1 #dedede
                );
            }
        """)
        self.add_drop_shadow(self.annotate_image_button)
        annotate_image_button_layout.addItem(annotate_image_spacer)
        annotate_image_button_layout.addWidget(self.annotate_image_button)
        button_layout2.addLayout(annotate_image_button_layout)

        self.annotate_image_button.clicked.connect(self.start_image_annotation)

        # 10. Proofreading Button
        proofreading_button_layout = QVBoxLayout()
        proofreading_spacer = QSpacerItem(100, 20, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.proofreading_button = RotatingButton("검수 진행")
        self.proofreading_button.setMinimumSize(100, 100)
        self.proofreading_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 50px;
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f7f7f7, stop:1 #eaeaea
                );
                color: #333;
                font-size: 15px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #eaeaea, stop:1 #dedede
                );
            }
        """)
        self.add_drop_shadow(self.proofreading_button)
        proofreading_button_layout.addItem(proofreading_spacer)
        proofreading_button_layout.addWidget(self.proofreading_button)
        button_layout2.addLayout(proofreading_button_layout)

        self.proofreading_button.clicked.connect(self.start_completion_translation)

        # 11. Translate Title/Toc Button
        translate_toc_button_layout = QVBoxLayout()
        translate_toc_spacer = QSpacerItem(120, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
        self.translate_toc_button = RotatingButton("제목/목차\n번역")
        self.translate_toc_button.setMinimumSize(120, 120)
        self.translate_toc_button.setStyleSheet("""
            QPushButton {
                border: none;
                border-radius: 60px;
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #f7f7f7, stop:1 #eaeaea
                );
                color: #333;
                font-size: 15px;
                padding: 0px;
            }
            QPushButton:hover {
                background-color: qlineargradient(
                    spread:pad, x1:0, y1:0, x2:0, y2:1,
                    stop:0 #eaeaea, stop:1 #dedede
                );
            }
        """)
        self.add_drop_shadow(self.translate_toc_button)
        translate_toc_button_layout.addItem(translate_toc_spacer)
        translate_toc_button_layout.addWidget(self.translate_toc_button)
        button_layout2.addLayout(translate_toc_button_layout)

        self.translate_toc_button.clicked.connect(self.start_toc_translation)

        main_layout.addLayout(button_layout)
        main_layout.addLayout(button_layout2)

        # Frame for buttons
        black_bar = QFrame()
        black_bar.setFrameShape(QFrame.Shape.NoFrame)
        black_bar.setFixedHeight(4)
        black_bar.setStyleSheet("background-color: #5d7091;")
        self.add_drop_shadow(black_bar)

        main_layout.addWidget(black_bar)

        # Selected File Indicator
        self.file_label = QLabel()
        self.file_label.setText("선택된 파일이 없습니다.")
        self.file_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.file_label.setFixedHeight(24)  # 한 줄 텍스트 라벨 높이
        self.file_label.setStyleSheet("""
            QLabel {
                font-family: 'Segoe UI', 'Malgun Gothic', 'Helvetica Neue', sans-serif;
                font-size: 8pt;
                color: #333;
                padding: 4px 8px;
                border: 1px solid #ccc;
                border-radius: 6px;
                background-color: #dedede;
            }
        """)
        self.file_label.setWordWrap(False)
        self.file_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.file_label.setToolTip("여기에 선택된 파일명이 표시됩니다.")
        self.file_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        main_layout.addWidget(self.file_label)

        # Log Text Box
        self.log_text_box = QTextEdit()
        self.log_text_box.setReadOnly(True)
        self.log_text_box.setStyleSheet("""
            QTextEdit {
                background-color: #f7f7f7;
                color: #333;
                border: 1px solid #dedede;
                border-radius: 10px;
                padding: 4px;
            }
        """)
        self.log_text_box.setMinimumHeight(100)
        main_layout.addWidget(self.log_text_box)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #eaeaea;
                border: none;
                border-radius: 10px;
                text-align: center;
                color: #333;
            }
            QProgressBar::chunk {
                background-color: #5d7091;
                border-radius: 10px;
            }
        """)
        self.add_drop_shadow(self.progress_bar)
        main_layout.addWidget(self.progress_bar)

        # Version Label
        version_label = QLabel("Version: 1.3.0")
        version_label.setAlignment(Qt.AlignCenter)
        version_label.setStyleSheet("color: #f7f7f7; font-size: 12px;")
        main_layout.addWidget(version_label)

        self.setLayout(main_layout)

    def add_drop_shadow(self, widget):
        from PyQt5.QtWidgets import QGraphicsDropShadowEffect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setOffset(2, 2)
        shadow.setColor(Qt.black)
        widget.setGraphicsEffect(shadow)
    
    def buttons_setEnabled(self, enabled):
        self.remove_ruby_button.setEnabled(enabled)
        self.extract_pn_button.setEnabled(enabled)
        self.edit_pn_dict_button.setEnabled(enabled)
        self.translate_button.setEnabled(enabled)
        self.proofreading_button.setEnabled(enabled)
        self.translate_toc_button.setEnabled(enabled)
        self.annotate_image_button.setEnabled(enabled)

    def select_epub(self):
        from PyQt5.QtWidgets import QFileDialog
        file_dialog = QFileDialog(self, "번역할 EPUB 파일 선택", "", "EPUB Files (*.epub)")
        file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        file_dialog.setStyleSheet("QWidget { background-color: #f7f7f7; color: #333; }")
        if file_dialog.exec_():
            file_path = file_dialog.selectedFiles()[0]
            if file_path:
                self.epub_file = file_path
                file_name = os.path.basename(file_path)
                wrapped_file_name = "\n".join(textwrap.wrap(file_name, width=100))
                self.file_label.setText(f"선택된 EPUB 파일: {wrapped_file_name}")
                self.file_label.setToolTip(file_path)
                self.log_text_box.append(f"선택된 EPUB 파일: {file_path}")
                self.csv_path = os.path.join(os.path.dirname(file_path), os.path.splitext(file_name)[0] + "_proper_nouns.csv")
                self.log_text_box.append(f"CSV 파일 경로: {self.csv_path}")

    def show_advanced_setting(self):
        dialog = AdvancedSettingsDialog(self.settings)
        self.advanced_setting_button.start_animation()
        dialog.exec_()
        self.advanced_setting_button.stop_animation()

    def start_toc_translation(self):
        if not self.epub_file:
            self.log_text_box.append("EPUB 파일을 선택하세요.")
            return
        
        dir_name = os.path.dirname(self.epub_file)
        base_name = os.path.splitext(os.path.basename(self.epub_file))[0]
        pn_csv_path = os.path.join(dir_name, base_name + "_proper_nouns.csv")

        try:
            if os.path.exists(pn_csv_path):
                proper_nouns = self.load_proper_nouns(pn_csv_path)
            else:
                proper_nouns = None

            self.toc_translation_worker = TocTranslationWorker(
                input_path=self.epub_file,
                output_path=self.epub_file,
                max_concurrent=1,
                gemini_model=self.settings.get("gemini_model", "gemini-2.0-flash"),
                chunk_size=1500,
                custom_prompt="",
                api_key=self.settings.get("api_key", "").strip(),
                delay=self.settings.get("request_delay", 0),
                dual_language_mode=False,
                completion_mode=False,
                proper_nouns=proper_nouns
            )
            self.toc_translation_worker.progress_signal.connect(self.update_progress)
            self.toc_translation_worker.log_signal.connect(self.log_text_box.append)
            self.toc_translation_worker.finished_signal.connect(self.toc_translation_finished)
            self.translate_toc_button.start_animation()
            self.buttons_setEnabled(False)
            self.toc_translation_worker.start()
        except Exception as e:
            self.log_text_box.append(f"번역 중 오류 발생: {e}")
            self.translate_toc_button.stop_animation()
            self.buttons_setEnabled(True)
            return
        
    def start_completion_translation(self):
        if not self.epub_file:
            self.log_text_box.append("EPUB 파일을 선택하세요.")
            return
        
        dir_name = os.path.dirname(self.epub_file)
        base_name = os.path.splitext(os.path.basename(self.epub_file))[0]
        pn_csv_path = os.path.join(dir_name, base_name + "_proper_nouns.csv")

        try:
            if os.path.exists(pn_csv_path):
                proper_nouns = self.load_proper_nouns(pn_csv_path)
            else:
                proper_nouns = None

            self.completion_translation_worker = CompletionTranslationWorker(
                input_path=self.epub_file,
                output_path=self.epub_file,
                max_concurrent=1,
                gemini_model=self.settings.get("gemini_model", "gemini-2.0-flash"),
                chunk_size=1500,
                custom_prompt="",
                api_key=self.settings.get("api_key", "").strip(),
                delay=self.settings.get("request_delay", 0),
                dual_language_mode=False,
                completion_mode=False,
                proper_nouns=proper_nouns
            )
            self.completion_translation_worker.progress_signal.connect(self.update_progress)
            self.completion_translation_worker.log_signal.connect(self.log_text_box.append)
            self.completion_translation_worker.finished_signal.connect(self.completion_translation_finished)
            self.proofreading_button.start_animation()
            self.buttons_setEnabled(False)
            self.completion_translation_worker.start()
        except Exception as e:
            self.log_text_box.append(f"번역 중 오류 발생: {e}")
            self.proofreading_button.stop_animation()
            self.buttons_setEnabled(True)
            return

    def start_image_annotation(self):
        if not self.epub_file:
            self.log_text_box.append("EPUB 파일을 선택하세요.")
            return
        
        dir_name = os.path.dirname(self.epub_file)
        base_name = os.path.splitext(os.path.basename(self.epub_file))[0]
        pn_csv_path = os.path.join(dir_name, base_name + "_proper_nouns.csv")

        try:
            if os.path.exists(pn_csv_path):
                proper_nouns = self.load_proper_nouns(pn_csv_path)
            else:
                proper_nouns = None

            self.completion_translation_worker = ImageAnnotationWorker(
                input_path=self.epub_file,
                output_path=self.epub_file,
                max_concurrent=1,
                gemini_model=self.settings.get("gemini_model", "gemini-2.0-flash"),
                chunk_size=1500,
                custom_prompt="",
                api_key=self.settings.get("api_key", "").strip(),
                delay=self.settings.get("request_delay", 0),
                dual_language_mode=False,
                completion_mode=False,
                proper_nouns=proper_nouns
            )
            self.completion_translation_worker.progress_signal.connect(self.update_progress)
            self.completion_translation_worker.log_signal.connect(self.log_text_box.append)
            self.completion_translation_worker.finished_signal.connect(self.image_annotation_finished)
            self.annotate_image_button.start_animation()
            self.buttons_setEnabled(False)
            self.completion_translation_worker.start()
        except Exception as e:
            self.log_text_box.append(f"번역 중 오류 발생: {e}")
            self.annotate_image_button.stop_animation()
            self.buttons_setEnabled(True)
            return


    def start_extraction(self):
        if not self.epub_file:
            self.append_log("먼저 파일을 선택해 주세요!")
            return
        
        dir_name = os.path.dirname(self.epub_file)
        base_name = os.path.splitext(os.path.basename(self.epub_file))[0]
        pn_csv_path = os.path.join(dir_name, base_name + "_proper_nouns.csv")

        try:
            if os.path.exists(pn_csv_path):
                reply = QMessageBox.question(
                    self,
                    "도우미",
                    f"'{os.path.basename(pn_csv_path)}' 이미 고유명사 사전 파일이 존재합니다.\n고유명사를 재추출하시겠습니까? 기존 사전은 삭제됩니다.",
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply == QMessageBox.Yes:
                    self.extraction_worker = ExtractionWorker(
                        input_path=self.epub_file,
                        output_path=pn_csv_path,
                        api_key=self.settings.get("api_key", "").strip(),
                        gemini_model=self.settings.get("gemini_model", "gemini-2.0-flash"),
                        delay=self.settings.get("request_delay", 0),
                        max_concurrent_requests=self.settings.get("max_concurrent_requests", 1)
                    )
                    self.extraction_worker.progress_signal.connect(self.update_progress)
                    self.extraction_worker.log_signal.connect(self.log_text_box.append)
                    self.extraction_worker.finished_signal.connect(self.extraction_finished)
                    self.extract_pn_button.start_animation()
                    self.buttons_setEnabled(False)
                    self.extraction_worker.start()
                else:
                    self.log_text_box.append("고유명사 추출을 취소하였습니다.")
                    self.extract_pn_button.stop_animation()
                    return
            else:
                self.extraction_worker = ExtractionWorker(
                    input_path=self.epub_file,
                    output_path=pn_csv_path,
                    api_key=self.settings.get("api_key", "").strip(),
                    gemini_model=self.settings.get("gemini_model", "gemini-2.0-flash"),
                    delay=self.settings.get("request_delay", 0),
                    max_concurrent_requests=self.settings.get("max_concurrent_requests", 1)
                )
                self.extraction_worker.progress_signal.connect(self.update_progress)
                self.extraction_worker.log_signal.connect(self.log_text_box.append)
                self.extraction_worker.finished_signal.connect(self.extraction_finished)
                self.extract_pn_button.start_animation()
                self.buttons_setEnabled(False)
                self.extraction_worker.start()
        except Exception as e:
            self.log_text_box.append(f"고유명사 추출에 실패하였습니다, 에러: {e}")
            self.extract_pn_button.stop_animation()
            self.buttons_setEnabled(True)
            return
            
    
    @pyqtSlot(str)
    def extraction_finished(self, output):
        self.log_text_box.append(f"고유명사 추출을 완료하였습니다, 저장 위치: {output}")
        self.csv_path = output
        self.extract_pn_button.stop_animation()
        self.buttons_setEnabled(True)
    @pyqtSlot(str)
    def ruby_removal_finished(self, output):
        self.log_text_box.append(f"루비문자 제거를 완료하였습니다, 저장 위치: {output}")
        self.remove_ruby_button.stop_animation()
        self.buttons_setEnabled(True)
    @pyqtSlot(str)
    def translation_finished(self, output_path):
        if output_path:
            self.log_text_box.append(f"번역 완료! 파일: {output_path}")
        else:
            self.log_text_box.append("번역 실패!")
        # Re-enable buttons after processing
        self.epub_file = output_path
        self.epub_file = output_path
        file_name = os.path.basename(output_path)
        wrapped_file_name = "\n".join(textwrap.wrap(file_name, width=100))
        self.file_label.setText(f"선택된 EPUB 파일: {wrapped_file_name}")
        self.file_label.setToolTip(output_path)
        self.log_text_box.append(f"선택된 EPUB 파일: {output_path}")
        self.translate_button.stop_animation()
        self.buttons_setEnabled(True)
    @pyqtSlot(str)
    def toc_translation_finished(self, output_path):
        if output_path:
            self.log_text_box.append(f"목차 번역 완료! 파일: {output_path}")
        else:
            self.log_text_box.append("목차 번역 실패!")
        # Re-enable buttons after processing
        self.translate_toc_button.stop_animation()
        self.buttons_setEnabled(True)
    @pyqtSlot(str)
    def completion_translation_finished(self, output_path):
        if output_path:
            self.log_text_box.append(f"검수 번역 완료! 파일: {output_path}")
        else:
            self.log_text_box.append("검수 번역 실패!")
        # Re-enable buttons after processing
        self.proofreading_button.stop_animation()
        self.buttons_setEnabled(True)
    @pyqtSlot(str)
    def image_annotation_finished(self, output_path):
        if output_path:
            self.log_text_box.append(f"이미지 주석 완료! 파일: {output_path}")
        else:
            self.log_text_box.append("이미지 주석 실패!")
        # Re-enable buttons after processing
        self.annotate_image_button.stop_animation()
        self.buttons_setEnabled(True)


    # ------------------- New Merged Start Translation Logic ------------------- #

    def start_translation(self):
        if not self.epub_file:
            self.log_text_box.append("EPUB 파일을 선택하세요.")
            return
        
        api_key = self.settings.get("api_key", "").strip()
        max_concurrent = self.settings.get("max_concurrent_requests", 1)
        gemini_model = self.settings.get("gemini_model", "gemini-2.0-flash")
        chunk_size = self.settings.get("chunk_size", 1500)
        custom_prompt = self.settings.get("custom_prompt", "")
        dual_language_mode = self.settings.get("dual_language_mode", False)
        completion_mode = self.settings.get("completion_mode", False)
        delay = self.settings.get("request_delay", 0)
        image_annotation_mode = self.settings.get("image_annotation_mode", False)
        dir_name = os.path.dirname(self.epub_file)
        base_name = os.path.splitext(os.path.basename(self.epub_file))[0]
        self.output_path = os.path.join(dir_name, base_name + "_translated.epub")
        
        if not api_key:
            self.log_text_box.append("API 키가 설정되어 있지 않습니다.")
            return
        
        pn_csv_path = os.path.join(dir_name, base_name + "_proper_nouns.csv")
        proper_nouns = None
        if os.path.exists(pn_csv_path):
            proper_nouns = {}
            try:
                with open(pn_csv_path, "r", newline="", encoding="utf-8-sig") as csvfile:
                    reader = csv.reader(csvfile)
                    header = next(reader, None)  # Skip header if exists
                    for row in reader:
                        proper_nouns[row[0]] = row[1]
            except Exception as e:
                self.log_text_box.append(f"Proper noun CSV 읽기 오류: {e}")

        self.translate_button.start_animation()
        self.buttons_setEnabled(False)

        try:
            self.log_text_box.append("번역을 시작합니다...")
            self.update_progress(0)
            self.worker = TranslationWorker(
                input_path=self.epub_file,
                output_path=self.output_path,
                max_concurrent=max_concurrent,
                gemini_model=gemini_model,
                chunk_size=chunk_size,
                custom_prompt=custom_prompt,
                api_key=api_key,
                delay=delay,
                dual_language_mode=dual_language_mode,
                completion_mode=completion_mode,
                proper_nouns=proper_nouns,
                image_annotation_mode=image_annotation_mode
            )
            self.worker.progress_signal.connect(self.update_progress)
            self.worker.log_signal.connect(self.log_text_box.append)
            self.worker.finished_signal.connect(self.translation_finished)
            self.worker.start()
        except Exception as e:
            self.log_text_box.append(f"번역 중 오류 발생: {e}")
            self.translate_button.stop_animation()
            self.buttons_setEnabled(True)

    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def remove_ruby(self, input_path):
        if input_path == None or input_path == '':
            self.log_text_box.append("먼저 파일을 선택해주세요.")
            return
        if not os.path.exists(input_path):
            self.log_text_box.append("선택한 파일이 존재하지 않습니다.")
            return
        try:
            self.ruby_remover_worker = RubyRemoverWorker(input_path)
            self.ruby_remover_worker.progress_signal.connect(self.update_progress)
            self.ruby_remover_worker.log_signal.connect(self.log_text_box.append)
            self.ruby_remover_worker.finished_signal.connect(self.ruby_removal_finished)
            self.remove_ruby_button.start_animation()
            self.buttons_setEnabled(False)
            self.ruby_remover_worker.start()
        except Exception as e:
            self.log_text_box(f"루비문자 제거에 실패하였습니다, 에러: {e}")
            self.remove_ruby_button.stop_animation()
            self.buttons_setEnabled(True)


    def load_proper_nouns(self, csv_path):
        proper_nouns = {}
        try:
            with open(csv_path, "r", newline="", encoding="utf-8-sig") as csvfile:
                reader = csv.reader(csvfile)
                header = next(reader, None)  # Skip header if exists
                for row in reader:
                    if len(row) >= 3 and row[2].strip().lower() == 'y':
                        proper_nouns[row[0]] = row[1]
        except Exception as e:
            self.log_text_box.append(f"Proper noun CSV 읽기 오류: {e}")
        return proper_nouns

    def after_extraction(self, csv_path, run_translation_callback):
        # Extraction 완료 후 proper noun 사전 수정 여부를 묻습니다.
        self.ask_use_dictionary(csv_path, run_translation_callback)

    def show_pn_dictionary(self):
        csv_path = self.csv_path

        if not csv_path or not os.path.exists(csv_path):
            self.log_text_box.append("해당 파일에는 고유명사 사전이 생성되지 않았습니다. 먼저 고유명사 추출을 통해 사전을 생성해주세요.")
            return

        self.edit_pn_dict_button.start_animation()
        reply = QMessageBox.question(
            self,
            "도우미",
            "Yes 버튼을 눌러 사전을 열고, No 버튼으로 취소합니다.\n일-한 번역이 어색한 경우 번역을 수정하거나 열을 삭제 하십시오.\n수정의 경우 일어, 한어 양쪽 다 가능합니다.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            dialog = CSVEditorDialog(csv_path)
            dialog.exec_()
            self.log_text_box.append("고유명사 사전 수정을 완료했습니다.")
        else:
            self.log_text_box.append("고유명사 사전 수정을 취소합니다.")

        self.edit_pn_dict_button.stop_animation()

    def ask_use_dictionary(self, csv_path, run_translation_callback):
        # 먼저 사전을 수정할 것인지 묻습니다.
        reply = QMessageBox.question(
            self,
            "고유명사 수정",
            "고유명사 추출이 완료되었습니다.\n고유명사 사전을 수정하시겠습니까?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            # 사용자의 기본 CSV 편집 프로그램으로 파일 열기
            QDesktopServices.openUrl(QUrl.fromLocalFile(csv_path))
            # 사용자가 수정을 완료했는지 확인하는 메시지 박스
            confirm = QMessageBox.question(
                self,
                "수정 완료 확인",
                "수정이 완료되었으면 'Yes'를 눌러 번역을 시작하세요.",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm == QMessageBox.Yes:
                proper_nouns = self.load_proper_nouns(csv_path)
                run_translation_callback(proper_nouns)
            else:
                # 만약 사용자가 수정 완료를 확인하지 않으면, 사전을 사용하지 않고 진행합니다.
                return
        else:
            # 수정하지 않고 기존 사전을 그대로 사용합니다.
            proper_nouns = self.load_proper_nouns(csv_path)
            run_translation_callback(proper_nouns)

    def easter_egg(self):
        self.log_text_box.append("Easter Egg button clicked!")

    def show_easter_egg(self):
        dialog = EasterEggDialog()
        self.easter_egg_button.start_animation()
        dialog.exec_()
        self.easter_egg_button.stop_animation()
        
    def open_proper_noun_csv(self):
        if self.epub_file:
            dir_name = os.path.dirname(self.epub_file)
            base_name = os.path.splitext(os.path.basename(self.epub_file))[0]
            pn_csv_path = os.path.join(dir_name, base_name + "_proper_nouns.csv")
            if os.path.exists(pn_csv_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(pn_csv_path))
            else:
                QMessageBox.warning(self, "Warning", "No proper noun CSV file found.")
