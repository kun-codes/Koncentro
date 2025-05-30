import os
import shlex
import shutil
import subprocess

from loguru import logger
from PySide6.QtCore import QObject, QThread, Signal
from uniproxy import Uniproxy

from config_values import ConfigValues
from utils.noHTTPClientError import NoHTTPClientError
from website_blocker.constants import MITMDUMP_COMMAND_LINUX, MITMDUMP_COMMAND_WINDOWS, MITMDUMP_SHUTDOWN_URL
from website_blocker.utils import kill_process

# Windows-specific constant for hiding console windows
CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0

class FilterWorker(QThread):
    """Worker thread for filtering operations"""
    operationCompleted = Signal(bool, str)  # Success flag, message

    def __init__(self, operation, *args, **kwargs):
        super().__init__()
        self.operation = operation
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            _result = self.operation(*self.args, **self.kwargs)
            self.operationCompleted.emit(True, "Operation completed successfully")
        except Exception as e:
            logger.error(f"Error in FilterWorker: {e}")
            self.operationCompleted.emit(False, str(e))


class ProxyWorker(QThread):
    """Worker thread for proxy operations"""

    def __init__(self, operation, *args, **kwargs):
        super().__init__()
        self.operation = operation
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            self.operation(*self.args, **self.kwargs)
        except Exception as e:
            logger.error(f"Error in ProxyWorker: {e}")


class WebsiteBlockerManager(QObject):
    filteringStarted = Signal()
    filteringStopped = Signal()
    operationError = Signal(str)

    def __init__(self):
        super().__init__()
        self.proxy = Uniproxy("127.0.0.1", ConfigValues.PROXY_PORT)
        self.workers = []  # Keep references to prevent garbage collection

    def start_filtering(
        self,
        listening_port: int,
        joined_addresses: str,
        block_type: str,
        mitmdump_bin_path: str,
    ):
        """Function which starts filtering in a separate thread."""
        logger.debug("Inside WebsiteBLockerManager.start_filtering().")

        self.stop_filtering(delete_proxy=False)

        # Replace threading.Thread with ProxyWorker
        proxy_worker = ProxyWorker(self.proxy.join)
        self.workers.append(proxy_worker)
        proxy_worker.start()

        worker = FilterWorker(self._start_mitmdump, listening_port, joined_addresses, block_type, mitmdump_bin_path)
        worker.operationCompleted.connect(self._on_start_completed)
        self.workers.append(worker)
        worker.start()

    def _start_mitmdump(self, listening_port, joined_addresses, block_type, mitmdump_bin_path):
        """Helper method to start mitmdump in a worker thread"""
        # Prepare command arguments
        if os.name == "nt":
            args = shlex.split(
                MITMDUMP_COMMAND_WINDOWS.format(mitmdump_bin_path, listening_port, joined_addresses, block_type),
                posix=False,
            )
        else:
            args = shlex.split(
                MITMDUMP_COMMAND_LINUX.format(mitmdump_bin_path, listening_port, joined_addresses, block_type)
            )

        # Start the process
        subprocess.Popen(args, creationflags=CREATE_NO_WINDOW)
        return True

    def _on_start_completed(self, success, message):
        """Handle completion of start_filtering operation"""
        if success:
            self.filteringStarted.emit()
        else:
            self.operationError.emit(f"Failed to start filtering: {message}")

    def stop_filtering(self, delete_proxy: bool = True):
        """Stop filtering in a separate thread."""
        logger.debug("Inside WebsiteBlockerManager.stop_filtering().")

        if delete_proxy:
            # Replace threading.Thread with ProxyWorker
            proxy_worker = ProxyWorker(self.proxy.delete_proxy)
            self.workers.append(proxy_worker)
            proxy_worker.start()

        worker = FilterWorker(self._shutdown_mitmdump)
        worker.operationCompleted.connect(self._on_stop_completed)
        self.workers.append(worker)
        worker.start()

    def _shutdown_mitmdump(self):
        """Helper method to shutdown mitmdump in a worker thread"""
        try:
            # detect if curl is installed
            curl_path = shutil.which("curl")
            # detect if wget is installed
            wget_path = shutil.which("wget")

            null_device = "NUL" if os.name == "nt" else "/dev/null"

            if curl_path:
                result = subprocess.run(
                    [curl_path, "-s", "--proxy", f"127.0.0.1:{ConfigValues.PROXY_PORT}", MITMDUMP_SHUTDOWN_URL],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,  # Prevent hanging indefinitely
                    creationflags=CREATE_NO_WINDOW
                )
                logger.debug(f"curl command return code: {result.returncode}")
                if result.returncode == 7:
                    logger.debug("curl return code 7: Most likely mitmproxy/mitmdump isn't running")
            elif wget_path:
                # https://askubuntu.com/a/586550
                result = subprocess.run([
                    wget_path,
                    "-q",  # quiet mode
                    "-O", null_device,  # discard output file
                    "-e", "use_proxy=yes",
                    "-e", f"http_proxy=http://127.0.0.1:{ConfigValues.PROXY_PORT}",
                    MITMDUMP_SHUTDOWN_URL
                ],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    timeout=5,
                    creationflags=CREATE_NO_WINDOW)  # Prevent hanging indefinitely
                logger.debug(f"wget command return code: {result.returncode}")
                if result.returncode == 4:
                    logger.debug("wget return code 4: Most likely mitmproxy/mitmdump isn't running")
            else:
                raise NoHTTPClientError("Neither curl nor wget found.")
            return True
        except Exception as e:
            logger.error(f"Graceful shutdown of mitmdump failed: {e}")
            # Fall back to force kill if graceful shutdown fails
            logger.info("Falling back to force kill of mitmdump and mitmproxy.")
            self._force_kill_process()
            return False

    def _force_kill_process(self):
        """Run kill_process in a thread to prevent GUI blocking"""
        # Replace threading.Thread with ProxyWorker
        kill_worker = ProxyWorker(kill_process)
        self.workers.append(kill_worker)
        kill_worker.start()
        return True

    def _on_stop_completed(self, success, message):
        """Handle completion of stop_filtering operation"""
        self.filteringStopped.emit()
        if not success:
            self.operationError.emit(f"Warning during filtering shutdown: {message}")

    def cleanup(self):
        """Clean up resources and terminate threads"""
        # Stop any running workers
        for worker in self.workers:
            if worker.isRunning():
                worker.requestInterruption()
                worker.wait(1000)  # Wait up to 1 second for thread to finish
                if worker.isRunning():
                    worker.terminate()

        # Clear the list
        self.workers.clear()

