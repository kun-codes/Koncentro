from typing import Optional, Union

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIconBase, RangeConfigItem, qconfig

from prefabs.setting_cards.SpinBoxSettingCardSQL import SpinBoxSettingCardSQL


class SpinBoxSettingCard(SpinBoxSettingCardSQL):
    def __init__(
        self,
        configItem: RangeConfigItem,
        icon: Union[str, QIcon, FluentIconBase],
        title: str,
        content: Optional[str] = None,
        parent: Optional[QWidget] = None,
    ) -> None:
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

    def setValue(self, value: int) -> None:
        qconfig.set(self.configItem, value)
        self.spinBox.setValue(value)
