import socket

from loguru import logger
from PySide6.QtCore import QThread, Signal


class CheckInternetWorker(QThread):
    internetCheckCompleted = Signal(bool)

    def __init__(self) -> None:
        super().__init__()

        # privacy-friendly dns providers. Sourced from https://www.privacyguides.org/en/dns/
        self.endpoints = [
            ("194.242.2.2", 53),  # Mullvad, https://mullvad.net/en/help/dns-over-https-and-dns-over-tls#specifications
            ("76.76.2.0", 53),  # Control D, Unfiltered config from https://controld.com/free-dns#quick-setups
            ("9.9.9.9", 53),  # Quad9, https://quad9.net/service/service-addresses-and-features/#rec
        ]

    def _can_connect(self, host: str, port: int) -> bool:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)

        try:
            sock.connect((host, port))
            return True
        except OSError:
            return False
        finally:
            sock.close()

    def run(self) -> None:
        logger.debug("Checking internet connection...")

        for host, port in self.endpoints:
            if self._can_connect(host, port):
                logger.debug(f"Successfully connected to {host}:{port}. Internet is available.")
                self.internetCheckCompleted.emit(True)
                return

        logger.debug("No internet connection available.")
        self.internetCheckCompleted.emit(False)
