from typing import Optional

from loguru import logger
from PySide6.QtCore import QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QWidget
from qfluentwidgets import BodyLabel, MessageBoxBase, SubtitleLabel

from constants import NEW_RELEASE_URL


class UpdateDialog(MessageBoxBase):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.titleLabel = SubtitleLabel("A new update is available", parent=self)
        self.bodyLabel = BodyLabel(
            "A new update is available. do you want to download it?",
            parent=self,
        )

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.bodyLabel)

        self.yesButton.setText("Yes, download it")
        self.cancelButton.setText("No, maybe later")

        url = QUrl(NEW_RELEASE_URL)

        self.accepted.connect(lambda: QDesktopServices.openUrl(url))
        self.rejected.connect(lambda: logger.debug("User wants to download the update later"))
