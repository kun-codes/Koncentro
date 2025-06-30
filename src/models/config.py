import platform

import darkdetect
from loguru import logger
from PySide6.QtCore import QSettings
from PySide6.QtDBus import QDBusInterface, QDBusMessage, QDBusVariant
from qfluentwidgets import BoolValidator, ConfigItem, QConfig, RangeConfigItem, RangeValidator, Theme, qconfig

from config_paths import settings_file_path
from constants import (
    APPLICATION_NAME,
    AUTOSTART_BREAK,
    AUTOSTART_WORK,
    BREAK_DURATION,
    ENABLE_WEBSITE_FILTER,
    LONG_BREAK_DURATION,
    ORGANIZATION_NAME,
    WORK_DURATION,
    WORK_INTERVALS,
)
from models.db_tables import Workspace
from prefabs.config.config_item_sql import ConfigItemSQL, RangeConfigItemSQL
from prefabs.config.qconfig_sql import QConfigSQL, qconfig_custom
from utils.detect_windows_version import isWin11


class WorkspaceSettings(QConfigSQL):
    """
    Used for storing settings unique to a workspace in the app.
    Documentation for QConfig is here: https://qfluentwidgets.com/pages/components/config/#usage
    """

    work_duration = RangeConfigItemSQL(Workspace, Workspace.work_duration, WORK_DURATION, RangeValidator(1, 240))
    break_duration = RangeConfigItemSQL(Workspace, Workspace.break_duration, BREAK_DURATION, RangeValidator(1, 60))
    long_break_duration = RangeConfigItemSQL(
        Workspace, Workspace.long_break_duration, LONG_BREAK_DURATION, RangeValidator(1, 60)
    )
    work_intervals = RangeConfigItemSQL(Workspace, Workspace.work_intervals, WORK_INTERVALS, RangeValidator(1, 10))
    autostart_work = ConfigItemSQL(Workspace, Workspace.autostart_work, AUTOSTART_WORK, BoolValidator())
    autostart_break = ConfigItemSQL(Workspace, Workspace.autostart_break, AUTOSTART_BREAK, BoolValidator())
    enable_website_filter = ConfigItemSQL(
        Workspace, Workspace.enable_website_filter, ENABLE_WEBSITE_FILTER, BoolValidator()
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
    has_completed_website_filter_view_tutorial = ConfigItem(
        "AppSettings", "HasCompletedWebsiteFilterViewTutorial", False, BoolValidator()
    )
    has_completed_workspace_manager_dialog_tutorial = ConfigItem(
        "AppSettings", "HasCompletedWorkspaceManagerDialogTutorial", False, BoolValidator()
    )
    mica_enabled = ConfigItem("MainWindow", "MicaEnabled", isWin11(), BoolValidator())


workspace_specific_settings = WorkspaceSettings()
app_settings = AppSettings()
settings = QSettings(QSettings.Format.NativeFormat, QSettings.Scope.UserScope, ORGANIZATION_NAME, APPLICATION_NAME)

app_settings.themeMode.value = Theme.AUTO


def load_workspace_settings():
    qconfig_custom.load("", workspace_specific_settings)  # passing empty string as the path as function asks for path
    # to json file which stores settings and we are using db to store settings


def load_app_settings():
    qconfig.load(settings_file_path, app_settings)


@property
def theme_override(self):
    """Get theme mode"""
    return self._theme


@theme_override.setter
def theme_override(self, t):
    """Change the theme without modifying the config file"""
    if t == Theme.AUTO:
        # Try dbus first
        try:
            iface = QDBusInterface(
                "org.freedesktop.portal.Desktop",
                "/org/freedesktop/portal/desktop",
                "org.freedesktop.portal.Settings",
            )

            # Check if the interface is valid
            if not iface.isValid():
                raise ValueError("DBus interface is not valid")

            reply: QDBusMessage = iface.call("Read", "org.freedesktop.appearance", "color-scheme")

            # Handle QDBusMessage reply
            value = None
            if isinstance(reply, QDBusMessage):
                if reply.type() == QDBusMessage.MessageType.ReplyMessage:
                    args = reply.arguments()
                    if args:
                        value: QDBusVariant = args[0]
                    else:
                        raise ValueError("No arguments in DBus reply")
                else:
                    raise ValueError(f"DBus error: {reply.errorMessage()}")

            # Extract the actual value from QDBusVariant with recursive unwrapping
            actual_value: QDBusVariant = value
            max_unwrap_attempts = 5  # Prevent infinite loops
            unwrap_count = 0

            # Keep unwrapping variants until we get the actual value
            while unwrap_count < max_unwrap_attempts:
                logger.debug(f"Unwrap attempt {unwrap_count + 1}: {actual_value} (type: {type(actual_value)})")

                if hasattr(actual_value, "variant") and callable(actual_value.variant):
                    actual_value = actual_value.variant()
                    unwrap_count += 1
                else:
                    # No more unwrapping possible
                    logger.debug("No 'variant' attribute found, breaking out of unwrapping loop.")
                    break

            logger.debug(f"Final unwrapped value: {actual_value} (type: {type(actual_value)})")

            # The Portal Settings returns the value in a specific format
            # It should be a variant containing (namespace, key, value) tuple or just the value
            if actual_value is not None and isinstance(actual_value, (int, float)):
                color_scheme = int(actual_value)
            else:
                raise ValueError("Expected an int or a tuple/list with an int value")

            logger.debug(f"Extracted color scheme from dbus: {color_scheme}")

            if color_scheme is not None:
                if color_scheme == 1:  # Dark mode
                    t = Theme.DARK
                    logger.debug("Using theme from dbus: DARK")
                elif color_scheme == 2:  # Light mode
                    t = Theme.LIGHT
                    logger.debug("Using theme from dbus: LIGHT")
                else:  # 0 = no preference, fall through to other methods
                    raise ValueError(f"No preference set (color-scheme: {color_scheme})")
            else:
                raise ValueError("Could not extract color scheme value")

        except Exception as e:
            # fallback to darkdetect
            logger.debug(f"DBus error or fallback: {e}")
            try:
                detected_theme = darkdetect.theme()
                t = Theme(detected_theme) if detected_theme else Theme.LIGHT
                logger.debug(f"Detected theme: {detected_theme}, using {t}")
            except ImportError:
                logger.debug("darkdetect not available, using LIGHT theme")
                t = Theme.LIGHT

    self._theme = t


if platform.system() == "Linux":
    qconfig.__class__.theme = theme_override

load_app_settings()
load_workspace_settings()
