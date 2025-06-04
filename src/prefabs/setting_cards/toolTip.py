from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from qfluentwidgets import ToolTip, ToolTipFilter, ToolTipPosition


class WaylandToolTipFilter(ToolTipFilter):
    def __init__(self, parent: QWidget, showDelay=300, position=ToolTipPosition.TOP):
        """
        Parameters
        ----------
        parent: QWidget
            the widget to install tool tip

        showDelay: int
            show tool tip after how long the mouse hovers in milliseconds

        position: TooltipPosition
            where to show the tooltip
        """
        super().__init__(parent, showDelay, position)

    def _createToolTip(self):
        return WaylandToolTip(self.parent().toolTip(), self.parent().window())

class WaylandToolTip(ToolTip):
    def __init__(self, text='', parent=None):
        """
        Parameters
        ----------
        text: str
            the text of tool tip

        parent: QWidget
            parent widget
        """
        super().__init__(text, parent)
        self.setWindowFlags(Qt.ToolTip)
