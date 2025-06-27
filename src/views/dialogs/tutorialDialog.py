from loguru import logger
from PySide6.QtCore import QSize, QUrl
from PySide6.QtWidgets import QHBoxLayout, QSizePolicy, QStackedWidget, QVBoxLayout, QWidget
from qfluentwidgets import (
    BodyLabel,
    FluentIcon,
    InfoBarIcon,
    MessageBoxBase,
    PillToolButton,
    SubtitleLabel,
    TeachingTip,
    TeachingTipTailPosition,
)
from qfluentwidgets.multimedia import VideoWidget

from prefabs.autoLoopVideoWidget import AutoLoopVideoWidget


class TutorialDialog(MessageBoxBase):
    def __init__(self, parent, title: str):
        super().__init__(parent=parent)

        self.title = SubtitleLabel(title, parent=self)
        self.title.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.stackedWidget = QStackedWidget(parent=self)
        self.stackedWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        navigationButtonSizePolicy = QSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        navigationButtonSizePolicy.setHorizontalStretch(0)
        navigationButtonSizePolicy.setVerticalStretch(0)

        self.imageLayout = QHBoxLayout()
        self.imageLayout.setContentsMargins(0, 0, 0, 0)
        self.imageLayout.setSpacing(0)

        self.leftButton = PillToolButton(parent=self)
        self.leftButton.setSizePolicy(navigationButtonSizePolicy)
        self.leftButton.setMinimumSize(QSize(40, 40))
        self.leftButton.setMaximumSize(QSize(40, 40))
        self.leftButton.setIconSize(QSize(16, 16))
        self.leftButton.setCheckable(False)
        self.leftButton.setIcon(FluentIcon.LEFT_ARROW)
        self.leftButton.clicked.connect(self.showPreviousVideo)

        self.rightButton = PillToolButton(parent=self)
        self.rightButton.setSizePolicy(navigationButtonSizePolicy)
        self.rightButton.setMinimumSize(QSize(40, 40))
        self.rightButton.setMaximumSize(QSize(40, 40))
        self.rightButton.setIconSize(QSize(16, 16))
        self.rightButton.setCheckable(False)
        self.rightButton.setIcon(FluentIcon.RIGHT_ARROW)
        self.rightButton.clicked.connect(self.showNextVideo)

        self.imageLayout.addWidget(self.leftButton, 0)
        self.imageLayout.addWidget(self.stackedWidget, 1)
        self.imageLayout.addWidget(self.rightButton, 0)

        # Create a container widget with the layout
        self.imageContainer = QWidget(self)
        self.imageContainer.setLayout(self.imageLayout)
        self.imageContainer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self.viewLayout.addWidget(self.title)
        self.viewLayout.addWidget(self.imageContainer, 1)

        self.yesButton.hide()

        self.cancelButton.setText("Close")

        self.__connectSignalsToSlots()
        self.updateNavigationButtons()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.updateSizes()

    def updateSizes(self):
        parent_width = self.parent().width()
        parent_height = self.parent().height()

        # Calculate size while respecting minimum dimensions
        widget_size = max(int(0.75 * min(parent_width, parent_height)), 500)
        self.widget.setFixedSize(widget_size, widget_size)

    def __connectSignalsToSlots(self):
        # disconnecting yesButton and cancelButton from the default slots, as they were connected in the parent class
        self.yesButton.clicked.disconnect()
        self.cancelButton.clicked.disconnect()

        self.cancelButton.clicked.connect(self.oncancelButtonClicked)
        self.stackedWidget.currentChanged.connect(self.onStackedWidgetCurrentChanged)

    def oncancelButtonClicked(self):
        if self.stackedWidget.currentIndex() == self.stackedWidget.count() - 1:
            # Stop all videos before closing
            for i in range(self.stackedWidget.count()):
                container = self.stackedWidget.widget(i)
                video_widget = container.findChild(VideoWidget)
                if video_widget:
                    video_widget.hide()
                    # video_widget.stop()
                    video_widget.player.setSource(QUrl())  # Clear source

            self.accept()
        else:
            TeachingTip.create(
                self.cancelButton,
                title="Complete the tutorial first",
                content="Please complete the tutorial before closing the dialog.",
                icon=InfoBarIcon.INFORMATION,
                isClosable=True,
                tailPosition=TeachingTipTailPosition.TOP,
                parent=self,
                isDeleteOnClose=True,
            )

    def addVideo(self, videoPath: QUrl, captionText: str):
        containerWidget = QWidget(parent=self)
        containerWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        containerWidgetLayout = QVBoxLayout(containerWidget)

        videoWidget = AutoLoopVideoWidget(parent=self)
        videoWidget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        videoWidget.setVideo(videoPath)
        videoWidget.hide()  # videoWidget doesn't appear if it's not hidden at start and shown when it's time to show
        # comes

        captionLabel = BodyLabel(captionText, self)
        captionLabel.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        containerWidgetLayout.addWidget(videoWidget, 1)
        containerWidgetLayout.addWidget(captionLabel, 0)

        self.stackedWidget.addWidget(containerWidget)

    def showPreviousVideo(self):
        currentIndex = self.stackedWidget.currentIndex()

        self.hideVideoWidget(currentIndex)  # hide the current video widget because it would be switched

        if currentIndex > 0:
            self.stackedWidget.setCurrentIndex(currentIndex - 1)
            self.updateNavigationButtons()

    def showNextVideo(self):
        currentIndex = self.stackedWidget.currentIndex()

        self.hideVideoWidget(currentIndex)  # hide the current video widget because it would be switched

        if currentIndex < self.stackedWidget.count() - 1:
            self.stackedWidget.setCurrentIndex(currentIndex + 1)
            self.updateNavigationButtons()

    def hideVideoWidget(self, index):
        currentVideoWidget = self.stackedWidget.widget(index).findChild(VideoWidget)
        if currentVideoWidget:
            currentVideoWidget.hide()

    def show(self):
        super().show()
        self.stackedWidget.setCurrentIndex(0)
        self.updateNavigationButtons()

    def updateNavigationButtons(self):
        currentIndex = self.stackedWidget.currentIndex()
        self.leftButton.setEnabled(currentIndex > 0)
        self.rightButton.setEnabled(currentIndex < self.stackedWidget.count() - 1)

    def onStackedWidgetCurrentChanged(self, index: int):
        logger.debug(f"Inside onStackedWidgetCurrentChanged: {index}")
        self.stackedWidget.widget(index).findChild(VideoWidget).show()
