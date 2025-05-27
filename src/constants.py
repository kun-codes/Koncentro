import os
import sys
from enum import Enum
from pathlib import Path

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
ENABLE_WEBSITE_FILTER = True

# for dotfile to detect if its the first time the app is run
FIRST_RUN_DOTFILE_NAME = ".first_run"

MITMDUMP_COMMAND_LINUX = (
    '{} --set allow_remote=true -p {} --showhost -s {} --set "addresses_str={}" --set "block_type={}"'.format(
        "{}",
        "{}",
        os.path.join(getattr(sys, "_MEIPASS", Path(__file__).parent), "website_blocker", "filter.py"),
        "{}",
        "{}",
    )
)  # using _MEIPASS to make it compatible with pyinstaller
# the os.path.join returns the location of filter.py

MITMDUMP_COMMAND_WINDOWS = (
    r"{} --set allow_remote=true -p {} --showhost -s {} --set addresses_str={} --set block_type={}".format(
        "{}",
        "{}",
        os.path.join(getattr(sys, "_MEIPASS", Path(__file__).parent), "website_blocker", "filter.py"),
        "{}",
        "{}",
    )
)  # using _MEIPASS to make it compatible with pyinstaller
# the os.path.join returns the location of filter.py

BLOCK_HTML_MESSAGE = f"<h1>Website blocked by {APPLICATION_NAME}!</h1>"

UPDATE_CHECK_URL = "https://raw.githubusercontent.com/kun-codes/koncentro/refs/heads/main/pyproject.toml"
NEW_RELEASE_URL = "https://github.com/kun-codes/koncentro/releases/latest"
MITMDUMP_SHUTDOWN_URL = f"http://shutdown.{APPLICATION_NAME.lower()}.internal/"


class WebsiteFilterType(Enum):
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


class InterfaceType(Enum):
    TASK_INTERFACE = 0
    POMODORO_INTERFACE = 1
    WEBSITE_FILTER_INTERFACE = 2
    SETTINGS_INTERFACE = 3

    DIALOG = -1


# https://pyqt-fluent-widgets.readthedocs.io/en/latest/navigation.html
class NavPanelButtonPosition(Enum):
    # 0 = Top Layout of Panel of Navigation Panel
    BACK_BUTTON = (0, 0)
    TASK_INTERFACE = (0, 2)
    POMODORO_INTERFACE = (0, 3)
    WEBSITE_FILTER_INTERFACE = (0, 4)

    # 1 = Scroll Layout of Panel of Navigation Panel

    # 2 = Bottom Layout of Panel of Navigation Panel
    WORKSPACE_MANAGER_DIALOG = (2, 0)
    SETTINGS_INTERFACE = (2, 1)
