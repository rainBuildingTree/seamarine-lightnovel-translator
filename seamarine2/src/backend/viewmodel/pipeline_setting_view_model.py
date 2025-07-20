from PySide6.QtCore import QObject, Slot, Signal, Property
from backend.model import ConfigData, RuntimeData
from backend.controller import AppController
from utils.config import save_config
from logger_config import setup_logger

class PipelineSettingViewModel(QObject):
    def __init__(self, config_data:ConfigData, runtime_data:RuntimeData, app_controller, parent=None):
        super().__init__(parent)
        self.logger = setup_logger()
        try:
            self.config_data = config_data
            self.app_controller: AppController = app_controller
            self.runtime_data = runtime_data
            self.pipeline = set(self.config_data.translate_pipeline)

            self.is_ruby_removal_active = "ruby removal" in self.pipeline
            self.is_pn_extract_active = "pn extract" in self.pipeline
            self.is_pn_dict_edit_active = "pn dict edit" in self.pipeline
            self.is_main_translation_active = "main translation" in self.pipeline
            self.is_toc_translation_active = "toc translation" in self.pipeline
            self.is_review_active = "review" in self.pipeline
            self.is_dual_language_active = "dual language" in self.pipeline
            self.is_image_translation_active = "image translation" in self.pipeline
            self.logger.info(str(self) + ".__init__")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    isRubyRemovalActiveChanged = Signal()
    isPnExtractActiveChanged = Signal()
    isPnDictEditActiveChanged = Signal()
    isMainTranslationActiveChanged = Signal()
    isTocTranslationActiveChanged = Signal()
    isReviewActiveChanged = Signal()
    isDualLanguageActiveChanged = Signal()
    isImageTranslationActiveChanged = Signal()

    def isRubyRemovalActive(self):
        return self.is_ruby_removal_active
    rubyRemovalActive = Property(bool, fget=isRubyRemovalActive, notify=isRubyRemovalActiveChanged)

    def isPnExtractActive(self):
        return self.is_pn_extract_active
    pnExtractActive = Property(bool, fget=isPnExtractActive, notify=isPnExtractActiveChanged)

    def isPnDictEditActive(self):
        return self.is_pn_dict_edit_active
    pnDictEditActive = Property(bool, fget=isPnDictEditActive, notify=isPnDictEditActiveChanged)

    def isMainTranslationActive(self):
        return self.is_main_translation_active
    mainTranslationActive = Property(bool, fget=isMainTranslationActive, notify=isMainTranslationActiveChanged)

    def isTocTranslationActive(self):
        return self.is_toc_translation_active
    tocTranslationActive = Property(bool, fget=isTocTranslationActive, notify=isTocTranslationActiveChanged)

    def isReviewActive(self):
        return self.is_review_active
    reviewActive = Property(bool, fget=isReviewActive, notify=isReviewActiveChanged)

    def isDualLanguageActive(self):
        return self.is_dual_language_active
    dualLanguageActive = Property(bool, fget=isDualLanguageActive, notify=isDualLanguageActiveChanged)

    def isImageTranslationActive(self):
        return self.is_image_translation_active
    imageTranslationActive = Property(bool, fget=isImageTranslationActive, notify=isImageTranslationActiveChanged)

    @Slot()
    def toggle_ruby_removal(self):
        try:
            self.is_ruby_removal_active = not self.is_ruby_removal_active
            if self.is_ruby_removal_active:
                self.pipeline.add("ruby removal")
            else:
                self.pipeline.remove("ruby removal")
            self.isRubyRemovalActiveChanged.emit()
            self.logger.info(str(self) + ".toggle_ruby_removal")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    @Slot()
    def toggle_pn_extract(self):
        try:
            self.is_pn_extract_active = not self.is_pn_extract_active
            if self.is_pn_extract_active:
                self.pipeline.add("pn extract")
            else:
                self.pipeline.remove("pn extract")
            self.isPnExtractActiveChanged.emit()
            self.logger.info(str(self) + ".toggle_pn_extract")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    @Slot()
    def toggle_pn_dict_edit(self):
        try:
            self.is_pn_dict_edit_active = not self.is_pn_dict_edit_active
            if self.is_pn_dict_edit_active:
                self.pipeline.add("pn dict edit")
            else:
                self.pipeline.remove("pn dict edit")
            self.isPnDictEditActiveChanged.emit()
            self.logger.info(str(self) + ".toggle_pn_dict_edit")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    @Slot()
    def toggle_main_translation(self):
        try:
            self.is_main_translation_active = not self.is_main_translation_active
            if self.is_main_translation_active:
                self.pipeline.add("main translation")
            else:
                self.pipeline.remove("main translation")
            self.isMainTranslationActiveChanged.emit()
            self.logger.info(str(self) + ".toggle_main_translation")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    @Slot()
    def toggle_toc_translation(self):
        try:
            self.is_toc_translation_active = not self.is_toc_translation_active
            if self.is_toc_translation_active:
                self.pipeline.add("toc translation")
            else:
                self.pipeline.remove("toc translation")
            self.isTocTranslationActiveChanged.emit()
            self.logger.info(str(self) + ".toggle_toc_translation")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    @Slot()
    def toggle_review(self):
        try:
            self.is_review_active = not self.is_review_active
            if self.is_review_active:
                self.pipeline.add("review")
            else:
                self.pipeline.remove("review")
            self.isReviewActiveChanged.emit()
            self.logger.info(str(self) + ".toggle_review")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    @Slot()
    def toggle_dual_language(self):
        try:
            self.is_dual_language_active = not self.is_dual_language_active
            if self.is_dual_language_active:
                self.pipeline.add("dual language")
            else:
                self.pipeline.remove("dual language")
            self.isDualLanguageActiveChanged.emit()
            self.logger.info(str(self) + ".toggle_dual_language")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    @Slot()
    def toggle_image_translation(self):
        try:
            self.is_image_translation_active = not self.is_image_translation_active
            if self.is_image_translation_active:
                self.pipeline.add("image translation")
            else:
                self.pipeline.remove("image translation")
            self.isImageTranslationActiveChanged.emit()
            self.logger.info(str(self) + ".toggle_image_translation")
        except Exception as e:
            self.logger.error(str(self) + str(e))
    
    @Slot()
    def close(self):
        try:
            self.pipeline = set(self.config_data.translate_pipeline)
            self.is_ruby_removal_active = "ruby removal" in self.pipeline
            self.is_pn_extract_active = "pn extract" in self.pipeline
            self.is_pn_dict_edit_active = "pn dict edit" in self.pipeline
            self.is_main_translation_active = "main translation" in self.pipeline
            self.is_toc_translation_active = "toc translation" in self.pipeline
            self.is_review_active = "review" in self.pipeline
            self.is_dual_language_active = "dual language" in self.pipeline
            self.is_image_translation_active = "image translation" in self.pipeline

            self.isRubyRemovalActiveChanged.emit()
            self.isPnExtractActiveChanged.emit()
            self.isPnDictEditActiveChanged.emit()
            self.isMainTranslationActiveChanged.emit()
            self.isTocTranslationActiveChanged.emit()
            self.isReviewActiveChanged.emit()
            self.isDualLanguageActiveChanged.emit()
            self.isImageTranslationActiveChanged.emit()

            self.app_controller.popCurrentPage.emit()
            self.logger.info(str(self) + ".close")
        except Exception as e:
            self.logger.error(str(self) + str(e))

    @Slot()
    def save_pipeline(self):
        try:
            self.config_data.translate_pipeline = list(self.pipeline)
            save_config(self.config_data.to_dict())
            self.app_controller.popCurrentPage.emit()
            self.logger.info(str(self) + ".__init__")
        except Exception as e:
            self.logger.error(str(self) + str(e))
    
    @Slot()
    def open_pipeline_guide(self):
        pass