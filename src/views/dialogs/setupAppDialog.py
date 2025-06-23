from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QSizePolicy
from qfluentwidgets import (
    BodyLabel,
    FluentIcon,
    MessageBoxBase,
    PushButton,
    SubtitleLabel,
)

from config_values import ConfigValues
from constants import APPLICATION_NAME
from utils.find_mitmdump_executable import get_mitmdump_path
from views.dialogs.postSetupVerificationDialog import PostSetupVerificationDialog
from website_blocker.website_blocker_manager import WebsiteBlockerManager


class SetupAppDialog(MessageBoxBase):
    def __init__(self, parent=None, is_setup_first_time: bool = True):
        super().__init__(parent=parent)

        self.is_setup_first_time = is_setup_first_time

        titleText = f"Setup {APPLICATION_NAME}"
        titleText += " for the first time" if self.is_setup_first_time else ""
        self.titleLabel = SubtitleLabel(titleText, parent=self)

        bodyText = "Click the below button to visit the webpage to set up system-wide website filtering. "

        self.bodyLabel = BodyLabel(
            bodyText,
            parent=self,
        )

        self.bodyLabel2 = BodyLabel(
            "You would need to install mitmproxy's certificate to your system to enable website filtering",
            parent=self,
        )

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.bodyLabel)
        self.viewLayout.addWidget(self.bodyLabel2)

        self.yesButton.setText("Open Setup")
        self.yesButton.setIcon(FluentIcon.LINK)
        self.cancelButton.setText("Setup Completed")

        self.backButton = PushButton("Cancel Setup", self.buttonGroup)

        # to make all buttons have the same size
        self.buttonLayout.insertWidget(0, self.backButton, 1, Qt.AlignmentFlag.AlignVCenter)
        for button in [self.yesButton, self.cancelButton, self.backButton]:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setMinimumWidth(150)

        self.initWidget()
        self.initTemporaryWebsiteBlockerManager()

    def initWidget(self):
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.bodyLabel.setWordWrap(True)
        self.bodyLabel.setAlignment(Qt.AlignmentFlag.AlignJustify)

        self.bodyLabel2.setWordWrap(True)
        self.bodyLabel2.setAlignment(Qt.AlignmentFlag.AlignJustify)

        # self.widget.setFixedSize(300, 500)

        self.__connectSignalsToSlots()

    def __connectSignalsToSlots(self):
        # disconnecting from the default slots as done in the parent class, so that self.accept() and self.reject()
        # are not called
        self.yesButton.clicked.disconnect()
        self.cancelButton.clicked.disconnect()
        self.yesButton.clicked.connect(self.onWebsiteFilterSetupButtonClicked)
        self.cancelButton.clicked.connect(self.onCloseButtonClicked)
        self.backButton.clicked.connect(self.onBackButtonClicked)

    def onWebsiteFilterSetupButtonClicked(self):
        url = QUrl("http://mitm.it/")
        QDesktopServices.openUrl(url)

    def onCloseButtonClicked(self):
        confirmation_dialog = PostSetupVerificationDialog(self, self.is_setup_first_time)

        if confirmation_dialog.exec():
            self.temporary_website_blocker_manager.stop_filtering(delete_proxy=True)  # stopping website filtering here
            # because this function will only be triggered after confirmation_dialog is accepted
            self.accept()

    def onBackButtonClicked(self):
        self.temporary_website_blocker_manager.stop_filtering(delete_proxy=True)
        self.reject()

    def initTemporaryWebsiteBlockerManager(self):
        self.temporary_website_blocker_manager = WebsiteBlockerManager()
        self.temporary_website_blocker_manager.start_filtering(
            listening_port=ConfigValues.PROXY_PORT,
            joined_addresses="example.com",
            block_type="blocklist",
            mitmdump_bin_path=get_mitmdump_path(),
        )
