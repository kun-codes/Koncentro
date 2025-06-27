import os
import ssl
import subprocess
import sys
import urllib.request
from pathlib import Path

import certifi
from loguru import logger
from PySide6.QtCore import QObject, QThread, Signal
from uniproxy import Uniproxy

from config_values import ConfigValues
from utils.check_flatpak_sandbox import is_flatpak_sandbox
from website_blocker.constants import MITMDUMP_SHUTDOWN_URL
from website_blocker.utils import kill_process

# Windows-specific constant for hiding console windows
CREATE_NO_WINDOW = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0


class FlatpakContainerError(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


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
        self.pending_start_params = None  # Store parameters for pending start operation

    def start_filtering(
        self,
        listening_port: int,
        joined_addresses: str,
        block_type: str,
        mitmdump_bin_path: str,
    ):
        """Function which starts filtering in a separate thread."""
        logger.debug("Inside WebsiteBLockerManager.start_filtering().")

        # Store parameters for later use after stop_filtering completes
        # would be cleared in _start_after_stop to emulate the memory management of method parameters
        # to prevent memory leaks
        self.pending_start_params = {
            "listening_port": listening_port,
            "joined_addresses": joined_addresses,
            "block_type": block_type,
            "mitmdump_bin_path": mitmdump_bin_path,
        }

        # Not connecting in __init__ because sometimes we want to stop mitmdump without starting it afterwards
        self.filteringStopped.connect(self._start_after_stop)

        self.stop_filtering(delete_proxy=False)

        proxy_worker = ProxyWorker(self.proxy.join)
        self.workers.append(proxy_worker)
        proxy_worker.start()

    def _start_mitmdump(self, listening_port, joined_addresses, block_type, mitmdump_bin_path):
        """Helper method to start mitmdump in a worker thread"""
        if os.name == "nt":
            args = [
                mitmdump_bin_path,
                "--set",
                "allow_remote=true",
                "-p",
                str(listening_port),
                "--showhost",
                "-s",
                os.path.join(getattr(sys, "_MEIPASS", Path(__file__).parent), "filter.py"),
                "--set",
                f"addresses_str={joined_addresses}",
                "--set",
                f"block_type={block_type}",
            ]
            # using _MEIPASS to make it compatible with pyinstaller
            # the os.path.join returns the location of filter.py

            logger.debug(f"Starting mitmdump with command: {' '.join(args)}")

            subprocess.Popen(args, creationflags=CREATE_NO_WINDOW)
        else:
            args = [
                mitmdump_bin_path,
                "--set",
                "allow_remote=true",
                "-p",
                str(listening_port),
                "--showhost",
                "-s",
                os.path.join(getattr(sys, "_MEIPASS", Path(__file__).parent), "filter.py"),
                "--set",
                f"addresses_str={joined_addresses}",
                "--set",
                f"block_type={block_type}",
            ]
            # using _MEIPASS to make it compatible with pyinstaller
            # the os.path.join returns the location of filter.py

            logger.debug(f"Starting mitmdump with command: {' '.join(args)}")

            subprocess.Popen(args)
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
            if is_flatpak_sandbox():
                raise FlatpakContainerError(
                    "Cannot shutdown mitmdump in a Flatpak sandbox using URL method. Will use "
                    "SIGINT or SIGKILL instead."
                )

            proxy_url = f"http://127.0.0.1:{ConfigValues.PROXY_PORT}"
            proxy_handler = urllib.request.ProxyHandler({"http": proxy_url, "https": proxy_url})
            context = ssl.create_default_context(cafile=certifi.where())
            https_handler = urllib.request.HTTPSHandler(context=context)
            opener = urllib.request.build_opener(proxy_handler, https_handler)

            try:
                with opener.open(MITMDUMP_SHUTDOWN_URL, timeout=5) as response:
                    logger.debug(f"mitmdump shutdown URL response status: {getattr(response, 'status', 'unknown')}")
            except urllib.error.URLError as e:
                logger.debug(f"urllib URLError: {e}")
                # Most likely mitmproxy/mitmdump isn't running if connection refused
                if hasattr(e, "reason") and isinstance(e.reason, ConnectionRefusedError):
                    logger.debug("Most likely mitmproxy/mitmdump isn't running (connection refused).")
            except FlatpakContainerError as e:
                logger.debug(f"Flatpak sandbox detected: {e}")
                raise
            except Exception:
                logger.exception("Unexpected error while shutting down mitmdump via urllib")
                raise

            return True
        except FlatpakContainerError:
            logger.debug("Flatpak sandbox detected, using SIGINT or SIGKILL instead for mitmdump.")
            self._force_kill_process()
            return False
        except Exception as e:
            logger.error(f"Graceful shutdown of mitmdump failed: {e}")
            # Fall back to force kill if graceful shutdown fails
            logger.info("Falling back to force kill of mitmdump and mitmproxy.")
            self._force_kill_process()
            return False

    def _force_kill_process(self):
        """Run kill_process in a thread to prevent GUI blocking"""
        kill_worker = ProxyWorker(kill_process)
        self.workers.append(kill_worker)
        kill_worker.start()
        return True

    def _on_stop_completed(self, success, message):
        """Handle completion of stop_filtering operation"""
        if not success:
            self.operationError.emit(f"Warning during filtering shutdown: {message}")

        self.filteringStopped.emit()

    def _start_after_stop(self):
        """Start mitmdump after stop_filtering has completed"""
        # disconnect the signal to prevent multiple connections as it would be reconnected in start_filtering
        self.filteringStopped.disconnect(self._start_after_stop)

        if self.pending_start_params:
            worker = FilterWorker(
                self._start_mitmdump,
                self.pending_start_params["listening_port"],
                self.pending_start_params["joined_addresses"],
                self.pending_start_params["block_type"],
                self.pending_start_params["mitmdump_bin_path"],
            )
            worker.operationCompleted.connect(self._on_start_completed)
            self.workers.append(worker)
            worker.start()

            # clear the pending parameters to mimic the memory management of method parameters and prevent memory leaks
            self.pending_start_params = None
        else:
            logger.warning("No pending parameters for starting mitmdump")

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
