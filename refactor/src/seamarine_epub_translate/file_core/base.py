from abc import ABC, abstractmethod


class FileCore(ABC):
    @abstractmethod
    def get_dict_to_translate(self) -> dict[str, str]:
        raise NotImplementedError()

    @abstractmethod
    def update_dict_to_translate(self, updated_dict: dict[str, str]):
        raise NotImplementedError()

    @abstractmethod
    def attach_original(self):
        raise NotImplementedError()

    @abstractmethod
    def detach_original(self):
        raise NotImplementedError()

    @abstractmethod
    def apply_dictionary(self, dictionary: dict[str, str]):
        raise NotImplementedError()

    @abstractmethod
    def save(self, path: str | None):
        raise NotImplementedError()


