from abc import ABC, abstractmethod

class TranslateCore(ABC):
    @abstractmethod
    def get_model_list(self):
        raise NotImplementedError()
    
    @abstractmethod
    def count_tokens(self):
        raise NotImplementedError()
    
    @abstractmethod
    def generate_content(self):
        raise NotImplementedError