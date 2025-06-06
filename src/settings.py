import os
import json
from PyQt5.QtCore import QStandardPaths

def get_settings_path():
    documents_folder = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
    return os.path.join(documents_folder, "SeaMarine_Epub_Translator_settings.json")

def load_settings():
    settings_path = get_settings_path()
    if os.path.exists(settings_path):
        with open(settings_path, "r") as f:
            return json.load(f)
    # 기본값 설정
    return {
        "use_vertex_ai": False,
        "service_account_json_path": "",
        "gcp_project_id": "",
        "gcp_location": "asia-northeast3", # Vertex AI 기본 리전 예시
        "tier": "free" # 기존 티어 설정 유지
    }

def save_settings(settings_data):
    settings_path = get_settings_path()
    with open(settings_path, "w") as f:
        json.dump(settings_data, f)
