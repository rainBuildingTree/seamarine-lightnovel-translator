from PySide6.QtCore import QObject, Slot, Property, Signal, QStandardPaths
from backend.controller.app_controller import AppController
from logger_config import setup_logger
from PySide6.QtWidgets import QFileDialog
from backend.model import ConfigData, RuntimeData
from backend.worker import RubyRemover, PnExtractor, MainTranslator, TocTranslator, Reviewer, LanguageMerger, ImageAnnotater
from utils import paths
import csv
import os

class AdvancedModeViewModel(QObject):
    def __init__(self, config_data, runtime_data, app_controller, parent=None):
        super().__init__(parent)
        self._logger = setup_logger()
        try:
            self._config_data: ConfigData = config_data
            self._runtime_data: RuntimeData = runtime_data
            self._app_controller: AppController = app_controller
            self._progress: int = 0
            self._is_running = [False] * 8
            self._is_ruby_removal_running = False
            self._is_pn_extract_running = False
            self._is_main_translate_running = False
            self._is_toc_translate_running = False
            self._is_review_running = False
            self._is_dual_language_running = False
            self._is_image_translate_running = False

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
    
    progressChanged = Signal()
    def get_progress(self):
        return self._progress
    def set_progress(self, value):
        self._progress = value
        self.progressChanged.emit()
    progress = Property(int, get_progress, set_progress, notify=progressChanged)
    
    rubyRemovalRunningChanged = Signal()
    @Property(bool, notify=rubyRemovalRunningChanged)
    def rubyRemovalRunning(self):
        return self._is_ruby_removal_running
    def setRubyRemovalFalse(self):
        self._is_ruby_removal_running = False
        self._is_running[0] = False
        self.rubyRemovalRunningChanged.emit()
    def updateTargetFile(self, path):
        self._runtime_data.set_file(path)
        self.fileChanged.emit()
        self.filenameChanged.emit()

    pnExtractRunningChanged = Signal()
    @Property(bool, notify=pnExtractRunningChanged)
    def pnExtractRunning(self):
        return self._is_pn_extract_running
    def setPnExtractFalse(self):
        self._is_pn_extract_running = False
        self._is_running[1] = False
        self.pnExtractRunningChanged.emit()

    mainTranslateRunningChanged = Signal()
    @Property(bool, notify=mainTranslateRunningChanged)
    def mainTranslateRunning(self):
        return self._is_main_translate_running
    def setMainTranslateFalse(self):
        self._is_main_translate_running = False
        self._is_running[3] = False
        self.mainTranslateRunningChanged.emit()

    tocTranslateRunningChanged = Signal()
    @Property(bool, notify=tocTranslateRunningChanged)
    def tocTranslateRunning(self):
        return self._is_toc_translate_running
    def setTocTranslateFalse(self):
        self._is_toc_translate_running = False
        self._is_running[4] = False
        self.tocTranslateRunningChanged.emit()

    reviewRunningChanged = Signal()
    @Property(bool, notify=reviewRunningChanged)
    def reviewRunning(self):
        return self._is_review_running
    def setReviewFalse(self):
        self._is_review_running = False
        self._is_running[5] = False
        self.reviewRunningChanged.emit()

    dualLanguageRunningChanged = Signal()
    @Property(bool, notify=dualLanguageRunningChanged)
    def dualLanguageRunning(self):
        return self._is_dual_language_running
    def setDualLanguageFalse(self):
        self._is_dual_language_running = False
        self._is_running[6] = False
        self.dualLanguageRunningChanged.emit()

    imageTranslateChanged = Signal()
    @Property(bool, notify=imageTranslateChanged)
    def imageTranslateRunning(self):
        return self._is_image_translate_running
    def setImageTranslateFalse(self):
        self._is_image_translate_running =  False
        self._is_running[7] = False
        self.imageTranslateChanged.emit()

    @Slot()
    def run_ruby_removal(self):
        try:
            if True in self._is_running:
                raise Exception("A task is already running")
            self.ruby_remover = RubyRemover(self._runtime_data.file, self._runtime_data.save_directory)
            self.ruby_remover.progress.connect(self.set_progress)
            self.ruby_remover.saved.connect(self.updateTargetFile)
            self.ruby_remover.finished.connect(self.setRubyRemovalFalse)
            self.ruby_remover.finished.connect(self.ruby_remover.quit)
            self._is_ruby_removal_running = True
            self._is_running[0] = True
            self.rubyRemovalRunningChanged.emit()
            self.ruby_remover.start()
            self._logger.info(str(self) + ".run_ruby_removal")
        except Exception as e:
            self._logger.exception(str(self) + ".run_ruby_removal\n-> " + str(e))
    @Slot()
    def run_pn_extract(self):
        try:
            if True in self._is_running:
                raise Exception("A task is already running")
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
            self.pn_extractor.finished.connect(self.setPnExtractFalse)
            self.pn_extractor.finished.connect(self.pn_extractor.quit)
            self._is_pn_extract_running = True
            self._is_running[1] = True
            self.pnExtractRunningChanged.emit()
            self.pn_extractor.start()
            self._logger.info(str(self) + ".run_pn_extract")
        except Exception as e:
            self._logger.exception(str(self) + ".run_pn_extract\n-> " + str(e))

    @Slot()
    def run_pn_dict_edit(self):
        try:
            self._app_controller.navigateToPnDictEditPage.emit()
            self._logger.info(str(self) + ".run_pn_dict_edit")
        except Exception as e:
            self._logger.exception(str(self) + ".run_pn_dict_edit\n-> " + str(e))
    @Slot()
    def run_main_translate(self):
        try:
            if True in self._is_running:
                raise Exception("A task is already running")
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
            self.main_translator.finished.connect(self.setMainTranslateFalse)
            self.main_translator.completed.connect(self.updateTargetFile)
            self.main_translator.finished.connect(self.main_translator.quit)
            self._is_main_translate_running = True
            self._is_running[3] = True
            self.mainTranslateRunningChanged.emit()
            self.main_translator.start()
            self._logger.info(str(self) + ".run_main_translate")
        except Exception as e:
            self._logger.exception(str(self) + ".run_main_translate\n-> " + str(e))
    @Slot()
    def run_toc_translate(self):
        try:
            if True in self._is_running:
                raise Exception("A task is already running")
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
            self.toc_translator.finished.connect(self.setTocTranslateFalse)
            self.toc_translator.completed.connect(self.updateTargetFile)
            self.toc_translator.finished.connect(self.toc_translator.quit)
            self._is_toc_translate_running = True
            self._is_running[4] = True
            self.tocTranslateRunningChanged.emit()
            self.toc_translator.start()
            self._logger.info(str(self) + ".run_toc_translate")
        except Exception as e:
            self._logger.exception(str(self) + ".run_toc_translate\n-> " + str(e))

    @Slot()
    def run_review(self):
        try:
            if True in self._is_running:
                raise Exception("A task is already running")
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
            self.reviewer.finished.connect(self.setReviewFalse)
            self.reviewer.completed.connect(self.updateTargetFile)
            self.reviewer.finished.connect(self.reviewer.quit)
            self._is_review_running = True
            self._is_running[5] = True
            self.reviewRunningChanged.emit()
            self.reviewer.start()
            self._logger.info(str(self) + ".run_review")
        except Exception as e:
            self._logger.exception(str(self) + ".run_review\n-> " + str(e))
    @Slot()
    def run_dual_language(self):
        try:
            if True in self._is_running:
                raise Exception("A task is already running")
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
            self.languageMerger.finished.connect(self.setDualLanguageFalse)
            self.languageMerger.completed.connect(self.updateTargetFile)
            self.languageMerger.finished.connect(self.languageMerger.quit)
            self._is_dual_language_running = True
            self._is_running[6] = True
            self.dualLanguageRunningChanged.emit()
            self.languageMerger.start()
            self._logger.info(str(self) + ".run_dual_language")
        except Exception as e:
            self._logger.exception(str(self) + ".run_dual_language\n-> " + str(e))

    @Slot()
    def run_image_translate(self):
        try:
            if True in self._is_running:
                raise Exception("A task is already running")
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
            self.image_annotater.finished.connect(self.setImageTranslateFalse)
            self.image_annotater.completed.connect(self.updateTargetFile)
            self.image_annotater.finished.connect(self.image_annotater.quit)
            self._is_image_translate_running = True
            self._is_running[7] = True
            self.imageTranslateChanged.emit()
            self.image_annotater.start()
            self._logger.info(str(self) + ".run_image_translate")
        except Exception as e:
            self._logger.exception(str(self) + ".run_image_translate\n-> " + str(e))

    @Slot()
    def select_file(self):
        try:
            path = QFileDialog.getOpenFileName(None, "번역할 파일을 선택해주세요", QStandardPaths.standardLocations(QStandardPaths.HomeLocation)[0], "EPUB 파일 (*.epub)")[0]
            self._runtime_data.set_file(path)
            self.filenameChanged.emit()
            self.fileChanged.emit()
            self._logger.info(str(self) + ".select_file -> " + self._runtime_data.file)
        except Exception as e:
            self._logger.error(str(self) + ".select_file\n->" + str(e))

    @Slot()
    def close(self):
        try:
            self._app_controller.popCurrentPage.emit()
            self._logger.info(str(self) + ".close")
        except Exception as e:
            self._logger.error(str(self) + str(e))   

    @Slot()
    def open_guide_link(self):
        pass         