from typing import TYPE_CHECKING, Optional, Union

from loguru import logger
from PySide6.QtCore import QPropertyAnimation
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import QWidget
from qfluentwidgets import (
    FluentIconBase,
    FluentWindow,
    FlyoutViewBase,
    PopupTeachingTip,
    TeachingTipTailPosition,
)

from constants import InterfaceType
from prefabs.skipTutorialTeachingTipView import SkipTutorialTeachingTipView

if TYPE_CHECKING:
    from mainWindow import MainWindow


class TransientPopupTeachingTip(PopupTeachingTip):
    def __init__(
        self,
        view: FlyoutViewBase,
        target: QWidget,
        duration: int = 1000,
        tailPosition: TeachingTipTailPosition = TeachingTipTailPosition.BOTTOM,
        parent: Optional[QWidget] = None,
        isDeleteOnClose: bool = True,
    ) -> None:
        super().__init__(view, target, duration, tailPosition, parent, isDeleteOnClose)

        self.mainWindow: Optional[FluentWindow] = None
        self.interface_type: Optional[InterfaceType] = None

    def connectSignalsToSlots(self) -> None:
        if self.mainWindow and hasattr(self.mainWindow, "stackedWidget"):
            self.mainWindow.stackedWidget.currentChanged.connect(self.onTabChanged)
            logger.debug(f"Connected stackedWidget.currentChanged in {self.__class__.__name__}")

    def onTabChanged(self, index: int) -> None:
        logger.debug(f"Tab changed to index: {index}")

        if self.interface_type.value == InterfaceType.DIALOG.value:  # no need to hide or show teaching tip
            # if teaching tip is used on a dialog
            return

        if index == self.interface_type.value:
            self.temporaryShow()
        else:
            self.temporaryHide()

    def temporaryHide(self) -> None:
        """Hide the teaching tip with fade animation without closing it"""
        if self.isVisible():
            self.hideAni = QPropertyAnimation(self, b"windowOpacity", self)
            self.hideAni.setDuration(84)
            self.hideAni.setStartValue(1)
            self.hideAni.setEndValue(0)
            self.hideAni.finished.connect(self.hide)
            self.hideAni.start()

    def temporaryShow(self) -> None:
        """Show the teaching tip with fade animation"""
        if not self.isVisible():
            self.setWindowOpacity(0)
            self.show()
            self.showAni = QPropertyAnimation(self, b"windowOpacity", self)
            self.showAni.setDuration(84)
            self.showAni.setStartValue(0)
            self.showAni.setEndValue(1)
            self.showAni.start()
            self.move(self.manager.position(self))

    @classmethod
    def create(
        cls,
        target: QWidget,
        title: str,
        content: str,
        mainWindow: "MainWindow",
        interface_type: InterfaceType,
        icon: Union[FluentIconBase, QIcon, str] = None,
        image: Union[str, QPixmap, QImage] = None,
        isClosable: bool = True,
        duration: int = 1000,
        tailPosition: TeachingTipTailPosition = TeachingTipTailPosition.BOTTOM,
        parent: Optional[QWidget] = None,
        isDeleteOnClose: bool = True,
    ) -> "TransientPopupTeachingTip":
        """Create a temporary popup teaching tip."""
        view = SkipTutorialTeachingTipView(title, content, icon, image, isClosable, tailPosition)
        tip = cls(view, target, duration, tailPosition, parent, isDeleteOnClose)

        tip.mainWindow = mainWindow
        tip.interface_type = interface_type
        tip.connectSignalsToSlots()

        # view.closed.connect(tip.close)

        # Explicitly show the teaching tip
        tip.show()
        return tip
