from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTextEdit, QLabel, QComboBox, QFileDialog, QSplitter
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

class TranslatorGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("📖 EPUB 번역기")
        self.setMinimumSize(800, 600)
        self.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                font-family: Consolas;
                font-size: 14px;
            }
            QComboBox {
                padding: 5px;
                border-radius: 5px;
            }
        """)
        self.setup_ui()

    def setup_ui(self):
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        # 상단 버튼 바
        button_layout = QHBoxLayout()
        self.open_button = QPushButton("열기")
        self.translate_button = QPushButton("번역 시작")
        self.save_button = QPushButton("저장")
        button_layout.addWidget(self.open_button)
        button_layout.addWidget(self.translate_button)
        button_layout.addWidget(self.save_button)
        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        # 중앙 텍스트 뷰어 (Split View)
        self.original_text = QTextEdit()
        self.original_text.setPlaceholderText("EPUB 원본 내용")
        self.translated_text = QTextEdit()
        self.translated_text.setPlaceholderText("번역된 텍스트 결과")

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.original_text)
        splitter.addWidget(self.translated_text)
        splitter.setSizes([400, 400])
        main_layout.addWidget(splitter)

        # 하단 설정
        bottom_layout = QHBoxLayout()
        engine_label = QLabel("번역 엔진:")
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["DeepL", "Google", "Gemini"])
        bottom_layout.addWidget(engine_label)
        bottom_layout.addWidget(self.engine_combo)
        bottom_layout.addStretch()
        main_layout.addLayout(bottom_layout)

        self.setCentralWidget(main_widget)

        # 연결
        self.open_button.clicked.connect(self.load_epub)
        self.translate_button.clicked.connect(self.translate_text)

    def load_epub(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "EPUB 파일 열기", "", "EPUB Files (*.epub)")
        if file_path:
            self.original_text.setText(f"✅ EPUB 불러옴: {file_path}")
            # 여기에 실제 EPUB 파싱 로직 추가 가능

    def translate_text(self):
        origin = self.original_text.toPlainText()
        if origin:
            # 임시 번역 예시
            self.translated_text.setText("🔄 번역된 결과:\n\n" + origin.replace("일본어", "한국어"))
        else:
            self.translated_text.setText("❗ 원본이 비어 있습니다.")

if __name__ == "__main__":
    app = QApplication([])
    window = TranslatorGUI()
    window.show()
    app.exec()
