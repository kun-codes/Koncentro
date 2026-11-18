import platform

from app_blocker.appBlockerBackend import AppBlockerBackend
from app_blocker.backends.linuxBackend import LinuxAppBlockerBackend
from app_blocker.backends.macosBackend import MacOSAppBlockerBackend
from app_blocker.backends.windowsBackend import WindowsAppBlockerBackend


def get_app_blocker_backend() -> AppBlockerBackend:
    backends = {
        "Linux": LinuxAppBlockerBackend,
        "Windows": WindowsAppBlockerBackend,
        "Darwin": MacOSAppBlockerBackend,
    }

    backend_class = backends.get(platform.system())
    if backend_class is None:
        raise NotImplementedError(f"App blocking is not supported on {platform.system()!r}")

    return backend_class()
