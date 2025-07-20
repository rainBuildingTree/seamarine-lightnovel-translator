from PySide6.QtCore import QObject, Slot, Signal, Property
from backend.controller import AppController
from logger_config import setup_logger
from backend.model import ConfigData, RuntimeData, AiModelConfig
from utils.config import get_default_config, save_config

class ReviewSettingViewModel(QObject):
    def __init__(self, config_data: ConfigData, runtime_data, app_controller, parent=None):
        super().__init__(parent)
        self.logger = setup_logger()
        try:
            self._config_data: ConfigData = config_data
            self._runtime_data: RuntimeData = runtime_data
            self._app_controller: AppController = app_controller
            self._ai_config: AiModelConfig = config_data.review_model_config
            
            self._llm_model_name: str = self._ai_config.name
            self._sys_prompt: str = self._ai_config.system_prompt
            self._temp: float = self._ai_config.temperature
            self._top_p: float = self._ai_config.top_p
            self._freq_penalty: float = self._ai_config.frequency_penalty
            self._thinking_budget: int = self._ai_config.thinking_budget
            self._use_thinking_budget: bool = self._ai_config.use_thinking_budget
            self._is_save_succeed = False
            self._is_save_failed = False

            self.logger.info(str(self) + ".__init__")
        except Exception as e:
            self.logger.error(str(self) + str(e))
    
    llmModelListChanged = Signal()
    @Property(list, notify=llmModelListChanged)
    def llmModelList(self):
        return self._runtime_data.gemini_model_list

    llmModelNameChanged = Signal()
    @Property(str, notify=llmModelNameChanged)
    def llmModelName(self):
        return self._llm_model_name
    
    llmModelIndexChanged = Signal()
    @Property(int, notify=llmModelIndexChanged)
    def llmModelIndex(self):
        try:
            return self._runtime_data.gemini_model_list.index(self._llm_model_name)
        except Exception as e:
            self.logger.error(str(self) + str(e))
            return 0
    
    sysPromptChanged = Signal()
    def setSysPrompt(self, value: str):
        self._sys_prompt = value
        self.sysPromptChanged.emit()
    def getSysPrompt(self) -> str: 
        return self._sys_prompt
    sysPrompt = Property(str, getSysPrompt, setSysPrompt, notify=sysPromptChanged)
    
    tempChanged = Signal()
    def setTemp(self, value: float):
        self._temp = value
        self.tempChanged.emit()
        self.logger.info(value)
    def getTemp(self) -> float:
        return self._temp
    temp = Property(float, getTemp, setTemp, notify=tempChanged)
    
    topPChanged = Signal()
    def setTopP(self, value: float):
        self._top_p = value
        self.topPChanged.emit()
    def getTopP(self) -> float:
        return self._top_p
    topP = Property(float, getTopP, setTopP, notify=topPChanged)
    
    freqPenaltyChanged = Signal()
    def setFreqPenalty(self, value: float):
        self._freq_penalty = value
        self.freqPenaltyChanged.emit()
    def getFreqPenalty(self) -> float:
        return self._freq_penalty
    freqPenalty = Property(float, getFreqPenalty, setFreqPenalty, notify=freqPenaltyChanged)
    
    thinkingBudgetChanged = Signal()
    def setThinkingBudget(self, value: int):
        self._thinking_budget = value
        self.thinkingBudgetChanged.emit()
    def getThinkingBudget(self) -> int:
        return self._thinking_budget
    thinkingBudget = Property(int, getThinkingBudget, setThinkingBudget, notify=thinkingBudgetChanged)
    
    useThinkingBudgetChanged = Signal()
    def setUseThinkingBudget(self, value: bool):
        self._use_thinking_budget = value
        self.useThinkingBudgetChanged.emit()
    def getUseThinkingBudget(self) -> bool:
        return self._use_thinking_budget
    useThinkingBudget = Property(bool, getUseThinkingBudget, setUseThinkingBudget, notify=useThinkingBudgetChanged)
    
    saveSucceedChanged = Signal()
    @Property(bool, notify=saveSucceedChanged)
    def saveSucceed(self):
        return self._is_save_succeed
    
    saveFailedChanged = Signal()
    @Property(bool, notify=saveFailedChanged)
    def saveFailed(self):
        return self._is_save_failed

    @Slot()
    def open_guide_link(self):
        pass
    @Slot(int)
    def update_model(self, index):
        try:
            self._llm_model_name = self._runtime_data.gemini_model_list[index]
        except Exception as e:
            self.logger.error(str(self) + str(e))
    
    @Slot()
    def save_data(
        self, 
        ):
        try:
            if self._llm_model_name not in self._runtime_data.gemini_model_list:
                raise Exception(f"Invalid llm model name detected ({self._llm_model_name}, name not in the available model list of ({self._runtime_data.gemini_model_list}))")
            if self._temp < 0.0 or self._temp > 2.0:
                raise Exception(f"Invalid temperature value detected ({self._temp}, should be [0.0, 2.0])")
            if self._top_p < 0.0 or self._top_p > 1.0:
                raise Exception(f"Invalid top p value detected ({self._top_p}, should be [0.0, 1.0])")
            if self._freq_penalty < -2.0 or self._freq_penalty > 2.0:
                raise Exception(f"Invalid frequency penalty value detected ({self._freq_penalty}, should be [-2.0, 2.0])")
            if self._thinking_budget < -1 or self._thinking_budget > 24576:
                raise Exception(f"Invalid thinking budget")
            
            self._ai_config.name = self._llm_model_name
            self._ai_config.system_prompt = self._sys_prompt
            self._ai_config.temperature = self._temp
            self._ai_config.top_p = self._top_p
            self._ai_config.frequency_penalty = self._freq_penalty
            self._ai_config.thinking_budget = self._thinking_budget
            self._ai_config.use_thinking_budget = self._use_thinking_budget

            self.llmModelNameChanged.emit()
            self.llmModelIndexChanged.emit()
            self.sysPromptChanged.emit()
            self.tempChanged.emit()
            self.topPChanged.emit()
            self.freqPenaltyChanged.emit()
            self.thinkingBudgetChanged.emit()
            self.useThinkingBudgetChanged.emit()

            self._config_data.review_model_config = self._ai_config
            save_config(self._config_data.to_dict())

            self._is_save_failed = False
            self._is_save_succeed = True
            self.saveFailedChanged.emit()
            self.saveSucceedChanged.emit()

            self.logger.info(str(self) + f".save_data")
        except Exception as e:
            self._is_save_succeed = False
            self._is_save_failed = True
            self.saveSucceedChanged.emit()
            self.saveFailedChanged.emit()
            self.logger.error(str(self) + str(e))

    @Slot()
    def close(self):
        try:
            self._llm_model_name: str = self._ai_config.name
            self._sys_prompt: str = self._ai_config.system_prompt
            self._temp: float = self._ai_config.temperature
            self._top_p: float = self._ai_config.top_p
            self._freq_penalty: float = self._ai_config.frequency_penalty
            self._thinking_budget: int = self._ai_config.thinking_budget
            self._use_thinking_budget: bool = self._ai_config.use_thinking_budget
            self._is_save_succeed = False
            self._is_save_failed = False

            self.llmModelNameChanged.emit()
            self.llmModelIndexChanged.emit()
            self.sysPromptChanged.emit()
            self.tempChanged.emit()
            self.topPChanged.emit()
            self.freqPenaltyChanged.emit()
            self.thinkingBudgetChanged.emit()
            self.useThinkingBudgetChanged.emit()
            self.saveFailedChanged.emit()
            self.saveSucceedChanged.emit()

            self._app_controller.popCurrentPage.emit()
        
            self.logger.info(str(self) + ".close")
        except Exception as e:
            self.logger.error(str(self) + str(e))      

    @Slot(str)
    def set_default(self, property: str):
        try:
            if 'name' in property:
                self._llm_model_name = get_default_config().get('review_model_config').get('name')
                self.llmModelNameChanged.emit()
                self.llmModelIndexChanged.emit()
            elif 'prompt' in property:
                self._sys_prompt = get_default_config().get('review_model_config').get('system_prompt')
                self.sysPromptChanged.emit()
            elif 'temp' in property:
                self._temp = get_default_config().get('review_model_config').get('temperature')
                self.tempChanged.emit()
            elif 'top' in property:
                self._top_p = get_default_config().get('review_model_config').get('top_p')
                self.topPChanged.emit()
            elif 'freq' in property:
                self._freq_penalty = get_default_config().get('review_model_config').get('frequency_penalty')
                self.freqPenaltyChanged.emit()
            elif 'use' in property:
                self._use_thinking_budget = get_default_config().get('review_model_config').get('use_thinking_budget')
                self.useThinkingBudgetChanged.emit()
            elif 'thinking' in property:
                self._thinking_budget = get_default_config().get('review_model_config').get('thinking_budget')
            else:
                raise Exception(f"Undefined behavior of defaulting property ({property})")
            self.logger.info(str(self) + f".set_default({property})")
        except Exception as e:
            self.logger.error(str(self) + str(e))
