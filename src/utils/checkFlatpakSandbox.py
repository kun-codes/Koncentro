import os
import platform


def is_flatpak_sandbox() -> bool:
    if platform.system() == "Linux" and os.environ.get("container") is not None:  # is running in flatpak
        return True
    else:
        return False
