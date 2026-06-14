import sys
from pathlib import Path
from typing import Optional

import psutil
from PySide6.QtCore import QObject, QThread


class AppBlockerWorker(QThread):
    def __init__(self, blocked_app_paths: set[Path]) -> None:
        super().__init__()
        self.blocked_app_paths = blocked_app_paths

    def run(self) -> None:
        if sys.platform == "linux":
            while True:
                for proc in psutil.process_iter(["exe"]):
                    try:
                        if proc.info["exe"] and Path(proc.info["exe"]) in self.blocked_app_paths:
                            proc.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                        pass
                self.msleep(2000)


class AppBlockerManager(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.worker: Optional[AppBlockerWorker] = None

    def start_blocking(self, blocked_app_paths: set[Path]) -> None:
        self.worker = AppBlockerWorker(blocked_app_paths)
        self.worker.start()

    def stop_blocking(self) -> None:
        if self.worker:
            self.worker.terminate()
