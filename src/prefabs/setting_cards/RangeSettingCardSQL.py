from typing import Union

from PySide6.QtCore import QTimer
from PySide6.QtGui import QIcon
from qfluentwidgets import FluentIconBase, RangeSettingCard

from prefabs.config.qconfig_sql import qconfig_custom


class RangeSettingCardSQL(RangeSettingCard):
    def __init__(self, configItem, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None):
        super().__init__(configItem, icon, title, content, parent)

        # Timer to buffer database writes
        self._save_timer = QTimer()
        self._save_timer.setSingleShot(True)
        self._save_timer.timeout.connect(self._saveToDatabase)

        # # Set fixed width for value label to prevent shifting
        # max_value = max(abs(configItem.range[0]), abs(configItem.range[1]))
        # max_digits = len(str(max_value))
        # label_width = max_digits * 10 + 10
        # self.valueLabel.setFixedWidth(label_width)
        # self.valueLabel.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        # Disconnect parent's immediate DB update and connect our buffered version
        self.slider.valueChanged.disconnect(self._RangeSettingCard__onValueChanged)
        self.slider.valueChanged.connect(self._onValueChangedBuffered)

    def _onValueChangedBuffered(self, value: int):
        """Update UI immediately, buffer database writes"""
        # Update visual label immediately
        self.valueLabel.setNum(value)

        # Restart timer - this buffers rapid changes
        self._save_timer.stop()
        self._save_timer.start(300)  # 300ms delay

    def _saveToDatabase(self):
        """Save current value to database"""
        current_value = self.slider.value()
        self._RangeSettingCard__onValueChanged(current_value)

    def setValue(self, value):
        qconfig_custom.set(self.configItem, value)
        self.valueLabel.setNum(value)
        self.slider.setValue(value)
