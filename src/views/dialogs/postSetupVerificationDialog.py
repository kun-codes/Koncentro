from encodings.punycode import selective_find

from PySide6.QtCore import Qt
from qfluentwidgets import (
    BodyLabel,
    MessageBoxBase,
    SubtitleLabel,
)

from constants import APPLICATION_NAME


class PostSetupVerificationDialog(MessageBoxBase):
    def __init__(self, parent=None, is_setup_first_time: bool = True):
        super().__init__(parent=parent)
        self.titleLabel = SubtitleLabel("Are you sure you have set up website filtering correctly?", parent=self)
        self.bodyLabel = BodyLabel(
            'You can check if the website filter is working correctly by visiting <a href="https://example.com">https://example.com</a>.',
            parent=self,
        )
        self.bodyLabel2 = BodyLabel(
            f"It should be blocked by {APPLICATION_NAME} if the website filter is working correctly.",
            parent=self
        )
        self.bodyLabel3 = BodyLabel(
            "Other websites like <a href='https://duckduckgo.com'>https://duckduckgo.com</a> should not be blocked.",
            parent=self
        )

        if is_setup_first_time:
            bodyLabel4Text = ("If you still face issues with website filtering, or if you want "
                              "to set up any other \n")
            bodyLabel4Text += ("Firefox-based browser, you can manually run the setup again "
                               "the anytime from the \nSettings page.")
        else:
            bodyLabel4Text = ("If you want to set up any other Firefox-based browser, you can "
                              "manually run the setup \n")
            bodyLabel4Text += "again anytime from the Settings page."

        self.bodyLabel4 = BodyLabel(
            bodyLabel4Text,
            parent=self
        )


        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.bodyLabel)
        self.viewLayout.addWidget(self.bodyLabel2)
        self.viewLayout.addWidget(self.bodyLabel3)
        self.viewLayout.addWidget(self.bodyLabel4)

        self.yesButton.setText("Yes")
        self.cancelButton.setText("No, Take me back")

        self.initWidget()

    def initWidget(self):
        for widget in [self.bodyLabel, self.bodyLabel3]:
            widget.setTextInteractionFlags(Qt.TextBrowserInteraction)
            widget.setOpenExternalLinks(True)
