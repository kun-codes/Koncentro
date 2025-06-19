from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, ToolTipFilter, ToolTipPosition

from ui_py.ui_bottom_bar_widget import Ui_BottomBarWidget


class BottomBar(Ui_BottomBarWidget, QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=None)
        self.setupUi(self)

        self.initWidget()

    def initWidget(self):
        self.stopButton.setIcon(FluentIcon.CLOSE)
        self.pauseResumeButton.setIcon(FluentIcon.PLAY)
        self.skipButton.setIcon(FluentIcon.CHEVRON_RIGHT)

        self.stopButton.setCheckable(False)
        self.pauseResumeButton.setCheckable(True)
        self.pauseResumeButton.setChecked(False)  # Changed from True to False to match PLAY icon
        self.skipButton.setCheckable(False)

        self.stopButton.setToolTip("Stop")
        self.stopButton.installEventFilter(ToolTipFilter(self.stopButton, showDelay=300, position=ToolTipPosition.TOP))
        self.pauseResumeButton.setToolTip("Pause/Resume")
        self.pauseResumeButton.installEventFilter(
            ToolTipFilter(self.pauseResumeButton, showDelay=300, position=ToolTipPosition.TOP)
        )
        self.skipButton.setToolTip("Skip")
        self.skipButton.installEventFilter(ToolTipFilter(self.skipButton, showDelay=300, position=ToolTipPosition.TOP))
