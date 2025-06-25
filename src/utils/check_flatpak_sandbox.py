import platform
import os


def is_flatpak_sandbox():
    if platform.system() == 'Linux' and os.environ.get('container') is not None:  # is running in flatpak
        return True
    else:
        return False

