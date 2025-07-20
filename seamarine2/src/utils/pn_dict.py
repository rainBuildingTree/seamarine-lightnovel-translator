import os
import csv
from PySide6.QtCore import QStandardPaths

def get_dict_directory():
    documents_folder = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
    return os.path.join(documents_folder, "SeaMarine_AI_Translate_Tool/Proper_Noun_Dict/")

def save_dict(filename: str, data: list):
    os.makedirs(get_dict_directory(), exist_ok=True)
    path = os.path.join(get_dict_directory(), filename)
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerows(data)