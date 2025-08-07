from google import genai
from google.genai import types

from .gemini import GeminiTranslateCore
from .api_info import ApiInfo

class VertexTranslateCore(GeminiTranslateCore):
    def _create_client(self, api_info: ApiInfo) -> genai.Client:
        return genai.Client(
            http_options=types.HttpOptions(api_version="v1"),
            vertexai=True,
            project=api_info.project_id,
            location=api_info.project_location,
            credentials=api_info.credentials
        )