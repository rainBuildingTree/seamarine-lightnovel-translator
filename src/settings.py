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
    return {}

def save_settings(settings_data):
    settings_path = get_settings_path()
    with open(settings_path, "w") as f:
        json.dump(settings_data, f)
