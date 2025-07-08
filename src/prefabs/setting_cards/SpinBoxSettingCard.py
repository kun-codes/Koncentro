from typing import Union

from PySide6.QtGui import QIcon
from qfluentwidgets import FluentIconBase, qconfig

from prefabs.setting_cards.SpinBoxSettingCardSQL import SpinBoxSettingCardSQL


class SpinBoxSettingCard(SpinBoxSettingCardSQL):
    def __init__(self, configItem, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None) -> None:
        """
        Parameters
        ----------
        configItem: RangeConfigItem
            configuration item operated by the card

        icon: str | QIcon | FluentIconBase
            the icon to be drawn

        title: str
            the title of card

        content: str
            the content of card

        parent: QWidget
            parent widget
        """
        super().__init__(configItem, icon, title, content, parent)

    def setValue(self, value) -> None:
        qconfig.set(self.configItem, value)
        self.spinBox.setValue(value)
