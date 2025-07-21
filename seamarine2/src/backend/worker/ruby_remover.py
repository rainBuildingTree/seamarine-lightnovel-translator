from PySide6.QtCore import QThread, Signal
import asyncio
import zipfile
import os
import shutil
from bs4 import BeautifulSoup
import logging
import time

class RubyRemover(QThread):
    progress = Signal(int)
    saved = Signal(str)

    def __init__(self, file_path, save_directory):
        super().__init__()
        self._logger = logging.getLogger("seamarine_translate")
        try:
            self._file_path: str = file_path
            self._save_directory: str = save_directory
            self._working_dir: str
            self._logger.info(str(self) + f".__init__({file_path}, {save_directory})")
        except Exception as e:
            self._logger.error(str(self) + f".__init__({file_path}, {save_directory})\n-> " + str(e))
        
    def run(self):
        self._logger.info(str(self) + ".run")
        try:
            self._execute()
        except Exception as e:
            self.progress.emit(0)
            self._logger.error(str(self) + ".run\n-> " + str(e))

    def _execute(self):
        try:
            self.progress.emit(0)
            self._create_working_dir()
            self._unzip_epub()
            self._remove_ruby_from_htmls()
            self._zip_up_epub()
            self.saved.emit(self._file_path)
            self._logger.info(str(self) + "suceed to complete the task")
        except Exception as e:
            self._logger.error(str(self) + " failed to complete the task")
            raise e
        finally:
            self._remove_working_dir()
            self.progress.emit(100)

        
    def _create_working_dir(self):
        start_time = time.time()
        self._logger.info(str(self) + ".create_working_dir")
        try:
            self._working_dir = os.path.join(self._save_directory, "temp_working_dir")
            if os.path.exists(self._working_dir):
                shutil.rmtree(self._working_dir)
            os.makedirs(self._working_dir)
            end_time = time.time()
            self._logger.info(str(self) + ".create_working_dir.time_elapsed: " + str(end_time - start_time))
            self.progress.emit(2)
        except Exception as e:
            self._logger.error(str(self) + ".create_working_dir\n-> " + str(e))
            raise e
        
    def _unzip_epub(self):
        start_time = time.time()
        self._logger.info(str(self) + ".unzip_epub")
        try:
            with zipfile.ZipFile(self._file_path, 'r') as zip_ref:
                zip_ref.extractall(self._working_dir)
            end_time = time.time()
            self._logger.info(str(self) + ".unzip_epub.time_elapsed: " + str(end_time - start_time))
            self.progress.emit(12)
        except Exception as e:
            self._logger.error(str(self) + ".unzip_epub\n-> " + str(e))
            raise e

    def _remove_ruby_from_htmls(self):
        start_time = time.time()
        self._logger.info(str(self) + ".remove_ruby_from_htmls")
        try:
            for root, _, files in os.walk(self._working_dir):
                for file in files:
                    if file.endswith((".html", ".xhtml", ".htm")):
                        file_path = os.path.join(root, file)
                        with open(file_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        new_content = self._remove_ruby_tags_from_html(content)
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(new_content)
            end_time = time.time()
            self._logger.info(str(self) + ".remove_ruby_from_htmls.time_elapsed: " + str(end_time - start_time))
            self.progress.emit(48)
        except Exception as e:
            self._logger.error(str(self) + ".remove_ruby_from_htmls\n-> " + str(e))
            raise e
    
    def _zip_up_epub(self):
        start_time = time.time()
        self._logger.info(str(self) + ".zip_up_epub")
        try:
            with zipfile.ZipFile(self._file_path, 'w') as zip_out:
                for foldername, subfolders, filenames in os.walk(self._working_dir):
                    for filename in filenames:
                        file_path = os.path.join(foldername, filename)
                        archive_name = os.path.relpath(file_path, self._working_dir)
                        if archive_name == "mimetype":
                            zip_out.writestr("mimetype", open(file_path, "rb").read(), compress_type=zipfile.ZIP_STORED)
                        else:
                            zip_out.write(file_path, archive_name, compress_type=zipfile.ZIP_DEFLATED)
            end_time = time.time()
            self._logger.info(str(self) + ".zip_up_epub.time_elapsed: " + str(end_time - start_time))
            self.progress.emit(95)
        except Exception as e:
            self._logger.error(str(self) + ".zip_up_epub\n-> " + str(e))
            raise e
    
    def _remove_working_dir(self):
        try:
            if os.path.exists(self._working_dir):
                shutil.rmtree(self._working_dir)
            self.progress.emit(99)
            self._logger.info(str(self) + ".remove_working_dir")
        except Exception as e:
            self._logger.error(str(self) + ".remove_working_dir\n-> " + str(e))
            raise e


    def _remove_ruby_tags_from_html(self, html_content):
        soup = BeautifulSoup(html_content, "lxml-xml")
        
        for ruby in soup.find_all('ruby'):
            rts = ruby.find_all('rt')
            if rts:
                text = ""
                for rt in rts:
                    text += rt.get_text()
                ruby.replace_with(text)
            else:
                ruby.decompose()

        return str(soup)
