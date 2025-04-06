import sys
import os
import json
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLineEdit, QPushButton, QVBoxLayout, QLabel, 
    QMessageBox, QHBoxLayout, QDialog, QComboBox, QCheckBox, QTextEdit, QGroupBox
)
from PyQt5.QtCore import QUrl, QStandardPaths
from PyQt5.QtGui import QDesktopServices, QIntValidator, QDoubleValidator
from google import genai

# --- Placeholder function for API key validation ---
def check_api_key(api_key):
    """
    Simulate checking the API key.
    Replace this with an actual Gemini API call.
    Here, we assume any key that starts with "AIza" is valid.
    """
    client = genai.Client(api_key=api_key)
    try:
        response = client.models.generate_content(
            model='gemini-2.0-flash-lite',
            contents='Hi there! How are you?',
        )
    except Exception as e:
        return False
    return True

# --- Functions to load and save settings ---
def get_settings_path():
    documents_folder = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
    return os.path.join(documents_folder, "SeaMarine_Epub_Translator_settings.json")

def load_settings():
    settings_path = get_settings_path()
    if os.path.exists(settings_path):
        with open(settings_path, "r") as f:
            return json.load(f)
    return {}

def save_settings(settings_data):
    settings_path = get_settings_path()
    with open(settings_path, "w") as f:
        json.dump(settings_data, f)


# --- API Key Entry Window (used for initial entry and via Advanced Settings) ---
# You may want to convert this to a QDialog for modal behavior.
class APIKeyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Sea Marine")
        self.api_key = None
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        self.info_label = QLabel("Google Gemini API 키를 입력하세요:")
        layout.addWidget(self.info_label)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("여기에 API 키를 입력하세요")
        layout.addWidget(self.api_key_input)
        
        # Button to open API key link
        self.link_button = QPushButton("API 키 확인/발급 하러가기")
        self.link_button.clicked.connect(self.open_api_link)
        layout.addWidget(self.link_button)
        
        # Button to check API key
        self.check_button = QPushButton("API Key 체크")
        self.check_button.clicked.connect(self.validate_api_key)
        layout.addWidget(self.check_button)
        
        self.setLayout(layout)
    
    def open_api_link(self):
        url = QUrl("https://aistudio.google.com/app/apikey")
        QDesktopServices.openUrl(url)
    
    def validate_api_key(self):
        entered_key = self.api_key_input.text().strip()
        if not entered_key:
            QMessageBox.warning(self, "입력 에러", "API 키를 작성해주세요.")
            return
        
        if check_api_key(entered_key):
            QMessageBox.information(self, "성공", "API 키가 유효합니다.")
            self.api_key = entered_key
            self.accept()
        else:
            QMessageBox.critical(self, "유효하지 않은 API 키", "입력하신 API 키가 유효하지 않습니다. 다시 확인해주세요.")

# --- Tier Selection Window ---
class TierSelectionDialog(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Select API Tier")
        self.tier = None
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        self.info_label = QLabel("Is your Google API key Free-tier or Paid-tier?")
        layout.addWidget(self.info_label)
        
        button_layout = QHBoxLayout()
        
        self.free_button = QPushButton("Free Tier")
        self.free_button.clicked.connect(self.select_free)
        button_layout.addWidget(self.free_button)
        
        self.paid_button = QPushButton("Paid Tier")
        self.paid_button.clicked.connect(self.select_paid)
        button_layout.addWidget(self.paid_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def select_free(self):
        self.tier = "free"
        self.close()
    
    def select_paid(self):
        self.tier = "paid"
        self.close()

class AdvancedSettingsDialog(QDialog):
    def __init__(self, settings):
        super().__init__()
        self.setWindowTitle("Advanced Settings")
        self.settings = settings
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()

        # ----- Top Section: Two Columns -----
        top_layout = QHBoxLayout()

        # Left Column Layout
        left_layout = QVBoxLayout()
        # --- API & Tier Group ---
        api_group = QGroupBox("API & Tier")
        api_layout = QVBoxLayout()
        self.api_key_label = QLabel("Google Gemini API Key:")
        api_layout.addWidget(self.api_key_label)
        self.api_key_display = QLineEdit()
        self.api_key_display.setText(self.settings.get("api_key", ""))
        self.api_key_display.setReadOnly(True)
        api_layout.addWidget(self.api_key_display)
        self.change_key_button = QPushButton("Change API Key")
        self.change_key_button.clicked.connect(self.change_api_key)
        api_layout.addWidget(self.change_key_button)
        self.tier_label = QLabel("User Tier:")
        api_layout.addWidget(self.tier_label)
        self.tier_combo = QComboBox()
        self.tier_combo.addItems(["free", "paid"])
        current_tier = self.settings.get("tier", "free")
        index = self.tier_combo.findText(current_tier)
        if index >= 0:
            self.tier_combo.setCurrentIndex(index)
        api_layout.addWidget(self.tier_combo)
        api_group.setLayout(api_layout)
        left_layout.addWidget(api_group)

        # --- Gemini Model Group ---
        gemini_group = QGroupBox("Gemini Model")
        gemini_layout = QVBoxLayout()
        self.gemini_model_combo = QComboBox()
        self.gemini_model_combo.setEditable(True)
        self.gemini_model_combo.addItem("Gemini 1.5 Pro", "gemini-1.5-pro")
        self.gemini_model_combo.addItem("Gemini 2.0 Flash", "gemini-2.0-flash")
        self.gemini_model_combo.addItem("Gemini 2.5 Pro Experimental", "gemini-2.5-pro-preview-03-25")
        gemini_layout.addWidget(self.gemini_model_combo)
        if "gemini_model" in self.settings:
            saved_model = self.settings["gemini_model"]
            reverse_mapping = {
                "gemini-1.5-pro": "Gemini 1.5 Pro",
                "gemini-2.0-flash": "Gemini 2.0 Flash",
                "gemini-2.5-pro-preview-03-25": "Gemini 2.5 Pro Experimental"
            }
            self.gemini_model_combo.setCurrentText(reverse_mapping.get(saved_model, saved_model))
        gemini_group.setLayout(gemini_layout)
        left_layout.addWidget(gemini_group)

        top_layout.addLayout(left_layout)

        # Right Column Layout
        right_layout = QVBoxLayout()
        # --- Performance Settings Group ---
        performance_group = QGroupBox("Performance Settings")
        performance_layout = QVBoxLayout()
        self.chunk_size_label = QLabel("Chunk Size (1-10000):")
        performance_layout.addWidget(self.chunk_size_label)
        self.chunk_size_input = QLineEdit()
        self.chunk_size_input.setValidator(QIntValidator(1, 10000, self))
        default_chunk_size = self.settings.get("chunk_size", 1000)
        self.chunk_size_input.setText(str(default_chunk_size))
        performance_layout.addWidget(self.chunk_size_input)
        self.max_concurrent_label = QLabel("Max Concurrent Requests (1-99):")
        performance_layout.addWidget(self.max_concurrent_label)
        self.max_concurrent_input = QLineEdit()
        self.max_concurrent_input.setValidator(QIntValidator(1, 99, self))
        default_max_concurrent = self.settings.get("max_concurrent_requests", 1)
        self.max_concurrent_input.setText(str(default_max_concurrent))
        performance_layout.addWidget(self.max_concurrent_input)
        self.request_delay_label = QLabel("Request Delay (0-99):")
        performance_layout.addWidget(self.request_delay_label)
        self.request_delay_input = QLineEdit()
        self.request_delay_input.setValidator(QDoubleValidator(0, 99, 2, self))
        default_request_delay = self.settings.get("request_delay", 0.0)
        self.request_delay_input.setText(str(default_request_delay))
        performance_layout.addWidget(self.request_delay_input)
        performance_group.setLayout(performance_layout)
        right_layout.addWidget(performance_group)

        # --- Modes Group ---
        modes_group = QGroupBox("Modes")
        modes_layout = QVBoxLayout()
        self.dual_language_checkbox = QCheckBox("Dual Language Mode")
        self.dual_language_checkbox.setChecked(self.settings.get("dual_language_mode", False))
        modes_layout.addWidget(self.dual_language_checkbox)
        self.completion_mode_checkbox = QCheckBox("Completion Mode")
        self.completion_mode_checkbox.setChecked(self.settings.get("completion_mode", False))
        modes_layout.addWidget(self.completion_mode_checkbox)
        self.image_annotation_checkbox = QCheckBox("Image Annotation Mode")
        self.image_annotation_checkbox.setChecked(self.settings.get("image_annotation_mode", False))
        modes_layout.addWidget(self.image_annotation_checkbox)
        modes_group.setLayout(modes_layout)
        right_layout.addWidget(modes_group)

        top_layout.addLayout(right_layout)
        main_layout.addLayout(top_layout)

        # ----- Bottom Section: Custom Prompt (spanning both columns) -----
        prompt_group = QGroupBox("Custom Prompt")
        prompt_layout = QVBoxLayout()
        self.custom_prompt_input = QTextEdit()
        self.custom_prompt_input.setPlainText(self.settings.get("custom_prompt", ""))
        prompt_layout.addWidget(self.custom_prompt_input)
        prompt_group.setLayout(prompt_layout)
        main_layout.addWidget(prompt_group)

        # ----- Bottom Buttons: Save and Exit Without Saving -----
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save Settings")
        self.save_button.clicked.connect(self.save_and_close)
        button_layout.addWidget(self.save_button)
        self.exit_button = QPushButton("Exit without saving")
        self.exit_button.clicked.connect(self.reject)
        button_layout.addWidget(self.exit_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

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
            "Gemini 2.5 Pro Experimental": "gemini-2.5-pro-preview-03-25"
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
        self.settings["dual_language_mode"] = self.dual_language_checkbox.isChecked()
        self.settings["completion_mode"] = self.completion_mode_checkbox.isChecked()
        self.settings["image_annotation_mode"] = self.image_annotation_checkbox.isChecked()

        save_settings(self.settings)

    def save_and_close(self):
        self.save_settings()
        self.accept()

# --- Main Application Window ---
class MainWindow(QWidget):
    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.setWindowTitle("Main Application Window")
        self.initUI()
        
    def initUI(self):
        layout = QVBoxLayout()
        
        self.info_label = QLabel(
            f"API Key: {self.settings.get('api_key')}\n"
            f"Tier: {self.settings.get('tier')}\n\n"
            "Main functionality goes here."
        )
        layout.addWidget(self.info_label)
        
        # Advanced Settings button
        self.advanced_button = QPushButton("Advanced Settings")
        self.advanced_button.clicked.connect(self.open_advanced_settings)
        layout.addWidget(self.advanced_button)
        
        self.setLayout(layout)
    
    def open_advanced_settings(self):
        dialog = AdvancedSettingsDialog(self.settings)
        dialog.exec_()
        # Optionally, update the main window to reflect any changes.
        self.info_label.setText(
            f"API Key: {self.settings.get('api_key')}\n"
            f"Tier: {self.settings.get('tier')}\n\n"
            "Main functionality goes here."
        )

# --- Main function ---
def main():
    app = QApplication(sys.argv)
    
    # Load settings from file.
    settings = load_settings()
    api_key = settings.get("api_key")
    tier = settings.get("tier")
    
    # If API key is not stored, prompt for it.
    if not api_key:
        api_dialog = APIKeyDialog()
        api_dialog.show()
        while api_dialog.isVisible():
            app.processEvents()
        api_key = api_dialog.api_key
        if not api_key:
            sys.exit(0)
        settings["api_key"] = api_key
        save_settings(settings)
    
    # If tier is not stored, prompt for tier selection.
    if not tier:
        tier_dialog = TierSelectionDialog()
        tier_dialog.show()
        while tier_dialog.isVisible():
            app.processEvents()
        tier = tier_dialog.tier if tier_dialog.tier else "free"
        settings["tier"] = tier
        save_settings(settings)
    
    # Proceed to the main application window.
    main_window = MainWindow(settings)
    main_window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()
