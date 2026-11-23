from typing import Callable

from app_blocker.appBlockerBackend import AppBlockerBackend, InstalledApp


class MacOSAppBlockerBackend(AppBlockerBackend):
    def _enumeration_sources(self) -> list[Callable[[], list[InstalledApp]]]:
        raise NotImplementedError("App blocking is not implemented on macos yet")

    def find_blocked_pids(self, targets: set[str]) -> list[tuple[str, int]]:
        raise NotImplementedError("App blocking is not implemented on macos yet")

    def terminate_pid(self, pid: int) -> None:
        raise NotImplementedError("App blocking is not implemented on macos yet")
