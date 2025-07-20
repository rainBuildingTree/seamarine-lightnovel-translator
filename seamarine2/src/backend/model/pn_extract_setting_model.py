class PnExtractSettingModel:
    def __init__(
        self, 
        llm_model_name_list: list[str],
        llm_model_name: str, 
        system_prompt: str, 
        temperature: float, 
        top_p: float, 
        freq_penalty: float, 
        thinking_budget: int,
    ):
        self.model_list: list[str] = llm_model_name_list
        self.model_name: str = llm_model_name
        self.system_prompt: str = system_prompt
        self.temperature: float = temperature
        self.top_p: float = top_p
        self.freq_penalty: float = freq_penalty
        self.thinking_budget: int = thinking_budget
