from PySide6.QtCore import QSettings
from qfluentwidgets import BoolValidator, ConfigItem, QConfig, RangeConfigItem, RangeValidator, Theme, qconfig

from configPaths import settings_file_path
from constants import (
    APPLICATION_NAME,
    DEFAULT_AUTOSTART_BREAK,
    DEFAULT_AUTOSTART_WORK,
    DEFAULT_BREAK_DURATION,
    DEFAULT_ENABLE_WEBSITE_BLOCKER,
    DEFAULT_LONG_BREAK_DURATION,
    DEFAULT_WORK_DURATION,
    DEFAULT_WORK_INTERVALS,
    ORGANIZATION_NAME,
)
from models.dbTables import Workspace
from prefabs.config.configItemSQL import ConfigItemSQL, RangeConfigItemSQL
from prefabs.config.qconfigSQL import QConfigSQL, qconfig_custom
from utils.detectWindowsVersion import isWin11
from utils.qconfigPatchTheme import apply_qconfig_theme_patch


class WorkspaceSettings(QConfigSQL):
    """
    Used for storing settings unique to a workspace in the app.
    Documentation for QConfig is here: https://qfluentwidgets.com/pages/components/config/#usage
    """

    work_duration = RangeConfigItemSQL(
        Workspace, Workspace.work_duration, DEFAULT_WORK_DURATION, RangeValidator(1, 240)
    )
    break_duration = RangeConfigItemSQL(
        Workspace, Workspace.break_duration, DEFAULT_BREAK_DURATION, RangeValidator(1, 60)
    )
    long_break_duration = RangeConfigItemSQL(
        Workspace, Workspace.long_break_duration, DEFAULT_LONG_BREAK_DURATION, RangeValidator(1, 60)
    )
    work_intervals = RangeConfigItemSQL(
        Workspace, Workspace.work_intervals, DEFAULT_WORK_INTERVALS, RangeValidator(1, 10)
    )
    autostart_work = ConfigItemSQL(Workspace, Workspace.autostart_work, DEFAULT_AUTOSTART_WORK, BoolValidator())
    autostart_break = ConfigItemSQL(Workspace, Workspace.autostart_break, DEFAULT_AUTOSTART_BREAK, BoolValidator())
    enable_website_blocker = ConfigItemSQL(
        Workspace, Workspace.enable_website_blocker, DEFAULT_ENABLE_WEBSITE_BLOCKER, BoolValidator()
    )


class AppSettings(QConfig):
    """
    Used for storing settings that are not workspace specific and global to the app.
    Documentation for QConfig is here: https://qfluentwidgets.com/pages/components/config/#usage
    """

    proxy_port = RangeConfigItem("AppSettings", "ProxyPort", 8080, RangeValidator(1024, 65535))
    check_for_updates_on_start = ConfigItem("AppSettings", "CheckForUpdatesOnStart", True, BoolValidator())
    has_completed_task_view_tutorial = ConfigItem("AppSettings", "HasCompletedTaskViewTutorial", False, BoolValidator())
    has_completed_pomodoro_view_tutorial = ConfigItem(
        "AppSettings", "HasCompletedPomodoroViewTutorial", False, BoolValidator()
    )
    has_completed_website_blocker_view_tutorial = ConfigItem(
        "AppSettings", "HasCompletedWebsiteBlockerViewTutorial", False, BoolValidator()
    )
    has_completed_workspace_manager_dialog_tutorial = ConfigItem(
        "AppSettings", "HasCompletedWorkspaceManagerDialogTutorial", False, BoolValidator()
    )
    mica_enabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())
    should_minimize_to_tray = ConfigItem("MainWindow", "ShouldMinimizeToTray", False, BoolValidator())


workspace_specific_settings = WorkspaceSettings()
app_settings = AppSettings()
settings = QSettings(QSettings.Format.NativeFormat, QSettings.Scope.UserScope, ORGANIZATION_NAME, APPLICATION_NAME)

app_settings.themeMode.value = Theme.AUTO


def load_workspace_settings() -> None:
    qconfig_custom.load("", workspace_specific_settings)  # passing empty string as the path as function asks for path
    # to json file which stores settings and we are using db to store settings


def load_app_settings() -> None:
    qconfig.load(settings_file_path, app_settings)


# A hacky way to apply the theme patch
# Only works if called from here, has something to do with module level functions calls
# which are called in mainWindow.py when config.py is imported
# position of apply_qconfig_theme_patch(), load_app_settings() and load_workspace_settings() is key here
apply_qconfig_theme_patch()

load_app_settings()
load_workspace_settings()
