import socket

from loguru import logger
from PySide6.QtCore import QThread, Signal


class CheckInternetWorker(QThread):
    internetCheckCompleted = Signal(bool)

    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        try:
            logger.debug("Checking internet connection...")

            socket.setdefaulttimeout(2)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("194.242.2.2", 53))  # using mullvad dns service
            # to maintain privacy
            # https://mullvad.net/en/help/dns-over-https-and-dns-over-tls#specifications
            self.internetCheckCompleted.emit(True)
        except OSError:
            self.internetCheckCompleted.emit(False)
