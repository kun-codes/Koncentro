import os
import shutil
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
    def __init__(self, message) -> None:
        self.message = message
        super().__init__(self.message)


class WebsiteBlockerWorker(QThread):
    """Worker thread for website blocking operations"""

    operationCompleted = Signal(bool, str)  # Success flag, message

    def __init__(self, operation, *args, **kwargs) -> None:
        super().__init__()
        self.operation = operation
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        try:
            _result = self.operation(*self.args, **self.kwargs)
            self.operationCompleted.emit(True, "Operation completed successfully")
        except Exception as e:
            logger.error(f"Error in WebsiteBlockerWorker: {e}")
            self.operationCompleted.emit(False, str(e))


class ProxyWorker(QThread):
    """Worker thread for proxy operations"""

    def __init__(self, operation, *args, **kwargs) -> None:
        super().__init__()
        self.operation = operation
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        try:
            self.operation(*self.args, **self.kwargs)
        except Exception as e:
            logger.error(f"Error in ProxyWorker: {e}")


class WebsiteBlockerManager(QObject):
    blockingStarted = Signal()
    blockingStopped = Signal()
    operationError = Signal(str)

    def __init__(self) -> None:
        super().__init__()
        self.proxy = Uniproxy("127.0.0.1", ConfigValues.PROXY_PORT)
        self.workers = []  # Keep references to prevent garbage collection
        self.pending_start_params = None  # Store parameters for pending start operation

    def start_blocking(
        self,
        listening_port: int,
        joined_addresses: str,
        block_type: str,
        mitmdump_bin_path: str,
    ) -> None:
        """Function which starts blocking in a separate thread."""
        logger.debug("Inside WebsiteBlockerManager.start_blocking().")

        # Store parameters for later use after stop_blocking completes
        # would be cleared in _start_after_stop to emulate the memory management of method parameters
        # to prevent memory leaks
        self.pending_start_params = {
            "listening_port": listening_port,
            "joined_addresses": joined_addresses,
            "block_type": block_type,
            "mitmdump_bin_path": mitmdump_bin_path,
        }

        # Not connecting in __init__ because sometimes we want to stop mitmdump without starting it afterwards
        self.blockingStopped.connect(self._start_after_stop)

        self.stop_blocking(delete_proxy=False)

        proxy_worker = ProxyWorker(self.proxy.join)
        self.workers.append(proxy_worker)
        proxy_worker.start()

    def _start_mitmdump(self, listening_port, joined_addresses, block_type, mitmdump_bin_path) -> bool:
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
                os.path.join(getattr(sys, "_MEIPASS", Path(__file__).parent), "block.py"),
                "--set",
                f"addresses_str={joined_addresses}",
                "--set",
                f"block_type={block_type}",
            ]
            # using _MEIPASS to make it compatible with pyinstaller
            # the os.path.join returns the location of block.py

            logger.debug(f"Starting mitmdump with command: {' '.join(args)}")

            subprocess.Popen(args, creationflags=CREATE_NO_WINDOW)
        else:
            block_py_path = Path(getattr(sys, "_MEIPASS", Path(__file__).parent)) / "block.py"
            if is_flatpak_sandbox():
                # this has to be done as flatpak build resets the last modified time of all source files to
                # epoch time 0, and mitmdump doesn't run block.py as a script if the last modified time is 0
                # this is a workaround which works by copying block.py's parent directory to xdg_data_home which
                # modifies the last modified time to the current time
                logger.debug("Running in Flatpak sandbox, copying block.py's parent directory to xdg_data_home")

                data_home_path: Path = Path(os.environ.get("XDG_DATA_HOME", ""))
                block_py_parent = block_py_path.parent

                dest_dir = data_home_path / block_py_parent.name

                shutil.copytree(block_py_parent, dest_dir, copy_function=shutil.copy, dirs_exist_ok=True)
                block_script_path = str(dest_dir / "block.py")

                logger.debug(f"Copied block.py's parent directory to: {dest_dir}")
            else:
                block_script_path = str(block_py_path)

            logger.debug(f"Using block.py path: {block_script_path}")

            args = [
                mitmdump_bin_path,
                "--set",
                "allow_remote=true",
                "-p",
                str(listening_port),
                "--showhost",
                "-s",
                block_script_path,
                "--set",
                f"addresses_str={joined_addresses}",
                "--set",
                f"block_type={block_type}",
            ]
            # using _MEIPASS to make it compatible with pyinstaller
            # the os.path.join returns the location of block.py

            logger.debug(f"Starting mitmdump with command: {' '.join(args)}")

            subprocess.Popen(args)
        return True

    def _on_start_completed(self, success, message) -> None:
        """Handle completion of start_blocking operation"""
        if success:
            self.blockingStarted.emit()
        else:
            self.operationError.emit(f"Failed to start blocking: {message}")

    def stop_blocking(self, delete_proxy: bool = True) -> None:
        """Stop website blocking in a separate thread."""
        logger.debug("Inside WebsiteBlockerManager.stop_blocking().")

        if delete_proxy:
            proxy_worker = ProxyWorker(self.proxy.delete_proxy)
            self.workers.append(proxy_worker)
            proxy_worker.start()

        worker = WebsiteBlockerWorker(self._shutdown_mitmdump)
        worker.operationCompleted.connect(self._on_stop_completed)
        self.workers.append(worker)
        worker.start()

    def _shutdown_mitmdump(self) -> bool:
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

    def _force_kill_process(self) -> bool:
        """Run kill_process in a thread to prevent GUI blocking"""
        kill_worker = ProxyWorker(kill_process)
        self.workers.append(kill_worker)
        kill_worker.start()
        return True

    def _on_stop_completed(self, success, message) -> None:
        """Handle completion of stop_blocking operation"""
        if not success:
            self.operationError.emit(f"Warning during blocking shutdown: {message}")

        self.blockingStopped.emit()

    def _start_after_stop(self) -> None:
        """Start mitmdump after stop_blocking has completed"""
        # disconnect the signal to prevent multiple connections as it would be reconnected in start_blocking
        self.blockingStopped.disconnect(self._start_after_stop)

        if self.pending_start_params:
            worker = WebsiteBlockerWorker(
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

    def cleanup(self) -> None:
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
