import os
import shutil
from utils.pn_dict import get_dict_directory

class RuntimeData:
    def __init__(self):
        self.gemini_model_list: list[str] = []
        self.translate_log: list[str] = []
        self.file: str = ""
        self.filename: str = ""
        self.pn_dict_file: str = ""
        self.user_dict_file: str = os.path.join(get_dict_directory() + "seamarine_user_dict.csv")
        self.save_directory: str = ""
        self.is_translating: bool = False
        self.current_phase: str = "None"
        self.homeViewHash = None
    
    def set_file(self, path: str) -> None:
        if not os.path.exists(path):
            return
        os.makedirs(self.save_directory, exist_ok=True)
        self.filename = os.path.basename(path)
        self.file = os.path.join(self.save_directory, self.filename)
        if self.file != path:
            shutil.copy2(path, self.file)

        fn, _ = os.path.splitext(self.filename)
        self.pn_dict_file = os.path.join(get_dict_directory(), fn+".csv")
    