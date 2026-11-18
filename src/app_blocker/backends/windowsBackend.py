from app_blocker.appBlockerBackend import AppBlockerBackend, InstalledApp


class WindowsAppBlockerBackend(AppBlockerBackend):
    def list_installed_apps(self) -> list[InstalledApp]:
        raise NotImplementedError("App blocking is not implemented on windows yet")

    def find_blocked_pids(self, targets: set[str]) -> list[tuple[str, int]]:
        raise NotImplementedError("App blocking is not implemented on windows yet")

    def terminate_pid(self, pid: int) -> None:
        raise NotImplementedError("App blocking is not implemented on windows yet")
