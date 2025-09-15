from loguru import logger
from PySide6.QtCore import QEvent, QPropertyAnimation, Qt, Signal
from qfluentwidgets import FluentWindow, TeachingTip, TeachingTipTailPosition, TeachingTipView

from constants import InterfaceType


class TargetClickTeachingTip(TeachingTip):
    """Teaching tip that only closes when the target widget is clicked."""

    def __init__(
        self, view, target, tailPosition=TeachingTipTailPosition.BOTTOM, parent=None, isDeleteOnClose: bool = True
    ) -> None:
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
        self.customSignalToDestroy: Signal = None
        self.expectedSignalParams: tuple = None

    def connectSignalsToSlots(self) -> None:
        logger.debug(f"Inside connectSignalsToSlots of {self.__class__.__name__}")
        self.mainWindow.stackedWidget.currentChanged.connect(self.onTabChanged)
        if self.customSignalToDestroy is not None:
            if self.expectedSignalParams is not None:
                # connect to custom handler that checks parameters
                self.customSignalToDestroy.connect(self._handleCustomSignal)
            else:
                self.customSignalToDestroy.connect(self._fadeOut)

    def _handleCustomSignal(self, *args):
        """Handle custom signal and compare parameters before calling _fadeOut"""
        logger.debug(f"Custom signal received with args: {args}")
        logger.debug(f"Expected params: {self.expectedSignalParams}")

        if self.expectedSignalParams is not None:
            if len(args) == len(self.expectedSignalParams):
                if args == self.expectedSignalParams:
                    logger.debug("Signal parameters match expected values, calling _fadeOut")
                    self._fadeOut()
                else:
                    logger.debug("Signal parameters do not match expected values, ignoring signal")
            else:
                logger.debug("Signal parameter count mismatch, ignoring signal")
        else:
            logger.debug("No expected parameters, calling _fadeOut")
            self._fadeOut()

    def onTabChanged(self, index) -> None:
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
        *expectedSignalParams,
    ) -> "TargetClickTeachingTip":
        """Create a teaching tip that only closes when the target is clicked.

        Args:
            expectedSignalParams: Variable number of parameters to compare against
                                customSignalToDestroy signal values. If provided,
                                _fadeOut() is only called when signal values match these parameters.
        """
        view = TeachingTipView(title, content, icon, image, False, tailPosition)
        tip = cls(view, target, tailPosition, parent, True)

        tip.mainWindow = mainWindow
        tip.interface_type = interface_type
        tip.customSignalToDestroy = customSignalToDestroy
        tip.expectedSignalParams = expectedSignalParams if expectedSignalParams else None

        logger.debug(f"customSignalToDestroy: {customSignalToDestroy}")
        logger.debug(f"expectedSignalParams: {expectedSignalParams}")
        logger.debug(f"type of expectedSignalParams: {type(expectedSignalParams)}")

        tip.connectSignalsToSlots()
        # Explicitly show the teaching tip
        tip.show()
        return tip

    def fadeOut(self) -> None:
        self._fadeOut()

    def temporaryHide(self) -> None:
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

    def temporaryShow(self) -> None:
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
