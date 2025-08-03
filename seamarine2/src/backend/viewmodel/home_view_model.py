from PySide6.QtCore import QObject, Slot, Property, Signal, QStandardPaths
from backend.controller.app_controller import AppController
from logger_config import setup_logger
import logging
from PySide6.QtWidgets import QFileDialog
from backend.model import ConfigData, RuntimeData
from backend.worker import RubyRemover, PnExtractor, MainTranslator, TocTranslator, Reviewer, LanguageMerger, ImageAnnotater
import csv
import os
import time

class HomeViewModel(QObject):
    def __init__(self, config_data, runtime_data, app_controller, parent=None):
        super().__init__(parent)
        self._logger = setup_logger()
        try:
            runtime_data.homeViewHash = hash(self)
            self._config_data: ConfigData = config_data
            self._runtime_data: RuntimeData = runtime_data
            self._app_controller: AppController = app_controller
            self._progress: int = 0

            self._logger.info(str(self) + ".__init__")
        except Exception as e:
            self._logger.error(str(self) + str(e))

    fileChanged = Signal()
    def get_file(self):
        return self._runtime_data.file
    def set_file(self, value):
        self._runtime_data.set_file(value)
        self.fileChanged.emit()
        self.filenameChanged.emit()
    file = Property(str, get_file, set_file, notify=fileChanged)

    filenameChanged = Signal()
    @Property(str, notify=filenameChanged)
    def filename(self):
        return str(self._runtime_data.filename)
    
    translatingChanged = Signal()
    @Property(bool, notify=translatingChanged)
    def translating(self):
        return self._runtime_data.is_translating
    def set_is_translating(self, value):
        self._runtime_data.is_translating = value
        self.translatingChanged.emit()
    
    progressChanged = Signal()
    def get_progress(self):
        return self._progress
    def set_progress(self, value):
        self._logger.info(self._runtime_data.current_phase)
        if self._runtime_data.current_phase == "ruby removal":
            self._progress = int(value * 1 / 100)
            self._logger.info(self._progress)
        elif self._runtime_data.current_phase == "pn extract":
            self._progress = int(1 + (value * 5 / 100))
        elif self._runtime_data.current_phase == "main translation":
            self._progress = int(6 + (value * 74 / 100))
        elif self._runtime_data.current_phase == "toc translation":
            self._progress = int(80 + (value * 2 / 100))
        elif self._runtime_data.current_phase == "review":
            self._progress = int(82 + (value * 8 / 100))
        elif self._runtime_data.current_phase == "dual language":
            self._progress = int(90 + (value * 1 / 100))
        elif self._runtime_data.current_phase == "image translation":
            self._progress = int(91 + (value * 8 / 100))
        elif self._runtime_data.current_phase == "absolute":
            self._progress = int(value)
        else:
            return
        self.progressChanged.emit()
    progress = Property(int, get_progress, set_progress, notify=progressChanged)
    
    @Slot()
    def lazy_init(self):
        try:
            self.fileChanged.emit()
            self.filenameChanged.emit()
            if self._runtime_data.is_translating and self._runtime_data.current_phase == "pn dict edit" and hash(self) == self._runtime_data.homeViewHash:
                self._main_translate()
            self._logger.info(str(self) + ".lazy_init")
        except Exception as e:
            self._logger.error(str(self) + ".lazy_init\n-> " + str(e))
    
    @Slot()
    def open_setting(self):
        if self._runtime_data.is_translating:
            return
        try:
            self._app_controller.navigateToSettingPage.emit()
            self._logger.info(str(self) + ".open_setting")
        except Exception as e:
            self._logger.error(str(self) + str(e))

    @Slot()
    def open_advanced_mode(self):
        if self._runtime_data.is_translating:
            return
        try:
            self._app_controller.navigateToAdvancedModePage.emit()
            self._logger.info(str(self) + ".open_advanced_mode")
        except Exception as e:
            self._logger.error(str(self) + str(e))

    @Slot()
    def select_file(self):
        if self._runtime_data.is_translating:
            return
        try:
            path = QFileDialog.getOpenFileName(None, "번역할 파일을 선택해주세요", QStandardPaths.standardLocations(QStandardPaths.HomeLocation)[0], "EPUB 파일 (*.epub)")[0]
            self._runtime_data.set_file(path)
            self.filenameChanged.emit()
            self.fileChanged.emit()
            self._logger.info(str(self) + ".select_file -> " + self._runtime_data.file)
        except Exception as e:
            self._logger.error(str(self) + ".select_file\n->" + str(e))
    def updateTargetFile(self, path):
        self._runtime_data.set_file(path)
        self.fileChanged.emit()
        self.filenameChanged.emit()


    @Slot()
    def start_translate(self):
        if self._runtime_data.is_translating:
            return
        self.set_is_translating(True)
        self._runtime_data.current_phase = "absolute"
        self.set_progress(0)
        print(self._config_data.translate_pipeline)
        self._remove_ruby()

    def _remove_ruby(self):
        self._runtime_data.current_phase = "ruby removal"
        if "ruby removal" not in self._config_data.translate_pipeline:
            self._extract_pn()
            return
        try:
            self._logger.info("Ruby Removal")
            self.ruby_remover = RubyRemover(self._runtime_data.file, self._runtime_data.save_directory)
            self.ruby_remover.progress.connect(self.set_progress)
            self.ruby_remover.saved.connect(self.updateTargetFile)
            self.ruby_remover.finished.connect(self.ruby_remover.quit)
            self.ruby_remover.finished.connect(self.ruby_remover.deleteLater)
            self.ruby_remover.finished.connect(self._extract_pn)
            self.ruby_remover.start()
            self._logger.info(str(self) + ".run_ruby_removal")
        except Exception as e:
            self._runtime_data.current_phase = "absolute"
            self.set_progress(0)
            self.set_is_translating(False)
            self._runtime_data.current_phase = "None"
            self._logger.exception(str(self) + ".run_ruby_removal\n-> " + str(e))

    def _extract_pn(self):
        self._runtime_data.current_phase = "pn extract"
        if "pn extract" not in self._config_data.translate_pipeline:
            self._edit_pn_dict()
            return
        try:
            self._logger.info("Extract Pn")
            self.pn_extractor = PnExtractor(
                self._app_controller.translate_core,
                self._config_data.pn_extract_model_config,
                self._runtime_data.file,
                self._runtime_data.pn_dict_file,
                self._config_data.max_chunk_size,
                self._config_data.max_concurrent_request,
                self._config_data.request_delay
            )
            self.pn_extractor.progress.connect(self.set_progress)
            self.pn_extractor.finished.connect(self.pn_extractor.quit)
            self.pn_extractor.finished.connect(self.pn_extractor.deleteLater)
            self.pn_extractor.finished.connect(self._edit_pn_dict)
            self.pn_extractor.start()
            self._logger.info(str(self) + ".run_pn_extract")
        except Exception as e:
            self._runtime_data.current_phase = "absolute"
            self.set_progress(0)
            self.set_is_translating(False)
            self._runtime_data.current_phase = "None"
            self._logger.exception(str(self) + ".run_pn_extract\n-> " + str(e))

    def _edit_pn_dict(self):
        if "pn dict edit" not in self._config_data.translate_pipeline:
            self._main_translate()
            return
        try:
            self._app_controller.navigateToPnDictEditPage.emit()
            self._logger.info(str(self) + ".run_pn_dict_edit")
            self._runtime_data.current_phase = "pn dict edit"
        except Exception as e:
            self._runtime_data.current_phase = "absolute"
            self.set_progress(0)
            self.set_is_translating(False)
            self._runtime_data.current_phase = "None"
            self._logger.exception(str(self) + ".run_pn_dict_edit\n-> " + str(e))

    def _main_translate(self):
        self._runtime_data.current_phase = "main translation"
        if "main translation" not in self._config_data.translate_pipeline:
            self._toc_translate()
            return
        try:
            self._logger.info("Main Translate")
            proper_noun = {}
            if os.path.exists(self._runtime_data.pn_dict_file):
                with open(self._runtime_data.pn_dict_file, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            proper_noun[row[0]] = row[1]
            if os.path.exists(self._runtime_data.user_dict_file):
                with open(self._runtime_data.user_dict_file, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            proper_noun[row[0]] = row[1]
            self.main_translator = MainTranslator(
                self._app_controller.translate_core,
                self._config_data.main_translate_model_config,
                proper_noun,
                self._runtime_data.file,
                self._runtime_data.save_directory,
                self._config_data.max_chunk_size,
                self._config_data.max_concurrent_request,
                self._config_data.request_delay
            )
            self.main_translator.progress.connect(self.set_progress)
            self.main_translator.completed.connect(self.updateTargetFile)
            self.main_translator.finished.connect(self.main_translator.quit)
            self.main_translator.finished.connect(self.main_translator.deleteLater)    
            self.main_translator.finished.connect(self._toc_translate)
            self.main_translator.start()
            self._logger.info(str(self) + ".run_main_translate")
        except Exception as e:
            self._runtime_data.current_phase = "absolute"
            self.set_progress(0)
            self.set_is_translating(False)
            self._runtime_data.current_phase = "None"
            self._logger.exception(str(self) + ".run_main_translate\n-> " + str(e))

    def _toc_translate(self):
        self._runtime_data.current_phase = "toc translation"
        if "toc translation" not in self._config_data.translate_pipeline:
            self._review()
            return
        try:
            self._logger.info("Toc Translate")
            proper_noun = {}
            if os.path.exists(self._runtime_data.pn_dict_file):
                with open(self._runtime_data.pn_dict_file, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            proper_noun[row[0]] = row[1]
            if os.path.exists(self._runtime_data.user_dict_file):
                with open(self._runtime_data.user_dict_file, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            proper_noun[row[0]] = row[1]
            self.toc_translator = TocTranslator(
                self._app_controller.translate_core,
                self._config_data.toc_translate_model_config,
                proper_noun,
                self._runtime_data.file,
                self._runtime_data.save_directory,
                self._config_data.max_chunk_size,
                self._config_data.max_concurrent_request,
                self._config_data.request_delay
            )
            self.toc_translator.progress.connect(self.set_progress)
            self.toc_translator.completed.connect(self.updateTargetFile)
            self.toc_translator.finished.connect(self.toc_translator.quit)
            self.toc_translator.finished.connect(self.toc_translator.deleteLater)
            self.toc_translator.finished.connect(self._review)
            self.toc_translator.start()
            self._logger.info(str(self) + ".run_toc_translate")
        except Exception as e:
            self._runtime_data.current_phase = "absolute"
            self.set_progress(0)
            self.set_is_translating(False)
            self._runtime_data.current_phase = "None"
            self._logger.exception(str(self) + ".run_toc_translate\n-> " + str(e))

    def _review(self):
        self._runtime_data.current_phase = "review"
        if "review" not in self._config_data.translate_pipeline:
            self._dual_language()
            return
        try:
            self._logger.info("Review")
            proper_noun = {}
            if os.path.exists(self._runtime_data.pn_dict_file):
                with open(self._runtime_data.pn_dict_file, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            proper_noun[row[0]] = row[1]
            if os.path.exists(self._runtime_data.user_dict_file):
                with open(self._runtime_data.user_dict_file, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            proper_noun[row[0]] = row[1]
            self.reviewer = Reviewer(
                self._app_controller.translate_core,
                self._config_data.review_model_config,
                proper_noun,
                self._runtime_data.file,
                self._runtime_data.save_directory,
                self._config_data.max_chunk_size,
                self._config_data.max_concurrent_request,
                self._config_data.request_delay
            )
            self.reviewer.progress.connect(self.set_progress)
            self.reviewer.completed.connect(self.updateTargetFile)
            self.reviewer.finished.connect(self.reviewer.quit)
            self.reviewer.finished.connect(self.reviewer.deleteLater)
            self.reviewer.finished.connect(self._dual_language)
            self.reviewer.start()
            self._logger.info(str(self) + ".run_review")
        except Exception as e:
            self._runtime_data.current_phase = "absolute"
            self.set_progress(0)
            self.set_is_translating(False)
            self._runtime_data.current_phase = "None"
            self._logger.exception(str(self) + ".run_review\n-> " + str(e))

    def _dual_language(self):
        self._runtime_data.current_phase = "dual language"
        if "dual language" not in self._config_data.translate_pipeline:
            self._translate_image()
            return
        try:
            self._logger.info("Dual Language")
            proper_noun = {}
            if os.path.exists(self._runtime_data.pn_dict_file):
                with open(self._runtime_data.pn_dict_file, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            proper_noun[row[0]] = row[1]
            if os.path.exists(self._runtime_data.user_dict_file):
                with open(self._runtime_data.user_dict_file, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            proper_noun[row[0]] = row[1]
            self.languageMerger = LanguageMerger(
                self._app_controller.translate_core,
                self._config_data.review_model_config,
                proper_noun,
                self._runtime_data.file,
                self._runtime_data.save_directory,
                self._config_data.max_chunk_size,
                self._config_data.max_concurrent_request,
                self._config_data.request_delay
            )
            self.languageMerger.progress.connect(self.set_progress)
            self.languageMerger.completed.connect(self.updateTargetFile)
            self.languageMerger.finished.connect(self.languageMerger.quit)
            self.languageMerger.finished.connect(self.languageMerger.deleteLater)
            self.languageMerger.finished.connect(self._translate_image)
            self.languageMerger.start()
            self._logger.info(str(self) + ".run_dual_language")
        except Exception as e:
            self._runtime_data.current_phase = "absolute"
            self.set_progress(0)
            self.set_is_translating(False)
            self._runtime_data.current_phase = "None"
            self._logger.exception(str(self) + ".run_dual_language\n-> " + str(e))

    def _translate_image(self):
        self._runtime_data.current_phase = "image translation"
        if "image translation" not in self._config_data.translate_pipeline:
            self._finish_translate()
            return
        try:
            self._logger.info("Image Translation")
            proper_noun = {}
            if os.path.exists(self._runtime_data.pn_dict_file):
                with open(self._runtime_data.pn_dict_file, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            proper_noun[row[0]] = row[1]
            if os.path.exists(self._runtime_data.user_dict_file):
                with open(self._runtime_data.user_dict_file, newline='', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if len(row) >= 2:
                            proper_noun[row[0]] = row[1]
            self.image_annotater = ImageAnnotater(
                self._app_controller.translate_core,
                self._config_data.image_translate_model_config,
                proper_noun,
                self._runtime_data.file,
                self._runtime_data.save_directory,
                self._config_data.max_chunk_size,
                self._config_data.max_concurrent_request,
                self._config_data.request_delay
            )
            self.image_annotater.progress.connect(self.set_progress)
            self.image_annotater.completed.connect(self.updateTargetFile)
            self.image_annotater.finished.connect(self.image_annotater.quit)
            self.image_annotater.finished.connect(self.image_annotater.deleteLater)
            self.image_annotater.finished.connect(self._finish_translate)
            self.image_annotater.start()
            self._logger.info(str(self) + ".run_image_translate")
        except Exception as e:
            self._runtime_data.current_phase = "absolute"
            self.set_progress(0)
            self.set_is_translating(False)
            self._runtime_data.current_phase = "None"
            self._logger.exception(str(self) + ".run_image_translate\n-> " + str(e))

    def _finish_translate(self):
        self._logger.info("Finished")
        self.set_is_translating(False)
        self._runtime_data.current_phase = "absolute"
        self.set_progress(100)
        self._runtime_data.current_phase = "None"

               