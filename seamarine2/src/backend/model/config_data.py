from .ai_model_config import AiModelConfig

class ConfigData:
    def __init__(self):
        self.version: str = ''
        self.data: dict = {}
        self.gemini_api_key: str = ''
        self.translate_pipeline: list[str] = ["ruby removal", "main translation", "review"]
        self.max_chunk_size: int = 4096
        self.max_concurrent_request: int = 1
        self.request_delay: int = 0
        self.pn_extract_model_config: AiModelConfig = AiModelConfig()
        self.main_translate_model_config: AiModelConfig = AiModelConfig()
        self.toc_translate_model_config: AiModelConfig = AiModelConfig()
        self.review_model_config: AiModelConfig = AiModelConfig()
        self.image_translate_model_config: AiModelConfig = AiModelConfig()

    def load(self, data: dict):
        self.data = data
        self.version = self.data.get('current_version', '')
        self.gemini_api_key = self.data.get('gemini_api_key', '')
        self.translate_pipeline = self.data.get('translate_pipeline', ["ruby removal", "main translation", "review"])
        self.max_chunk_size = self.data.get('max_chunk_size', 4096)
        self.max_concurrent_request = self.data.get('max_concurrent_request', 1)
        self.request_delay = self.data.get('request_delay', 0)
        self.pn_extract_model_config.load(data.get('pn_extract_model_config', {}))
        self.main_translate_model_config.load(data.get('main_translate_model_config', {}))
        self.toc_translate_model_config.load(data.get('toc_translate_model_config', {}))
        self.review_model_config.load(data.get('review_model_config', {}))
        self.image_translate_model_config.load(data.get('image_translate_model_config', {}))

    def to_dict(self):
        return {
            'current_version': self.version,
            'gemini_api_key': self.gemini_api_key,
            'translate_pipeline': self.translate_pipeline,
            'max_chunk_size': self.max_chunk_size,
            'max_concurrent_request': self.max_concurrent_request,
            'request_delay': self.request_delay,
            'pn_extract_model_config': self.pn_extract_model_config.to_dict(),
            'main_translate_model_config': self.main_translate_model_config.to_dict(),
            'toc_translate_model_config': self.toc_translate_model_config.to_dict(),
            'review_model_config': self.review_model_config.to_dict(),
            'image_translate_model_config': self.image_translate_model_config.to_dict()
        }

        
        
