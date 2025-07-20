import os
from PySide6.QtCore import QStandardPaths

def get_save_directory() -> str:
    documents_folder = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
    return os.path.join(documents_folder, "SeaMarine_AI_Translate_Tool/Output/")