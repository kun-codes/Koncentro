import subprocess
import sys
import threading
import urllib.request
from typing import Optional

from loguru import logger
from PySide6.QtCore import QObject
from uniproxy import Uniproxy

from configValues import ConfigValues
from utils.isNuitka import is_nuitka
from website_blocker.constants import MITMDUMP_SHUTDOWN_URL


class WebsiteBlockerManager(QObject):
    """
    Manages mitmproxy as a separate subprocess for website blocking.

    Ordering guarantees (to avoid temporary internet loss):
      - Start: mitmproxy binds its port -> *then* system proxy is joined
      - Stop:  system proxy is deleted -> *then* mitmproxy subprocess is shut down
    """

    def __init__(self) -> None:
        super().__init__()
        self.proxy: Uniproxy = Uniproxy("127.0.0.1", ConfigValues.PROXY_PORT)

        self._process: Optional[subprocess.Popen] = None
        self._proxy_thread: Optional[threading.Thread] = None
        self._stop_thread: Optional[threading.Thread] = None
        self._process_lock = threading.Lock()

    def start_blocking(
        self,
        listening_port: int,
        joined_addresses: str,
        block_type: str,
    ) -> None:
        """
        Starts the mitmproxy subprocess + join system proxy in a background thread (non-blocking).

        Order within the thread:
          shut down old subprocess -> start new subprocess -> join new system proxy
        """
        logger.debug("Inside WebsiteBlockerManager.start_blocking().")

        def run() -> None:
            self._stop_current_process(delete_proxy=True)

            cmd = self._build_subprocess_cmd(listening_port, joined_addresses, block_type)
            logger.debug(f"Starting mitmproxy subprocess: {' '.join(cmd)}")

            try:
                process = subprocess.Popen(cmd)

                # make the new process visible so stop_blocking can find it
                with self._process_lock:
                    self._process = process

                # give mitmproxy a moment to bind its port, then point the system proxy at it
                logger.debug("Joining system proxy.")
                self.proxy.join()
            except Exception as e:
                logger.error(f"Failed to start mitmproxy subprocess: {e}")

        self._proxy_thread = threading.Thread(target=run, daemon=True)
        self._proxy_thread.start()
        logger.debug("Proxy subprocess starting in background thread.")

    def stop_blocking(self, delete_proxy: bool = True) -> None:
        """
        Stops the mitmproxy subprocess and optionally deletes the system proxy (non-blocking).

        When *delete_proxy* is ``True`` the work is done in a background
        thread with the correct order: delete system proxy -> shutdown subprocess.
        """
        logger.debug("Inside WebsiteBlockerManager.stop_blocking().")

        if delete_proxy:

            def stop_sequence() -> None:
                with self._process_lock:
                    process = self._process
                    self._process = None

                if process is None:
                    return

                logger.debug("Deleting system proxy.")
                self.proxy.delete_proxy()
                logger.debug("Shutting down mitmproxy subprocess.")
                self._shutdown_process(process)

            self._stop_thread = threading.Thread(target=stop_sequence, daemon=True)
            self._stop_thread.start()
        else:
            with self._process_lock:
                process = self._process
                self._process = None
            if process is not None:
                self._shutdown_process(process)

    def cleanup(self) -> None:
        """
        Clean up resources.

        This method is blocking and is intended for use from a background thread.
        """
        logger.debug("Inside WebsiteBlockerManager.cleanup().")

        self._stop_current_process(delete_proxy=True)

        for attr in ("_stop_thread", "_proxy_thread"):
            t: Optional[threading.Thread] = getattr(self, attr, None)
            if t is not None and t.is_alive():
                t.join(timeout=5)
                setattr(self, attr, None)

        self.proxy.delete_proxy()
        logger.debug("Cleanup complete.")

    def _stop_current_process(self, delete_proxy: bool) -> None:
        """
        Stop whichever subprocess is currently running (runs in caller's thread).
        """
        with self._process_lock:
            process = self._process
            self._process = None

        if process is None:
            return

        if delete_proxy:
            logger.debug("Deleting system proxy (old instance).")
            self.proxy.delete_proxy()

        logger.debug("Shutting down previous mitmproxy subprocess.")
        self._shutdown_process(process)

    def _build_subprocess_cmd(
        self,
        port: int,
        addresses: str,
        block_type: str,
    ) -> list[str]:
        """Build the command list to launch the blocking subprocess."""
        args = [
            "--port",
            str(port),
            "--addresses",
            addresses,
            "--block-type",
            block_type,
        ]
        if is_nuitka():
            return [sys.executable, "--blocking-subprocess"] + args
        return [sys.executable, "-m", "website_blocker.blocking_process"] + args

    @staticmethod
    def _shutdown_process(process: subprocess.Popen) -> None:
        """
        Shut down the given subprocess.

        Attempts a graceful HTTP shutdown through mitmproxy first, then
        falls back to ``terminate()`` and finally ``kill()``.
        """
        # 1. Graceful: send HTTP shutdown request through mitmproxy itself
        WebsiteBlockerManager._send_http_shutdown()

        # 2. Wait for process to exit on its own
        try:
            process.wait(timeout=5)
            return
        except subprocess.TimeoutExpired:
            pass

        # 3. Force terminate (SIGTERM on Unix, TerminateProcess on Windows)
        logger.debug("Sending SIGTERM to mitmproxy subprocess.")
        process.terminate()
        try:
            process.wait(timeout=3)
            return
        except subprocess.TimeoutExpired:
            pass

        # 4. Last resort: kill (SIGKILL on Unix)
        logger.debug("Sending SIGKILL to mitmproxy subprocess.")
        process.kill()
        process.wait()

    @staticmethod
    def _send_http_shutdown() -> None:
        """Send a shutdown request through mitmproxy (best-effort)."""
        proxy_url = f"http://127.0.0.1:{ConfigValues.PROXY_PORT}"
        proxy_handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
        opener = urllib.request.build_opener(proxy_handler)
        try:
            with opener.open(MITMDUMP_SHUTDOWN_URL, timeout=3):
                logger.debug("HTTP shutdown request sent to mitmproxy.")
        except Exception:
            # If mitmproxy is already gone or the connection fails, that's fine
            pass
