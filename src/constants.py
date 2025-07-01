from enum import Enum

# Application
ORGANIZATION_NAME = "Koncentro"
APPLICATION_NAME = "Koncentro"

# for pomodoro timer of new workspaces
WORK_DURATION = 25
BREAK_DURATION = 5
LONG_BREAK_DURATION = 15
WORK_INTERVALS = 2
AUTOSTART_WORK = True
AUTOSTART_BREAK = True
ENABLE_WEBSITE_BLOCKER = True

APPLICATION_UID = "com.bishwasaha.koncentro"

# for dotfile to detect if its the first time the app is run
FIRST_RUN_DOTFILE_NAME = ".first_run"

UPDATE_CHECK_URL = "https://api.github.com/repos/kun-codes/koncentro/releases/latest"
NEW_RELEASE_URL = "https://github.com/kun-codes/koncentro/releases/latest"


class WebsiteBlockType(Enum):
    BLOCKLIST = 0
    ALLOWLIST = 1


class URLListType(Enum):
    BLOCKLIST = "blocklist_urls"
    BLOCKLIST_EXCEPTION = "blocklist_exception_urls"
    ALLOWLIST = "allowlist_urls"
    ALLOWLIST_EXCEPTION = "allowlist_exception_urls"


class TimerState(Enum):
    """
    Tells what state the timer is in
    """

    NOTHING = "Begin Timer"
    WORK = "Focus"
    BREAK = "Break"
    LONG_BREAK = "Long Break"


class UpdateCheckResult(Enum):
    UP_TO_DATE = "App is up to date"
    UPDATE_AVAILABLE = "Update available"
    NETWORK_UNREACHABLE = "Network Unreachable"
    UNKNOWN_ERROR = "An unknown error occurred"
    UPDATE_URL_DOES_NOT_EXIST = "Update URL does not exist or is invalid"
    RATE_LIMITED = "GitHub API rate limit exceeded, try again later"


class InterfaceType(Enum):
    TASK_INTERFACE = 0
    POMODORO_INTERFACE = 1
    WEBSITE_BLOCKER_INTERFACE = 2
    SETTINGS_INTERFACE = 3

    DIALOG = -1


# https://pyqt-fluent-widgets.readthedocs.io/en/latest/navigation.html
class NavPanelButtonPosition(Enum):
    # 0 = Top Layout of Panel of Navigation Panel
    BACK_BUTTON = (0, 0)
    TASK_INTERFACE = (0, 2)
    POMODORO_INTERFACE = (0, 3)
    WEBSITE_BLOCKER_INTERFACE = (0, 4)

    # 1 = Scroll Layout of Panel of Navigation Panel

    # 2 = Bottom Layout of Panel of Navigation Panel
    WORKSPACE_MANAGER_DIALOG = (2, 0)
    SETTINGS_INTERFACE = (2, 1)


class WindowGeometryKeys(Enum):
    """Keys used for storing window geometry information in QSettings"""

    GEOMETRY = "MainWindow/geometry"
    IS_MAXIMIZED = "MainWindow/isMaximized"
