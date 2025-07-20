import os
import csv
from PySide6.QtCore import QAbstractListModel, QModelIndex, Signal, Slot, Property, QObject, Qt
from PySide6 import QtCore
from logger_config import setup_logger
from enum import IntEnum, auto
from utils.pn_dict import save_dict
from backend.model import RuntimeData, ConfigData
from backend.controller import AppController

class PnDictEditViewModel(QObject):
    saveSucceed = Signal()
    saveFailed = Signal()
    closePage = Signal()

    def __init__(self, config_data, runtime_data, app_controller, parent=None):
        super().__init__(parent)
        self._logger = setup_logger()
        try:
            self._model: PnDictModel = PnDictModel()
            self._config_data: ConfigData = config_data
            self._runtime_data: RuntimeData = runtime_data
            self._app_controller: AppController = app_controller
            self.load_csv()
            self._logger.info(str(self) + ".__init__")
        except Exception as e:
            self._logger.error(str(self) + str(e))

    def load_csv(self):
        try:
            with open(self._runtime_data.pn_dict_file, newline='', encoding='utf-8') as f:
                self._model = PnDictModel()
                reader = csv.reader(f)
                for row in reader:
                    if len(row) >= 2:
                        self._model.add_term(row[0].strip(), row[1].strip())
        except Exception as e:
            self._logger.error(str(self) + str(e))
            if not os.path.exists(self._runtime_data.pn_dict_file):
                try:
                    os.makedirs(os.path.dirname(self._runtime_data.pn_dict_file), exist_ok=True)
                    save_dict(self._runtime_data.pn_dict_file, [])
                    with open(self._runtime_data.pn_dict_file, newline='', encoding='utf-8') as f:
                        self._model = PnDictModel()
                        reader = csv.reader(f)
                        for row in reader:
                            if len(row) >= 2:
                                self._model.add_term(row[0].strip(), row[1].strip())
                except Exception as e:
                    self._logger.error("Not directory non-existence error: " + str(self) + str(e))

    @Slot()
    def lazy_init(self):
        try:
            self.load_csv()
            self._logger.info(str(self) + ".lazy_init")
        except Exception as e:
            self._logger.error(str(self) + ".lazy_init\n->" + str(e))
            
    @Slot()
    def save_csv(self):
        try:
            data_to_save = self._model.get_all_data()
            
            save_dict(os.path.basename(self._runtime_data.pn_dict_file), data_to_save)
            
            self._logger.info(f"Data successfully saved to {self._runtime_data.pn_dict_file}, {str(data_to_save)}")
            self.saveSucceed.emit()

        except Exception as e:
            self._logger.error(f"Failed to save data to {self._runtime_data.pn_dict_file}: {e}")
            self.saveFailed.emit()

    @Slot(int, str, str)
    def update_data(self, index, role, value):
        try:
            if role == "from":
                role = ListElementRoles.FROM
            elif role == "to":
                role = ListElementRoles.TO
            else:
                role = ListElementRoles.INDEX
                value = int(value)
            self._model.setData(index, value, role)
            self.dataChanged.emit()
            self._logger.info(str(self) + f".update_data({index}, {role}, {value})")
        except Exception as e:
            self._logger.error(str(self) + f".update_data({index}, {role}, {value})\n-> " + str(e))
    
    @Slot(int)
    def remove_row(self, index):
        try:
            for i in range(index+1, self._model.len()):
                self._model.setData(i, i-1, ListElementRoles.INDEX)
            self._model.removeRow(index)
            self.dataChanged.emit()
            self._logger.info(str(self) + f".remove_row({index})")
        except Exception as e:
            self._logger.error(str(self) + f".remove_row({index})\n->" + str(e))
    
    @Slot()
    def add_row(self):
        try:
            self._model.add_term("", "")
            self._logger.info(str(self) + ".add_row")
        except Exception as e:
            self._logger.error(str(self) + ".add_row\n->" + str(e))

    @Slot()
    def close(self):
        try:
            self.load_csv()
            self._app_controller.popCurrentPage.emit()
            self._logger.info(str(self) + ".close")
        except Exception as e:
            self._logger.error(str(self) + ".close" + str(e))


    
    dataChanged = Signal()
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



class ListElementRoles(IntEnum):
    FROM = Qt.UserRole
    TO = auto()
    INDEX = auto()

_role_names = {
    ListElementRoles.FROM: b'from',
    ListElementRoles.TO: b'to',
    ListElementRoles.INDEX: b'index'
}