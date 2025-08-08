from google import genai
from google.genai import types

from .gemini import GeminiTranslateCore
from .api_info import ApiInfo

class VertexTranslateCore(GeminiTranslateCore):
    def __init__(self,
                 project_id: str,
                 location: str,
                 credentials: str,
                 model: str,
                 system_instruction: str | None     = None,
                 max_output_token: int | None       = None,
                 temperature: float | None          = None,
                 top_p: float | None                = None,
                 presence_penalty: float | None     = None,
                 frequency_penalty: float | None    = None,
                 thinking_budget: int | None        = None):
        self._client = genai.Client(
            http_options=types.HttpOptions(api_version="v1"),
            vertexai=True,
            project=project_id,
            location=location,
            credentials=credentials
        )
        super().__init__(
            api_key             = None,
            model               = model,
            system_instruction  = system_instruction,
            max_output_token    = max_output_token,
            temperature         = temperature,
            top_p               = top_p,
            presence_penalty    = presence_penalty,
            frequency_penalty   = frequency_penalty,
            thinking_budget     = thinking_budget
        )