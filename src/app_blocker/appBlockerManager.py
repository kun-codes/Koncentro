from typing import Optional

from loguru import logger
from PySide6.QtCore import QObject, QThread

from app_blocker.appBlockerBackend import AppBlockerBackend
from app_blocker.backendFactory import get_app_blocker_backend
from app_blocker.constants import SCAN_INTERVAL_MS, STOP_POLL_MS


class AppBlockerWorker(QThread):
    def __init__(self, backend: AppBlockerBackend, targets: set[str]) -> None:
        super().__init__()
        self.backend = backend
        self.targets: set[str] = targets
        self._running: bool = True

    def stop(self) -> None:
        self._running = False

    def _sleep_scan_interval(self) -> None:
        slept_ms = 0
        while self._running and slept_ms < SCAN_INTERVAL_MS:
            self.msleep(STOP_POLL_MS)
            slept_ms += STOP_POLL_MS

    def run(self) -> None:
        signaled: set[int] = set()
        while self._running:
            live: set[int] = set()
            for target, pid in self.backend.find_blocked_pids(self.targets):
                if pid in signaled:
                    logger.info(f"{target}: pid {pid} still running after SIGTERM")
                    live.add(pid)
                    continue
                self.backend.terminate_pid(pid)
                logger.info(f"{target}: sent SIGTERM to pid {pid}")
                live.add(pid)
            signaled = live
            self._sleep_scan_interval()


class AppBlockerManager(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.backend: AppBlockerBackend = get_app_blocker_backend()
        self.worker: Optional[AppBlockerWorker] = None

    def start_blocking(self, targets: set[str]) -> None:
        self.stop_blocking()
        if not targets:
            return
        self.worker = AppBlockerWorker(self.backend, targets)
        self.worker.start()

    def stop_blocking(self) -> None:
        if self.worker is None:
            return
        if self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
        self.worker = None
