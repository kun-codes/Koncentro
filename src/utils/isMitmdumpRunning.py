import ssl
import urllib.request

import certifi
from loguru import logger
from PySide6.QtCore import QThread, Signal

from config_values import ConfigValues
from website_blocker.constants import MITMDUMP_CHECK_URL


class isMitmdumpRunningWorker(QThread):
    """Worker thread for checking if mitmdump is running"""

    checkCompleted = Signal(bool)

    def __init__(self) -> None:
        super().__init__()

    def run(self) -> None:
        try:
            is_running = self.isMitmdumpRunning()
            self.checkCompleted.emit(is_running)
        except Exception as e:
            logger.error(f"Error checking if mitmdump is running: {e}")
            self.checkCompleted.emit(False)

    def isMitmdumpRunning(self) -> bool:
        proxy_url = f"http://127.0.0.1:{ConfigValues.PROXY_PORT}"
        proxy_handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
        context = ssl.create_default_context(cafile=certifi.where())
        https_handler = urllib.request.HTTPSHandler(context=context)
        opener = urllib.request.build_opener(proxy_handler, https_handler)

        try:
            with opener.open(MITMDUMP_CHECK_URL, timeout=5) as response:
                if response.status == 200:
                    logger.debug("Mitmdump is running.")
                    return True
                else:
                    logger.debug(f"mitmdump check URL response status: {response.status}")
                    return False
        except urllib.error.URLError as e:
            logger.debug(f"urllib URLError: {e}")
            # Most likely mitmproxy/mitmdump isn't running if connection refused
            if hasattr(e, "reason") and isinstance(e.reason, ConnectionRefusedError):
                logger.debug("Most likely mitmproxy/mitmdump isn't running (connection refused).")
            return False
