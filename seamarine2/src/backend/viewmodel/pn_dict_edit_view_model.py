import os
import csv
from PySide6.QtCore import QAbstractListModel, QModelIndex, Signal, Slot, Property, QObject, Qt
from PySide6 import QtCore
from logger_config import setup_logger
from enum import IntEnum, auto
from utils.pn_dict import save_dict
from backend.model import RuntimeData, ConfigData
from backend.controller import AppController
from abc import ABC, abstractmethod, ABCMeta

class QABCMeta(type(QObject), ABCMeta):
    """QObject의 메타클래스와 ABCMeta를 결합한 메타클래스"""
    pass

class BaseDictEditViewModel(QObject, ABC, metaclass=QABCMeta):
    """
    사전(Dictionary) 편집 ViewModel의 공통 로직을 담는 추상 베이스 클래스.
    상속받는 클래스는 _get_dict_file_path 메소드를 반드시 구현해야 합니다.
    """
    saveSucceed = Signal()
    saveFailed = Signal()
    closePage = Signal()
    dataChanged = Signal()

    def __init__(self, config_data, runtime_data, app_controller, parent=None):
        super().__init__(parent)
        self._logger = setup_logger()
        try:
            self._model: PnDictModel = PnDictModel()
            self._config_data: ConfigData = config_data
            self._runtime_data: RuntimeData = runtime_data
            self._app_controller: AppController = app_controller
            self.load_csv()
            self._logger.info(f"{self.__class__.__name__}.__init__")
        except Exception as e:
            self._logger.error(f"{self.__class__.__name__}: {e}")

    @abstractmethod
    def _get_dict_file_path(self) -> str:
        """
        자식 클래스에서 CSV 파일의 전체 경로를 반환하도록 구현해야 하는 추상 메소드.
        """
        raise NotImplementedError("Subclasses must implement _get_dict_file_path()")

    def load_csv(self):
        file_path = self._get_dict_file_path()
        try:
            with open(file_path, newline='', encoding='utf-8') as f:
                self._model = PnDictModel()
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        self._model.add_term(row[0].strip(), row[1].strip())
        except FileNotFoundError:
            self._logger.warning(f"File not found: {file_path}. Creating a new file.")
            try:
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    pass
                self._model = PnDictModel()
            except Exception as e:
                self._logger.error(f"Failed to create directory or file for {file_path}: {e}")
        except Exception as e:
            self._logger.error(f"Error loading {file_path}: {e}")


    @Slot()
    def save_csv(self):
        file_path = self._get_dict_file_path()
        try:
            data_to_save = self._model.get_all_data()
            
            save_dict(os.path.basename(file_path), data_to_save)
            
            self._logger.info(f"Data successfully saved to {file_path}, {str(data_to_save)}")
            self.saveSucceed.emit()

        except Exception as e:
            self._logger.error(f"Failed to save data to {file_path}: {e}")
            self.saveFailed.emit()


    @Slot()
    def lazy_init(self):
        try:
            self.load_csv()
            self._logger.info(f"{self.__class__.__name__}.lazy_init")
        except Exception as e:
            self._logger.error(f"{self.__class__.__name__}.lazy_init\n->{e}")

    @Slot(int, str, str)
    def update_data(self, index, role, value):
        try:
            if role == "from": role_enum = ListElementRoles.FROM
            elif role == "to": role_enum = ListElementRoles.TO
            else:
                role_enum = ListElementRoles.INDEX
                value = int(value)
            self._model.setData(index, value, role_enum)
            self.dataChanged.emit()
            self._logger.info(f"{self.__class__.__name__}.update_data({index}, {role}, {value})")
        except Exception as e:
            self._logger.error(f"{self.__class__.__name__}.update_data({index}, {role}, {value})\n-> {e}")

    @Slot(int)
    def remove_row(self, index):
        try:
            for i in range(index + 1, self._model.len()):
                self._model.setData(i, i - 1, ListElementRoles.INDEX)
            self._model.removeRow(index)
            self.dataChanged.emit()
            self._logger.info(f"{self.__class__.__name__}.remove_row({index})")
        except Exception as e:
            self._logger.error(f"{self.__class__.__name__}.remove_row({index})\n->{e}")

    @Slot()
    def add_row(self):
        try:
            self._model.add_term("", "")
            self.dataChanged.emit()
            self._logger.info(f"{self.__class__.__name__}.add_row")
        except Exception as e:
            self._logger.error(f"{self.__class__.__name__}.add_row\n->{e}")

    @Slot()
    def close(self):
        try:
            self.load_csv()
            self._app_controller.popCurrentPage.emit()
            self._logger.info(f"{self.__class__.__name__}.close")
        except Exception as e:
            self._logger.error(f"{self.__class__.__name__}.close: {e}")

    def get_data(self):
        return self._model
    def set_data(self, value):
        self._model = value
        self.dataChanged.emit()
    data = Property(QObject, get_data, set_data, notify=dataChanged)


class PnDictModel(QAbstractListModel):
    def __init__(self):
        super().__init__()
        self._data = []

    def add_term(self, term_from, term_to):
        new_row = {
            ListElementRoles.FROM: term_from,
            ListElementRoles.TO: term_to,
            ListElementRoles.INDEX: len(self._data)
        }
        self._data.append(new_row)
    
    def roleNames(self):
        return _role_names

    def rowCount(self, parent=QModelIndex()):
        return len(self._data)
    
    def data(self, index, role):
        if role not in list(ListElementRoles):
            return None
        
        try:
            element = self._data[index.row()]
        except IndexError:
            return None

        if role in element:
            return element[role]
        return None
    
    def setData(self, index, value, role):
        try:
            data_row = self._data[index]
        except IndexError:
            return False

        data_row[role] = value
        self.dataChanged.emit(index, index, [role])
        return True
    
    def removeRow(self, index):
        try:
            self._data.remove(self._data[index])
        except IndexError:
            return False
        return True
    
    def get_all_data(self):
        return [
            [row[ListElementRoles.FROM], row[ListElementRoles.TO]]
            for row in self._data
        ]
    
    def len(self):
        return len(self._data)
    
class PnDictEditViewModel(BaseDictEditViewModel):
    """PN 사전을 편집하는 ViewModel"""
    def _get_dict_file_path(self) -> str:
        """PN 사전 파일 경로를 반환합니다."""
        return self._runtime_data.pn_dict_file

class UserDictEditViewModel(BaseDictEditViewModel):
    """사용자 사전을 편집하는 ViewModel"""
    def _get_dict_file_path(self) -> str:
        """사용자 사전 파일 경로를 반환합니다."""
        return self._runtime_data.user_dict_file

class ListElementRoles(IntEnum):
    FROM = Qt.UserRole
    TO = auto()
    INDEX = auto()

_role_names = {
    ListElementRoles.FROM: b'from',
    ListElementRoles.TO: b'to',
    ListElementRoles.INDEX: b'index'
}