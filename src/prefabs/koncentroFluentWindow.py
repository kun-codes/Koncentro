from typing import Optional

from PySide6.QtWidgets import QVBoxLayout, QWidget
from qfluentwidgets import FluentWindow, setCustomStyleSheet
from qfluentwidgets.window.fluent_window import FluentWindowBase

from prefabs.bottomBar import BottomBar


class VBoxLayoutInitializer(QWidget):
    """
    A hack to declare self.vBoxLayout in KoncentroFluentWindowBase before FluentWindowBase's parent classes's __init__
    is called
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.vBoxLayout = QVBoxLayout(self)  # this line causes the error "QLayout: Attempting to add QLayout "" to
        # MainWindow "", which already has a layout", it can be fixed if I change the line in FluentWindowBase from
        # self.hBoxLayout = QHBoxLayout(self) to self.hBoxLayout = QHBoxLayout()
        # but I don't know how to do it
        self.vBoxLayout.setSpacing(0)
        self.vBoxLayout.setContentsMargins(0, 0, 0, 0)


class KoncentroFluentWindowBase(FluentWindowBase, VBoxLayoutInitializer):
    """Fluent window base class"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)


class KoncentroFluentWindow(KoncentroFluentWindowBase, FluentWindow):
    """Fluent window"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.bottomBar = BottomBar(self)

        self.vBoxLayout.addLayout(self.hBoxLayout)
        self.vBoxLayout.addWidget(self.bottomBar)

        self.stackedWidget.setObjectName("stackedWidget")

        self.rightBorder = QWidget(self)
        self.rightBorder.setObjectName("rightBorder")
        self.rightBorder.setFixedWidth(10)
        self.hBoxLayout.addWidget(self.rightBorder)

        qssLight = """
        StackedWidget {
            border-bottom-left-radius: 10px;
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
            border-right: 1px solid rgba(0, 0, 0, 0.068);
            border-bottom: 1px solid rgba(0, 0, 0, 0.068);
        }
        """
        qssDark = """
        StackedWidget {
            border-bottom-left-radius: 10px;
            border-top-right-radius: 10px;
            border-bottom-right-radius: 10px;
            border-right: 1px solid rgba(0, 0, 0, 0.18);
            border-bottom: 1px solid rgba(0, 0, 0, 0.18);
        }
        """

        # from: https://github.com/zhiyiYo/PyQt-Fluent-Widgets/issues/707
        self.style().unpolish(self)
        self.style().polish(self)

        # setCustomStyleSheet(self.stackedWidget, borderQss, borderQss)
        setCustomStyleSheet(self.stackedWidget, qssLight, qssDark)

        # set focus to the current interface so the shortcuts defined inside it which aren't global become active
        # instantly without having to click on the interface first after switching to it to make it have the focus
        self.stackedWidget.currentChanged.connect(self.setFocusToInterface)

    def setFocusToInterface(self, index: int) -> None:
        self.stackedWidget.widget(index).setFocus()
