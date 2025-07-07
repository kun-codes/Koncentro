from typing import Type

from PySide6.QtCore import QObject, Signal
from qfluentwidgets import ConfigSerializer, ConfigValidator
from sqlalchemy.orm import InstrumentedAttribute  # for type hinting of sqlalchemy columns

from models.db_tables import Base


class ConfigItemSQL(QObject):
    valueChanged = Signal(object)

    def __init__(
        self,
        db_table: Type[Base],
        db_column: InstrumentedAttribute,
        default,
        validator=None,
        serializer=None,
        restart=False,
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
    def value(self):
        return self.__value

    @value.setter
    def value(self, v) -> None:
        v = self.validator.correct(v)
        ov = self.__value
        self.__value = v
        if ov != v:
            self.valueChanged.emit(v)

    def serialize(self):
        return self.serializer.serialize(self.value)

    def deserializeFrom(self, value) -> None:
        self.value = self.serializer.deserialize(value)


class RangeConfigItemSQL(ConfigItemSQL):
    """Config item of range"""

    @property
    def range(self):
        """get the available range of config"""
        return self.validator.range

    def __str__(self) -> str:
        return f"{self.__class__.__name__}[range={self.range}, value={self.value}]"
