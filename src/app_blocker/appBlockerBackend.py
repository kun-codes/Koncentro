from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from enum import StrEnum
from typing import Callable, Optional

from PySide6.QtCore import QSize
from PySide6.QtGui import QGuiApplication, QIcon, QPixmap


class AppKind(StrEnum):
    NATIVE = "native"
    FLATPAK = "flatpak"
    SNAP = "snap"
    PATH = "path"


class InstalledApp:
    def __init__(
        self, app_id: str, app_name: str, target: str, kind: AppKind, app_icon_name: Optional[str] = None
    ) -> None:
        self.app_id = app_id
        self.app_name = app_name
        self.target = target
        self.kind = kind
        self.app_icon_name = app_icon_name

    @property
    def app_qicon(self) -> Optional[QIcon]:
        if not self.app_icon_name or QGuiApplication.instance() is None:
            return None
        return QIcon.fromTheme(self.app_icon_name)

    @property
    def app_icon(self) -> Optional[QPixmap]:
        icon = self.app_qicon
        if icon is None:
            return None
        pixmap = icon.pixmap(QSize(48, 48))
        return None if pixmap.isNull() else pixmap

    def __repr__(self) -> str:
        return f"InstalledApp({self.app_id!r}, {self.app_name!r}, {self.target!r}, {self.kind!r})"


class AppBlockerBackend(ABC):
    def setup_icon_theme(self) -> None:
        pass

    def list_installed_apps(self) -> list[InstalledApp]:
        sources = self._enumeration_sources()
        if len(sources) == 1:
            return sources[0]()

        apps: list[InstalledApp] = []
        with ThreadPoolExecutor(max_workers=len(sources)) as pool:
            futures = [pool.submit(source) for source in sources]
            for future in futures:
                apps += future.result()
        return apps

    @abstractmethod
    def _enumeration_sources(self) -> list[Callable[[], list[InstalledApp]]]:
        """Declare the backend's enumeration sources; they are scanned in parallel"""
        pass

    @abstractmethod
    def find_blocked_pids(self, targets: set[str]) -> list[tuple[str, int]]:
        pass

    @abstractmethod
    def terminate_pid(self, pid: int) -> None:
        pass
