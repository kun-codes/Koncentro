from loguru import logger
from PySide6.QtCore import QEvent, QPropertyAnimation, Qt, Signal
from qfluentwidgets import FluentWindow, TeachingTip, TeachingTipTailPosition, TeachingTipView

from constants import InterfaceType


class TargetClickTeachingTip(TeachingTip):
    """Teaching tip that only closes when the target widget is clicked."""

    def __init__(self, view, target, tailPosition=TeachingTipTailPosition.BOTTOM, parent=None, isDeleteOnClose=True):
        super().__init__(
            view, target, duration=-1, tailPosition=tailPosition, parent=parent, isDeleteOnClose=isDeleteOnClose
        )

        # Qt.ToolTip and Qt.FramelessWindowHint to fix to ensure TargetClickTeachingTip is positioned correctly on
        # wayland after this fix, TeachingTipTailPosition.RIGHT doesn't position correctly on wayland
        # however TOP, BOTTOM and LEFT work fine
        # Qt.Window.WindowTransparentForInput is used to ensure that the teaching tip does not block input events
        # at the corner of buttons because of overlap between its invisible border and the button on all platforms
        # the invisibile border is visible on flatpak wayland sessions
        self.setWindowFlags(Qt.WindowType.WindowTransparentForInput | Qt.ToolTip | Qt.FramelessWindowHint)

        # installing event filter on target to detect clicks
        self.target.installEventFilter(self)

        self.mainWindow: FluentWindow = None
        self.interface_type: InterfaceType = None
        self.customSignalToDestroy: Signal = False

    def connectSignalsToSlots(self):
        logger.debug(f"Inside connectSignalsToSlots of {self.__class__.__name__}")
        self.mainWindow.stackedWidget.currentChanged.connect(self.onTabChanged)
        if self.customSignalToDestroy is not None:
            self.customSignalToDestroy.connect(self._fadeOut)

    def onTabChanged(self, index):
        logger.debug(f"Tab changed to index: {index}")

        if self.interface_type.value == InterfaceType.DIALOG.value:  # no need to hide or show teaching tip
            # if teaching tip is used on a dialog
            return

        if index == self.interface_type.value:
            self.temporaryShow()
        else:
            self.temporaryHide()

    def eventFilter(self, obj, event):
        # Check if the target was clicked
        if self.customSignalToDestroy is None:  # delete when clicked on target
            if obj is self.target and event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self._fadeOut()
                    return False
        else:  # else temporary hide
            if obj is self.target and event.type() == QEvent.MouseButtonPress:
                if event.button() == Qt.LeftButton:
                    self.temporaryHide()
                    return False

        return super().eventFilter(obj, event)

    @classmethod
    def create(
        cls,
        target,
        title,
        content,
        mainWindow,
        interface_type: InterfaceType,
        icon=None,
        image=None,
        tailPosition=TeachingTipTailPosition.BOTTOM,
        parent=None,
        customSignalToDestroy: Signal = None,
    ):
        """Create a teaching tip that only closes when the target is clicked."""
        view = TeachingTipView(title, content, icon, image, False, tailPosition)
        tip = cls(view, target, tailPosition, parent, True)

        tip.mainWindow = mainWindow
        tip.interface_type = interface_type
        tip.customSignalToDestroy = customSignalToDestroy

        logger.debug(f"customSignalToDestroy: {customSignalToDestroy}")

        tip.connectSignalsToSlots()
        # Explicitly show the teaching tip
        tip.show()
        return tip

    def fadeOut(self):
        self._fadeOut()

    def temporaryHide(self):
        """Hide the teaching tip with fade animation without closing it"""
        logger.debug(f"Temporary hide {self.__class__.__name__}")
        # only animate if visible
        if self.isVisible():
            self.hideAni = QPropertyAnimation(self, b"windowOpacity", self)
            duration = 84
            self.hideAni.setDuration(duration)
            self.hideAni.setStartValue(1)
            self.hideAni.setEndValue(0)
            # when animation finishes, hide the widget but don't close it
            self.hideAni.finished.connect(self.hide)
            self.hideAni.start()

    def temporaryShow(self):
        """Show the teaching tip with fade animation"""
        # only proceed if it's hidden
        if not self.isVisible():
            # make sure we start with opacity 0
            self.setWindowOpacity(0)
            self.show()
            # create a new opacity animation
            self.showAni = QPropertyAnimation(self, b"windowOpacity", self)
            duration = 84
            self.showAni.setDuration(duration)
            self.showAni.setStartValue(0)
            self.showAni.setEndValue(1)
            self.showAni.start()
            # make sure we're properly positioned
            self.move(self.manager.position(self))
