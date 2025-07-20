class AiModelConfig:
    def __init__(self):
        self.data: dict = {}
        self.name: str = "gemini-2.5-flash-preview-05-20"
        self.system_prompt: str = ''
        self.temperature: float = 1.0
        self.top_p: float = 0.95
        self.frequency_penalty: float = 0.0
        self.thinking_budget: int = 0
        self.use_thinking_budget: bool = False

    def load(self, data: dict):
        self.data = data
        print(str(data))

        self.name = data.get('name', 'gemini-2.5-flash-preview-05-20')
        self.system_prompt = data.get('system_prompt', '')
        self.temperature = data.get('temperature', 1.0)
        self.top_p = data.get('top_p', 0.95)
        self.frequency_penalty = data.get('frequency_penalty', 0.0)
        self.thinking_budget = data.get('thinking_budget', 0)
        self.use_thinking_budget = data.get('use_thinking_budget', False)

    def to_dict(self):
        return {
            'name': self.name,
            'system_prompt': self.system_prompt,
            'temperature': self.temperature,
            'top_p': self.top_p,
            'frequency_penalty': self.frequency_penalty,
            'thinking_budget': self.thinking_budget,
            'use_thinking_budget': self.use_thinking_budget
        }