from abc import ABC, abstractmethod

class BaseTranslateCore(ABC):
    @abstractmethod
    def setup(self, 
              key: str | None,
              system_instruction: str | None, 
              max_output_token: int | None,
              temperature: float | None,
              top_p: float | None,
              top_k: float | None,
              presence_penalty: float | None,
              frequency_penalty: float | None,
              include_thoughts: bool | None,
              thinking_budget: int | None):
        raise NotImplementedError()


class GeminiTranslateCore(BaseTranslateCore):
    pass

class VertexTranslateCore(BaseTranslateCore):
    pass
