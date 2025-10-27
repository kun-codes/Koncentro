import sys


def isWin11() -> bool:
    return sys.platform == "win32" and sys.getwindowsversion().build >= 22000


def isWin10OrEarlier() -> bool:
    return sys.platform == "win32" and sys.getwindowsversion().build < 22000
