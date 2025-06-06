import os
import csv
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, QHBoxLayout, QMessageBox, QComboBox, QCheckBox, QTextEdit, QGroupBox, QTableWidget, QTableWidgetItem, QFileDialog
)
from PyQt5.QtCore import QUrl, Qt
from PyQt5.QtGui import QDesktopServices, QIntValidator, QDoubleValidator, QPixmap
from settings import save_settings
from utils import check_api_key

class CSVEditorDialog(QDialog):
    def __init__(self, csv_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("고유명사 사전 편집")
        self.resize(800, 500)

        self.csv_path = csv_path

        # 테이블
        self.table = QTableWidget()

        # 버튼들
        self.add_row_btn = QPushButton("행 추가")
        self.delete_row_btn = QPushButton("행 삭제")
        self.save_btn = QPushButton("저장")

        # 버튼 레이아웃
        button_layout = QHBoxLayout()
        button_layout.addWidget(self.add_row_btn)
        button_layout.addWidget(self.delete_row_btn)
        button_layout.addWidget(self.save_btn)

        # 전체 레이아웃
        layout = QVBoxLayout(self)
        layout.addLayout(button_layout)
        layout.addWidget(self.table)

        self.load_csv(self.csv_path)

        # 버튼 연결
        self.add_row_btn.clicked.connect(self.add_row)
        self.delete_row_btn.clicked.connect(self.delete_selected_row)
        self.save_btn.clicked.connect(self.save_csv)

    def load_csv(self, path):
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)
            if not rows:
                return
            self.table.setRowCount(len(rows))
            self.table.setColumnCount(len(rows[0]))
            for r, row in enumerate(rows):
                for c, cell in enumerate(row):
                    self.table.setItem(r, c, QTableWidgetItem(cell))

    def add_row(self):
        current_rows = self.table.rowCount()
        self.table.setRowCount(current_rows + 1)
        for col in range(self.table.columnCount()):
            self.table.setItem(current_rows, col, QTableWidgetItem(""))

    def delete_selected_row(self):
        selected_ranges = self.table.selectedRanges()
        if not selected_ranges:
            QMessageBox.warning(self, "경고", "삭제할 행을 선택하세요.")
            return

        row_to_delete = selected_ranges[0].topRow()

        if row_to_delete == 0:
            QMessageBox.warning(self, "경고", "첫 번째 행(헤더)은 삭제할 수 없습니다.")
            return

        self.table.removeRow(row_to_delete)

    def save_csv(self):
        with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else "")
                writer.writerow(row_data)
        QMessageBox.information(self, "저장됨", "CSV 파일이 저장되었습니다.")

class EasterEggDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("시마 린 EPUB 번역기")
        self.setMaximumSize(250, 250)
        layout = QVBoxLayout(self)
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        jpg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                "very_important_folder", "very_important_file.jpg")
        if os.path.exists(jpg_path):
            pixmap = QPixmap(jpg_path)
            scaled = pixmap.scaled(250, 250, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.label.setPixmap(scaled)
        else:
            self.label.setText("파일을 찾을 수 없습니다.")

# --- API Key Entry Window (used for initial entry and via Advanced Settings) ---
# You may want to convert this to a QDialog for modal behavior.
# This dialog now also handles initial Vertex AI setup.
class APIKeyDialog(QDialog):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle("Sea Marine 인증 설정")
        self.initUI()
        self.toggle_auth_mode_ui() # Initial UI state based on settings

    def initUI(self):
        layout = QVBoxLayout()

        # --- Auth Mode Selection ---
        self.use_vertex_ai_checkbox = QCheckBox("Vertex AI 사용 (서비스 계정 또는 ADC)")
        self.use_vertex_ai_checkbox.setChecked(self.settings.get("use_vertex_ai", False))
        self.use_vertex_ai_checkbox.stateChanged.connect(self.toggle_auth_mode_ui)
        layout.addWidget(self.use_vertex_ai_checkbox)

        # --- API Key Group ---
        self.api_key_group = QGroupBox("Gemini API 키 설정")
        api_key_layout = QVBoxLayout()
        self.info_label = QLabel("Google Gemini API 키를 입력하세요:")
        api_key_layout.addWidget(self.info_label)
        self.api_key_input = QLineEdit(self.settings.get("api_key", ""))
        self.api_key_input.setPlaceholderText("여기에 API 키를 입력하세요")
        api_key_layout.addWidget(self.api_key_input)
        self.link_button = QPushButton("API 키 확인/발급 하러가기")
        self.link_button.clicked.connect(self.open_api_link)
        api_key_layout.addWidget(self.link_button)
        self.api_key_group.setLayout(api_key_layout)
        layout.addWidget(self.api_key_group)

        # --- Vertex AI Group ---
        self.vertex_ai_group = QGroupBox("Vertex AI 설정")
        vertex_ai_layout = QVBoxLayout()
        self.sa_json_path_label = QLabel("서비스 계정 JSON 파일 경로 (선택 사항):")
        vertex_ai_layout.addWidget(self.sa_json_path_label)
        sa_path_layout = QHBoxLayout()
        self.sa_json_path_input = QLineEdit(self.settings.get("service_account_json_path", ""))
        self.sa_json_path_input.setPlaceholderText("예: /path/to/your-service-account.json")
        sa_path_layout.addWidget(self.sa_json_path_input)
        self.sa_json_browse_button = QPushButton("찾아보기")
        self.sa_json_browse_button.clicked.connect(self.browse_sa_json)
        sa_path_layout.addWidget(self.sa_json_browse_button)
        vertex_ai_layout.addLayout(sa_path_layout)
        self.gcp_project_id_label = QLabel("GCP Project ID (필수):")
        vertex_ai_layout.addWidget(self.gcp_project_id_label)
        self.gcp_project_id_input = QLineEdit(self.settings.get("gcp_project_id", ""))
        self.gcp_project_id_input.setPlaceholderText("예: your-gcp-project-id")
        vertex_ai_layout.addWidget(self.gcp_project_id_input)
        self.gcp_location_label = QLabel("GCP Location (필수, 예: asia-northeast3):")
        vertex_ai_layout.addWidget(self.gcp_location_label)
        self.gcp_location_input = QLineEdit(self.settings.get("gcp_location", "asia-northeast3"))
        vertex_ai_layout.addWidget(self.gcp_location_input)
        self.vertex_ai_group.setLayout(vertex_ai_layout)
        layout.addWidget(self.vertex_ai_group)

        # --- Save Button ---
        self.save_button = QPushButton("설정 저장 및 계속")
        self.save_button.clicked.connect(self.save_configuration)
        layout.addWidget(self.save_button)

        self.setLayout(layout)

    def toggle_auth_mode_ui(self):
        use_vertex = self.use_vertex_ai_checkbox.isChecked()
        self.vertex_ai_group.setVisible(use_vertex)
        self.api_key_group.setVisible(not use_vertex)

    def browse_sa_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "서비스 계정 JSON 파일 선택", "", "JSON Files (*.json)")
        if path:
            self.sa_json_path_input.setText(path)

    def open_api_link(self):
        url = QUrl("https://aistudio.google.com/app/apikey")
        QDesktopServices.openUrl(url)

    def save_configuration(self):
        if self.use_vertex_ai_checkbox.isChecked():
            sa_path = self.sa_json_path_input.text().strip()
            project_id = self.gcp_project_id_input.text().strip()
            location = self.gcp_location_input.text().strip()

            if not project_id:
                QMessageBox.warning(self, "입력 오류", "Vertex AI 사용 시 GCP Project ID는 필수입니다.")
                return
            if not location:
                QMessageBox.warning(self, "입력 오류", "Vertex AI 사용 시 GCP Location은 필수입니다.")
                return

            self.settings["use_vertex_ai"] = True
            self.settings["service_account_json_path"] = sa_path
            self.settings["gcp_project_id"] = project_id
            self.settings["gcp_location"] = location
            # self.settings["api_key"] = "" # Clear API key if Vertex AI is chosen
            QMessageBox.information(self, "Vertex AI 설정 저장됨", "Vertex AI 설정이 저장되었습니다.")
            self.accept()
        else:
            entered_key = self.api_key_input.text().strip()
            if not entered_key:
                QMessageBox.warning(self, "입력 오류", "API 키를 입력해주세요.")
                return
            if check_api_key(entered_key): # API 키 유효성 검사
                self.settings["api_key"] = entered_key
                self.settings["use_vertex_ai"] = False
                QMessageBox.information(self, "API 키 저장됨", "API 키가 유효하며 저장되었습니다.")
                self.accept()
            else:
                QMessageBox.critical(self, "유효하지 않은 API 키", "입력하신 API 키가 유효하지 않습니다. 다시 확인해주세요.")

# --- Tier Selection Window ---
class TierSelectionDialog(QDialog):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle("API 티어 확인")
        self.tier = None
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.info_label = QLabel("Google Cloud (Gemini API)에 카드를 등록하셨나요?")
        layout.addWidget(self.info_label)

        button_layout = QHBoxLayout()

        self.free_button = QPushButton("아니요 (Free Tier)")
        self.free_button.clicked.connect(self.select_free)
        button_layout.addWidget(self.free_button)

        self.paid_button = QPushButton("예 (Tier 1+)")
        self.paid_button.clicked.connect(self.select_paid)
        button_layout.addWidget(self.paid_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def optimize_settings_for_tier(self, tier):
        # Retrieve the current custom prompt from settings (or default to empty)
        custom_prompt = self.settings.get("custom_prompt", "")
        new_chunk_size = 1800
        if new_chunk_size < 1:
            new_chunk_size = 1
        self.settings["chunk_size"] = new_chunk_size

        if tier == "free":
            self.settings["max_concurrent_requests"] = 1
            self.settings["request_delay"] = 0
        elif tier == "paid":
            self.settings["max_concurrent_requests"] = 30
            self.settings["request_delay"] = 0

        # Set the model to Gemini 2.0 Flash regardless of tier
        self.settings["gemini_model"] = "gemini-2.0-flash"
        self.settings["tier"] = tier

        # Save the updated settings to the file
        save_settings(self.settings)

    def select_free(self):
        self.tier = "free"
        self.optimize_settings_for_tier("free")
        self.close()

    def select_paid(self):
        self.tier = "paid"
        self.optimize_settings_for_tier("paid")
        self.close()

class AdvancedSettingsDialog(QDialog):
    def __init__(self, settings):
        super().__init__()
        self.setWindowTitle("Advanced Settings")
        self.settings = settings
        self.initUI()
        self.update_vertex_ai_fields_enabled_state()

    def initUI(self):
        main_layout = QVBoxLayout()

        # ----- Top Section: Two Columns -----
        top_layout = QHBoxLayout()

        # Left Column Layout
        left_layout = QVBoxLayout()
        # --- API & Tier Group ---
        api_group = QGroupBox("Gemini API 관련")
        api_layout = QVBoxLayout()
        self.api_key_label = QLabel("Gemini API 키:")
        api_layout.addWidget(self.api_key_label)
        self.api_key_display = QLineEdit()
        self.api_key_display.setText(self.settings.get("api_key", ""))
        self.api_key_display.setReadOnly(True)
        api_layout.addWidget(self.api_key_display)
        self.change_key_button = QPushButton("API 키 변경")
        self.change_key_button.clicked.connect(self.change_api_key)
        api_layout.addWidget(self.change_key_button)
        self.tier_label = QLabel("API 티어(카드 등록: paid):")
        api_layout.addWidget(self.tier_label)
        self.tier_combo = QComboBox()
        self.tier_combo.addItems(["free", "paid"])
        current_tier = self.settings.get("tier", "free")
        index = self.tier_combo.findText(current_tier)
        if index >= 0:
            self.tier_combo.setCurrentIndex(index)
        api_layout.addWidget(self.tier_combo)
        api_group.setLayout(api_layout)

        # --- Vertex AI Group ---
        vertex_ai_group = QGroupBox("Vertex AI 설정")
        vertex_ai_layout = QVBoxLayout()
        self.use_vertex_ai_checkbox = QCheckBox("Vertex AI 사용")
        self.use_vertex_ai_checkbox.setChecked(self.settings.get("use_vertex_ai", False))
        self.use_vertex_ai_checkbox.stateChanged.connect(self.update_vertex_ai_fields_enabled_state)
        vertex_ai_layout.addWidget(self.use_vertex_ai_checkbox)

        self.sa_json_path_label = QLabel("서비스 계정 JSON 파일 경로:")
        vertex_ai_layout.addWidget(self.sa_json_path_label)
        sa_path_layout = QHBoxLayout()
        self.sa_json_path_input = QLineEdit(self.settings.get("service_account_json_path", ""))
        sa_path_layout.addWidget(self.sa_json_path_input)
        self.sa_json_browse_button = QPushButton("찾아보기")
        self.sa_json_browse_button.clicked.connect(self.browse_sa_json)
        sa_path_layout.addWidget(self.sa_json_browse_button)
        vertex_ai_layout.addLayout(sa_path_layout)

        self.gcp_project_id_label = QLabel("GCP Project ID:")
        vertex_ai_layout.addWidget(self.gcp_project_id_label)
        self.gcp_project_id_input = QLineEdit(self.settings.get("gcp_project_id", ""))
        vertex_ai_layout.addWidget(self.gcp_project_id_input)
        self.gcp_location_label = QLabel("GCP Location (e.g., asia-northeast3):")
        vertex_ai_layout.addWidget(self.gcp_location_label)
        self.gcp_location_input = QLineEdit(self.settings.get("gcp_location", "asia-northeast3"))
        vertex_ai_layout.addWidget(self.gcp_location_input)
        vertex_ai_group.setLayout(vertex_ai_layout)


        left_layout.addWidget(api_group)

        # --- Gemini Model Group ---
        gemini_group = QGroupBox("Gemini 모델")
        gemini_layout = QVBoxLayout()
        self.gemini_model_combo = QComboBox()
        self.gemini_model_combo.setEditable(True)
        self.gemini_model_combo.addItem("Gemini 1.5 Pro", "gemini-1.5-pro")
        self.gemini_model_combo.addItem("Gemini 2.0 Flash", "gemini-2.0-flash")
        self.gemini_model_combo.addItem("Gemini 2.5 Pro Experimental", "gemini-2.5-pro-exp-03-25")
        self.gemini_model_combo.addItem("Gemini 2.5 Pro Preview(유료)", " gemini-2.5-pro-preview-03-25")
        gemini_layout.addWidget(self.gemini_model_combo)
        if "gemini_model" in self.settings:
            saved_model = self.settings["gemini_model"]
            reverse_mapping = {
                "gemini-1.5-pro": "Gemini 1.5 Pro",
                "gemini-2.0-flash": "Gemini 2.0 Flash",
                "gemini-2.5-pro-exp-03-25": "Gemini 2.5 Pro Experimental",
                "gemini-2.5-pro-preview-03-25": "Gemini 2.5 Pro Preview(유료)"
            }
            self.gemini_model_combo.setCurrentText(reverse_mapping.get(saved_model, saved_model))
        gemini_group.setLayout(gemini_layout)
        left_layout.addWidget(gemini_group)
        left_layout.addWidget(vertex_ai_group) # Vertex AI 그룹 추가

        top_layout.addLayout(left_layout)

        # Right Column Layout
        right_layout = QVBoxLayout()
        # --- Performance Settings Group ---
        performance_group = QGroupBox("성능 관련")
        performance_layout = QVBoxLayout()
        self.chunk_size_label = QLabel("청크 사이즈 (1-10000):")
        performance_layout.addWidget(self.chunk_size_label)
        self.chunk_size_input = QLineEdit()
        self.chunk_size_input.setValidator(QIntValidator(1, 10000, self))
        default_chunk_size = self.settings.get("chunk_size", 1000)
        self.chunk_size_input.setText(str(default_chunk_size))
        performance_layout.addWidget(self.chunk_size_input)
        self.max_concurrent_label = QLabel("최대 동시 요청 수 (1-99):")
        performance_layout.addWidget(self.max_concurrent_label)
        self.max_concurrent_input = QLineEdit()
        self.max_concurrent_input.setValidator(QIntValidator(1, 99, self))
        default_max_concurrent = self.settings.get("max_concurrent_requests", 1)
        self.max_concurrent_input.setText(str(default_max_concurrent))
        performance_layout.addWidget(self.max_concurrent_input)
        self.request_delay_label = QLabel("요청 지연 (0-99):")
        performance_layout.addWidget(self.request_delay_label)
        self.request_delay_input = QLineEdit()
        self.request_delay_input.setValidator(QDoubleValidator(0, 99, 2, self))
        default_request_delay = self.settings.get("request_delay", 0.0)
        self.request_delay_input.setText(str(default_request_delay))
        performance_layout.addWidget(self.request_delay_input)
        performance_group.setLayout(performance_layout)
        right_layout.addWidget(performance_group)

        # --- Modes Group ---
        #modes_group = QGroupBox("기타 설정")
        #modes_layout = QVBoxLayout()
        self.dual_language_checkbox = QCheckBox("원문과 번역문 같이 표시")
        self.dual_language_checkbox.setChecked(self.settings.get("dual_language_mode", False))
        #modes_layout.addWidget(self.dual_language_checkbox)
        self.completion_mode_checkbox = QCheckBox("번역 후 검수")
        self.completion_mode_checkbox.setChecked(self.settings.get("completion_mode", False))
        #modes_layout.addWidget(self.completion_mode_checkbox)
        self.image_annotation_checkbox = QCheckBox("이미지에 주석 달기")
        self.image_annotation_checkbox.setChecked(self.settings.get("image_annotation_mode", False))
        #modes_layout.addWidget(self.image_annotation_checkbox)
        self.language_label = QLabel("원어 (영어로 적을 것)")
        self.language_input = QLineEdit()
        default_language = self.settings.get("language", "Japanese")
        self.language_input.setText(str(default_language))
        #modes_layout.addWidget(self.language_label)
        #modes_layout.addWidget(self.language_input)
        #modes_group.setLayout(modes_layout)
        #right_layout.addWidget(modes_group)

        top_layout.addLayout(right_layout)
        main_layout.addLayout(top_layout)

        # ----- Bottom Section: Custom Prompt -----
        prompt_group = QGroupBox("커스텀 프롬프트")
        prompt_layout = QVBoxLayout()
        self.custom_prompt_input = QTextEdit()
        self.custom_prompt_input.setPlainText(self.settings.get("custom_prompt", ""))
        prompt_layout.addWidget(self.custom_prompt_input)
        prompt_group.setLayout(prompt_layout)
        main_layout.addWidget(prompt_group)

        # ----- Bottom Buttons: Save, Optimize and Exit -----
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("저장 후 닫기")
        self.save_button.clicked.connect(self.save_and_close)
        button_layout.addWidget(self.save_button)

        self.optimize_button = QPushButton("설정 최적화")
        self.optimize_button.clicked.connect(self.optimize_settings)
        button_layout.addWidget(self.optimize_button)

        self.exit_button = QPushButton("저장하지 않고 닫기")
        self.exit_button.clicked.connect(self.reject)
        button_layout.addWidget(self.exit_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def browse_sa_json(self):
        path, _ = QFileDialog.getOpenFileName(self, "서비스 계정 JSON 파일 선택", "", "JSON Files (*.json)")
        if path:
            self.sa_json_path_input.setText(path)

    def update_vertex_ai_fields_enabled_state(self):
        use_vertex = self.use_vertex_ai_checkbox.isChecked()
        self.sa_json_path_label.setEnabled(use_vertex)
        self.sa_json_path_input.setEnabled(use_vertex)
        self.sa_json_browse_button.setEnabled(use_vertex)
        self.gcp_project_id_label.setEnabled(use_vertex)
        self.gcp_project_id_input.setEnabled(use_vertex)
        self.gcp_location_label.setEnabled(use_vertex)
        self.gcp_location_input.setEnabled(use_vertex)

        # API 키 관련 필드는 Vertex AI 사용 시 선택적으로 비활성화 가능
        # self.api_key_display.setEnabled(not use_vertex)
        # self.change_key_button.setEnabled(not use_vertex)



    def optimize_settings(self):
        # Use the current tier from the combo box and the custom prompt from this dialog
        tier = self.tier_combo.currentText().lower()  # "free" or "paid"
        custom_prompt = self.custom_prompt_input.toPlainText()
        new_chunk_size = 1800
        if new_chunk_size < 1000:
            new_chunk_size = 1000
        self.chunk_size_input.setText(str(new_chunk_size))
        
        if tier == "free":
            self.max_concurrent_input.setText("1")
            self.request_delay_input.setText("0")
        elif tier == "paid":
            self.max_concurrent_input.setText("30")
            self.request_delay_input.setText("0")
        
        # Always set the model to Gemini 2.0 Flash
        self.gemini_model_combo.setCurrentText("Gemini 2.0 Flash")

    def change_api_key(self):
        dialog = APIKeyDialog()
        if dialog.exec_() == QDialog.Accepted and dialog.api_key:
            new_key = dialog.api_key
            self.settings["api_key"] = new_key
            self.api_key_display.setText(new_key)
            save_settings(self.settings)

    def save_settings(self):
        self.settings["tier"] = self.tier_combo.currentText()
        model_text = self.gemini_model_combo.currentText()
        friendly_to_raw = {
            "Gemini 1.5 Pro": "gemini-1.5-pro",
            "Gemini 2.0 Flash": "gemini-2.0-flash",
            "Gemini 2.5 Pro Experimental": "gemini-2.5-pro-exp-03-25",
            "Gemini 2.5 Pro Preview(유료)": "gemini-2.5-pro-preview-03-25",
        }
        self.settings["gemini_model"] = friendly_to_raw.get(model_text, model_text)
        try:
            self.settings["chunk_size"] = int(self.chunk_size_input.text())
        except ValueError:
            self.settings["chunk_size"] = 1000
        try:
            self.settings["max_concurrent_requests"] = int(self.max_concurrent_input.text())
        except ValueError:
            self.settings["max_concurrent_requests"] = 1
        try:
            self.settings["request_delay"] = float(self.request_delay_input.text())
        except ValueError:
            self.settings["request_delay"] = 0.0
        self.settings["custom_prompt"] = self.custom_prompt_input.toPlainText()
        # Vertex AI settings
        self.settings["use_vertex_ai"] = self.use_vertex_ai_checkbox.isChecked()
        self.settings["service_account_json_path"] = self.sa_json_path_input.text()
        self.settings["gcp_project_id"] = self.gcp_project_id_input.text()
        self.settings["gcp_location"] = self.gcp_location_input.text()
        
        self.settings["dual_language_mode"] = self.dual_language_checkbox.isChecked()
        self.settings["completion_mode"] = self.completion_mode_checkbox.isChecked()
        self.settings["image_annotation_mode"] = self.image_annotation_checkbox.isChecked()
        self.settings["language"] = self.language_input.text()

        save_settings(self.settings)

    def save_and_close(self):
        self.save_settings()
        self.accept()