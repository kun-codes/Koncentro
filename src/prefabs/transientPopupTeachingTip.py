from loguru import logger
from PySide6.QtCore import QPropertyAnimation
from qfluentwidgets import FluentWindow, PopupTeachingTip, TeachingTipTailPosition, TeachingTipView

from constants import InterfaceType


class TransientPopupTeachingTip(PopupTeachingTip):
    def __init__(self, view, target, duration=1000,
                 tailPosition=TeachingTipTailPosition.BOTTOM, parent=None, isDeleteOnClose=True):
        super().__init__(view, target, duration, tailPosition, parent, isDeleteOnClose)

        self.mainWindow: FluentWindow = None
        self.interface_type: InterfaceType = None

    def connectSignalsToSlots(self):
        if self.mainWindow and hasattr(self.mainWindow, 'stackedWidget'):
            self.mainWindow.stackedWidget.currentChanged.connect(self.onTabChanged)
            logger.debug(f"Connected stackedWidget.currentChanged in {self.__class__.__name__}")

    def onTabChanged(self, index):
        logger.debug(f"Tab changed to index: {index}")

        if self.interface_type.value == InterfaceType.DIALOG.value:  # no need to hide or show teaching tip
            # if teaching tip is used on a dialog
            return

        if index == self.interface_type.value:
            self.temporaryShow()
        else:
            self.temporaryHide()

    def temporaryHide(self):
        """Hide the teaching tip with fade animation without closing it"""
        if self.isVisible():
            self.hideAni = QPropertyAnimation(self, b'windowOpacity', self)
            self.hideAni.setDuration(84)
            self.hideAni.setStartValue(1)
            self.hideAni.setEndValue(0)
            self.hideAni.finished.connect(self.hide)
            self.hideAni.start()

    def temporaryShow(self):
        """Show the teaching tip with fade animation"""
        if not self.isVisible():
            self.setWindowOpacity(0)
            self.show()
            self.showAni = QPropertyAnimation(self, b'windowOpacity', self)
            self.showAni.setDuration(84)
            self.showAni.setStartValue(0)
            self.showAni.setEndValue(1)
            self.showAni.start()
            self.move(self.manager.position(self))

    @classmethod
    def create(cls, target, title, content, mainWindow, interface_type: InterfaceType, icon=None, image=None,
               isClosable=True, duration=1000, tailPosition=TeachingTipTailPosition.BOTTOM,
               parent=None, isDeleteOnClose=True):
        """Create a temporary popup teaching tip."""
        view = TeachingTipView(title, content, icon, image, isClosable, tailPosition)
        tip = cls(view, target, duration, tailPosition, parent, isDeleteOnClose)

        tip.mainWindow = mainWindow
        tip.interface_type = interface_type
        tip.connectSignalsToSlots()

        # view.closed.connect(tip.close)

        # Explicitly show the teaching tip
        tip.show()
        return tip
