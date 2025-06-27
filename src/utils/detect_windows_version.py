import sys


def isWin11():
    return sys.platform == "win32" and sys.getwindowsversion().build >= 22000


def isWin10OrEarlier():
    return sys.platform == "win32" and sys.getwindowsversion().build < 22000
