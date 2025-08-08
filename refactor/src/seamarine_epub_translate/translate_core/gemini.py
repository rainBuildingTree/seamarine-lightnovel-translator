import time, warnings
from google import genai
from google.genai import types, errors

from .base import TranslateCore

def _safe_clamp(value: int | float | None, lo: int | float, hi: int | float) -> int | float | None:
    if value is None:   return None
    else:               return max(lo, min(value, hi))

def _decode_maybe_bytes(data: str | bytes | None) -> str | None:
    if data is None:            return None
    if isinstance(data, bytes): return data.decode()
    else:                       return data

class GeminiTranslateCore(TranslateCore):
    OFF_SAFETY_SETTING = [
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
            threshold=types.HarmBlockThreshold.OFF
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
            threshold=types.HarmBlockThreshold.OFF
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
            threshold=types.HarmBlockThreshold.OFF
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
            threshold=types.HarmBlockThreshold.OFF
        ),
        types.SafetySetting(
            category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
            threshold=types.HarmBlockThreshold.OFF
        )
    ]

    def __init__(self,
                 api_key: str | None,
                 model: str,
                 system_instruction: str | None     = None,
                 max_output_token: int | None       = None,
                 temperature: float | None          = None,
                 top_p: float | None                = None,
                 presence_penalty: float | None     = None,
                 frequency_penalty: float | None    = None,
                 thinking_budget: int | None        = None):
        self._client: genai.Client = genai.Client(api_key=api_key) if not self._client else self._client

        model_info = self._client.models.get(model=model)
        if not ('generateContent' in model_info.supported_actions and 'countTokens' in model_info.supported_actions):
            raise KeyError(f"{model} does not support 'generateContent' or 'countTokens' action")
        self._model = model

        self._generate_content_config = types.GenerateContentConfig(
            system_instruction  = system_instruction,
            safety_settings     = self.OFF_SAFETY_SETTING,
            max_output_tokens   = _safe_clamp(max_output_token,     512,    model_info.output_token_limit),
            temperature         = _safe_clamp(temperature,          0.0,    2.0),
            top_p               = _safe_clamp(top_p,                0.0,    1.0),
            presence_penalty    = _safe_clamp(presence_penalty,    -2.0,    1.99),
            frequency_penalty   = _safe_clamp(frequency_penalty,   -2.0,    1.99),
            thinking_config     = types.ThinkingConfig(thinking_budget=self._resolve_thinking_budget(model, thinking_budget))
        )

    def get_model_list(self) -> list[tuple[str, str]]:
        available_models = self._client.models.list()
        return [
            (model_data.display_name, model_data.name.removeprefix('models/'))
            for model_data in available_models
        ]
    
    def count_tokens(self, contents: str | bytes) -> int:
        if not contents: return 0
        return self._client.models.count_tokens(self._model, _decode_maybe_bytes(contents)).total_tokens
    
    def generate_content(self, contents: str | bytes) -> str:
        if not contents:
            warnings.warn("Trying to generate content with empty input")
            contents = ""
        
        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=_decode_maybe_bytes(contents),
                config=self._generate_content_config
            )
        except errors.APIError as e:
            if e.code == 429:
                retry_delay = e.details.get('retryDelay', "10s")
                retry_delay = int(retry_delay[:-1])
                warnings.warn(f"Resource exhaustion(429) detected: retry after {retry_delay+5}s")
                time.sleep(retry_delay + 5)
                return self.generate_content(contents)
            else:
                raise

        if response.prompt_feedback and response.prompt_feedback.block_reason:
            raise RuntimeError(f"Gemini blocked the request with the reason ({response.prompt_feedback.block_reason})")
        if not response.text:
            return ""
        
        return response.text.strip()
    
    def _resolve_thinking_budget(self, model: str, budget: int | None) -> int | None:
        if budget is None:  return None
        if not model:       raise ValueError("Model is empty or none")

        model = model.lower()
        is_25 = 'gemini-2.5' in model
        is_pro = 'pro' in model
        is_lite = 'lite' in model

        if is_pro:      lo, hi = 128, 32768
        elif is_lite:   lo, hi = 512, 24576
        else:           lo, hi = 1, 24576

        if not is_25:                   return None
        if budget == -1:                return -1
        if not is_pro and budget == 0:  return 0

        return max(lo, min(int(budget), hi))