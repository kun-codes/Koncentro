from abc import ABC, abstractmethod
from enum import StrEnum
from typing import Optional

from PySide6.QtGui import QPixmap


class AppKind(StrEnum):
    NATIVE = "native"
    FLATPAK = "flatpak"
    SNAP = "snap"
    PATH = "path"


class InstalledApp:
    def __init__(
        self,
        app_id: str,
        app_name: str,
        target: str,
        kind: AppKind,
        app_icon: Optional[QPixmap] = None,
    ) -> None:
        self.app_id = app_id
        self.app_name = app_name
        self.target = target
        self.kind = kind
        self.app_icon = app_icon

    def __repr__(self) -> str:
        return f"InstalledApp({self.app_id!r}, {self.app_name!r}, {self.target!r}, {self.kind!r})"


class AppBlockerBackend(ABC):
    @abstractmethod
    def list_installed_apps(self) -> list[InstalledApp]:
        pass

    @abstractmethod
    def find_blocked_pids(self, targets: set[str]) -> list[tuple[str, int]]:
        pass

    @abstractmethod
    def terminate_pid(self, pid: int) -> None:
        pass
