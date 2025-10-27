from typing import Tuple, Type, Union

from PySide6.QtCore import QObject, Signal
from qfluentwidgets import ConfigSerializer, ConfigValidator
from sqlalchemy.orm import InstrumentedAttribute  # for type hinting of sqlalchemy columns

from models.dbTables import Base


class ConfigItemSQL(QObject):
    valueChanged = Signal(object)

    def __init__(
        self,
        db_table: Type[Base],
        db_column: InstrumentedAttribute,
        default: Union[bool, int],  # TODO: int is for RangeConfigItemSQL, so for ConfigItemSQL it should be only bool
        validator: ConfigValidator = None,
        serializer: ConfigSerializer = None,
        restart: bool = False,
    ) -> None:
        super().__init__()
        self.db_table = db_table
        self.db_column = db_column
        self.validator = validator or ConfigValidator()
        self.serializer = serializer or ConfigSerializer()
        self.__value = default
        self.value = default
        self.restart = restart
        self.defaultValue = self.validator.correct(default)

    @property
    def value(self) -> Union[bool, int]:
        return self.__value

    @value.setter
    def value(self, v: Union[bool, int]) -> None:
        v = self.validator.correct(v)
        ov = self.__value
        self.__value = v
        if ov != v:
            self.valueChanged.emit(v)

    def serialize(self) -> str:
        return self.serializer.serialize(self.value)

    def deserializeFrom(self, value: Union[bool, int]) -> None:
        self.value = self.serializer.deserialize(value)


class RangeConfigItemSQL(ConfigItemSQL):
    """Config item of range"""

    @property
    def range(self) -> Tuple[int, int]:
        """get the available range of config"""
        return self.validator.range

    def __str__(self) -> str:
        return f"{self.__class__.__name__}[range={self.range}, value={self.value}]"
