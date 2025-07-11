from PySide6.QtMultimedia import QMediaPlayer
from qfluentwidgets.multimedia import VideoWidget


class AutoLoopVideoWidget(VideoWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)

        self.playBar.hide()

        self.player.setLoops(QMediaPlayer.Loops.Infinite)  # type: StandardMediaPlayBar

    def enterEvent(self, e) -> None:
        pass

    def leaveEvent(self, e) -> None:
        pass

    def hideEvent(self, e) -> None:
        self.stop()
        e.accept()

    def showEvent(self, e) -> None:
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
