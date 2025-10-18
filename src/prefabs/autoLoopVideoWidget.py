from typing import Optional

from PySide6.QtCore import QEvent
from PySide6.QtGui import QEnterEvent, QHideEvent, QShowEvent
from PySide6.QtMultimedia import QMediaPlayer
from PySide6.QtWidgets import QWidget
from qfluentwidgets.multimedia import VideoWidget


class AutoLoopVideoWidget(VideoWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)

        self.playBar.hide()

        self.player.setLoops(QMediaPlayer.Loops.Infinite)

    def enterEvent(self, e: QEnterEvent) -> None:
        pass

    def leaveEvent(self, e: QEvent) -> None:
        pass

    def hideEvent(self, e: QHideEvent) -> None:
        self.stop()
        e.accept()

    def showEvent(self, e: QShowEvent) -> None:
        self.play()
        e.accept()

    # def setVideo(self, url: QUrl):
    #     """ set the video to play """
    #     self.player.setSource(url)
    #     self.fitInView(self.videoItem, Qt.KeepAspectRatio)
    #     self.play()

    # def showEvent(self, event):
    #     super().showEvent(event)
    #     self.play()
