from enum import Enum

from qfluentwidgets import FluentIconBase, Theme, getIconColor

from resources import resources_rc


class CustomFluentIcon(FluentIconBase, Enum):
    """Custom icons"""

    AUTOSTART_BREAK = "autostart_break"
    AUTOSTART_WORK = "autostart_work"
    BREAK = "break"
    WEBSITE_BLOCKER_VIEW = "website_blocker_view"
    LONG_BREAK = "long_break"
    TASKS_VIEW = "tasks_view"
    WORK = "work"
    WORK_INTERVAL = "work_interval"
    WORKSPACE_SELECTOR_VIEW = "workspace_selector_view"
    PORT = "port"
    CHANGE_CURRENT_TASK = "change_current_task"
    PLAY_PAUSE = "play_pause"
    EXIT = "exit"
    CLICK = "click"
    TEXT_ADD = "text_add"
    SETUP_AGAIN = "setup_again"
    RESET_PROXY = "reset_proxy"
    UNINSTALL = "uninstall"
    MINIMIZE_TO_SYSTEM_TRAY_WIN = "minimize_to_system_tray_win"
    MINIMIZE_TO_SYSTEM_TRAY_MAC = "minimize_to_system_tray_mac"

    def path(self, theme=Theme.AUTO) -> str:
        # getIconColor() return "white" or "black" according to current theme
        return f":/iconsPrefix/icons/{self.value}_{getIconColor(theme)}.svg"
