import logging
from PySide6.QtCore import QStandardPaths
import os

def _get_log_file_path():
    documents_folder = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
    return os.path.join(documents_folder, "SeaMarine_AI_Translate_Tool/app.log")
def _get_translate_log_file_path():
    documents_folder = QStandardPaths.writableLocation(QStandardPaths.DocumentsLocation)
    return os.path.join(documents_folder, "SeaMarine_AI_Translate_Tool/translate.log")

def setup_logger(name: str = "seamarine") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        log_file_path = _get_log_file_path()
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        fh = logging.FileHandler(log_file_path)
        fh.setLevel(logging.DEBUG)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)

        logger.addHandler(ch)
        logger.addHandler(fh)

    return logger

def setup_translate_logger(target: list[str], name: str = "seamarine_translate") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)

        log_file_path = _get_translate_log_file_path()
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
        fh = logging.FileHandler(log_file_path)
        fh.setLevel(logging.DEBUG)

        lh = ListAccumulatorHandler(target)
        lh.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        ch.setFormatter(formatter)
        fh.setFormatter(formatter)
        lh.setFormatter(formatter)

        logger.addHandler(ch)
        logger.addHandler(fh)
        logger.addHandler(lh)

    return logger

class ListAccumulatorHandler(logging.Handler):
    def __init__(self, target_object_list: list[str]):
        super().__init__()
        self.target_object_list: list[str] = target_object_list

    def emit(self, record):
        log_message = self.format(record)
        self.target_object_list.append(log_message)
    
    