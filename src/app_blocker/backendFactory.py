import platform

from app_blocker.appBlockerBackend import AppBlockerBackend

os_name = platform.system()

# have to do this because `xdg` pypi package is only installed for linux. Without the following errors will happen
# on other platforms
if os_name == "Linux":
    from app_blocker.backends.linuxBackend import LinuxAppBlockerBackend
elif os_name == "Windows":
    from app_blocker.backends.windowsBackend import WindowsAppBlockerBackend
elif os_name == "Darwin":
    from app_blocker.backends.macosBackend import MacOSAppBlockerBackend


def get_app_blocker_backend() -> AppBlockerBackend:
    if os_name == "Linux":
        return LinuxAppBlockerBackend()
    if os_name == "Windows":
        return WindowsAppBlockerBackend()
    if os_name == "Darwin":
        return MacOSAppBlockerBackend()

    raise NotImplementedError(f"App blocking is not supported on {os_name!r}")
