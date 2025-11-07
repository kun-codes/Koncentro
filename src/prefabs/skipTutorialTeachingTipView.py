from typing import Optional, Union

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import QWidget
from qfluentwidgets import (
    FluentIconBase,
    PrimaryPushButton,
    TeachingTipTailPosition,
    TeachingTipView,
)


class SkipTutorialTeachingTipView(TeachingTipView):
    def __init__(
        self,
        title: str,
        content: str,
        icon: Union[FluentIconBase, QIcon, str] = None,
        image: Union[str, QPixmap, QImage] = None,
        isClosable: bool = True,
        tailPosition: TeachingTipTailPosition = TeachingTipTailPosition.BOTTOM,
        parent: Optional[QWidget] = None,
    ) -> None:
        super().__init__(title, content, icon, image, isClosable, tailPosition, parent)

        self.skipButton = PrimaryPushButton("Skip Tutorial")

        self.widgetLayout.addSpacing(12)
        self.widgetLayout.addWidget(self.skipButton, stretch=0, alignment=Qt.AlignmentFlag.AlignRight)
