import os

from loguru import logger
from PySide6.QtGui import QAction, QIcon
from PySide6.QtWidgets import QMenu, QSystemTrayIcon
from qfluentwidgets import FluentIcon, Theme, qconfig

from config_values import ConfigValues
from constants import TimerState
from prefabs.customFluentIcon import CustomFluentIcon
from utils.detect_windows_version import isWin10OrEarlier


class SystemTray(QSystemTrayIcon):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.tray_menu = QMenu()

        self.tray_white_icon = QIcon(":/logosPrefix/logos/logo-monochrome-white.svg")
        self.tray_black_icon = QIcon(":/logosPrefix/logos/logo-monochrome-black.svg")

        self.initSystemTray()

    def initSystemTray(self) -> None:
        """Initialize system tray icon and notifications"""
        is_os_dark_mode = qconfig.theme == Theme.DARK
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        is_gnome = "gnome" in desktop

        self.tray_menu_timer_status_action = self.tray_menu.addAction("Timer not running")
        self.tray_menu_timer_status_action.setIcon(
            FluentIcon.STOP_WATCH.icon(Theme.DARK if is_os_dark_mode else Theme.LIGHT)
        )
        self.tray_menu_timer_status_action.setEnabled(False)  # Make it non-clickable

        self.tray_menu.addSeparator()

        # Timer control actions
        # context menu of Windows 10 system tray icon is always in light mode for qt apps.
        self.tray_menu_start_action = self.tray_menu.addAction("Start")
        dark_mode_condition: bool = is_os_dark_mode and not isWin10OrEarlier()
        self.tray_menu_start_action.setIcon(FluentIcon.PLAY.icon(Theme.DARK if dark_mode_condition else Theme.LIGHT))

        self.tray_menu_pause_resume_action = self.tray_menu.addAction("Pause/Resume")
        self.tray_menu_pause_resume_action.setIcon(
            CustomFluentIcon.PLAY_PAUSE.icon(Theme.DARK if dark_mode_condition else Theme.LIGHT)
        )
        self.tray_menu_pause_resume_action.setEnabled(False)

        self.tray_menu_stop_action = self.tray_menu.addAction("Stop")
        self.tray_menu_stop_action.setIcon(FluentIcon.CLOSE.icon(Theme.DARK if dark_mode_condition else Theme.LIGHT))

        self.tray_menu_skip_action = self.tray_menu.addAction("Skip")
        self.tray_menu_skip_action.setIcon(
            FluentIcon.CHEVRON_RIGHT.icon(Theme.DARK if dark_mode_condition else Theme.LIGHT)
        )

        self.tray_menu.addSeparator()

        # not adding tray_menu_show_hide_action here, it will be done in onShouldMinimizeToSystemTraySettingChanged
        self.tray_menu_show_hide_action = QAction("Show/Hide")
        self.tray_menu_show_hide_action.setIcon(
            FluentIcon.VIEW.icon(Theme.DARK if dark_mode_condition else Theme.LIGHT)
        )
        self.tray_menu_after_show_hide_separator = QAction()
        self.tray_menu_after_show_hide_separator.setSeparator(True)

        self.tray_menu_quit_action = self.tray_menu.addAction("Quit")
        self.tray_menu_quit_action.setIcon(
            CustomFluentIcon.EXIT.icon(Theme.DARK if dark_mode_condition else Theme.LIGHT)
        )

        # onShouldMinimizeToSystemTraySettingChanged() adds self.tray_menu_show_hide_action to the tray menu and
        # related separators. Also connects/disconnects the tray icon activation signal to onSystemTrayActivated()
        #
        # calling onShouldMinimizeToSystemTraySettingChanged() manually as parent.connectSignalsToSlots() is called
        # after initializing systemTray in parent.__init()
        #
        # also calling after self.tray_menu_quit_action is created as it is used in
        # onShouldMinimizeToSystemTraySettingChanged()
        self.onShouldMinimizeToSystemTraySettingChanged(ConfigValues.SHOULD_MINIMIZE_TO_TRAY)

        self.setContextMenu(self.tray_menu)

        if is_gnome:
            initial_icon = self.tray_white_icon
        elif is_os_dark_mode:
            initial_icon = self.tray_white_icon
        else:
            initial_icon = self.tray_black_icon

        self.setIcon(initial_icon)
        self.setVisible(True)

    def onSystemTrayActivated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:  # single left click
            self.parent.toggleWindowVisibility()

    def updateSystemTrayIcon(self) -> None:
        logger.debug("Updating system tray icon")
        # context menu of Windows 10 system tray icon is always in light mode for qt apps.
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        is_gnome = "gnome" in desktop
        if is_gnome:
            self.setIcon(self.tray_white_icon)
        elif qconfig.theme == Theme.DARK:
            self.setIcon(self.tray_white_icon)
        else:
            self.setIcon(self.tray_black_icon)

        if isWin10OrEarlier():
            return

        if qconfig.theme == Theme.DARK:
            self.tray_menu_timer_status_action.setIcon(FluentIcon.STOP_WATCH.icon(Theme.DARK))
            self.tray_menu_start_action.setIcon(FluentIcon.PLAY.icon(Theme.DARK))
            self.tray_menu_pause_resume_action.setIcon(CustomFluentIcon.PLAY_PAUSE.icon(Theme.DARK))
            self.tray_menu_stop_action.setIcon(FluentIcon.CLOSE.icon(Theme.DARK))
            self.tray_menu_skip_action.setIcon(FluentIcon.CHEVRON_RIGHT.icon(Theme.DARK))
            self.tray_menu_show_hide_action.setIcon(FluentIcon.VIEW.icon(Theme.DARK))
            self.tray_menu_quit_action.setIcon(CustomFluentIcon.EXIT.icon(Theme.DARK))
        else:
            self.tray_menu_timer_status_action.setIcon(FluentIcon.STOP_WATCH.icon(Theme.LIGHT))
            self.tray_menu_start_action.setIcon(FluentIcon.PLAY.icon(Theme.LIGHT))
            self.tray_menu_pause_resume_action.setIcon(CustomFluentIcon.PLAY_PAUSE.icon(Theme.LIGHT))
            self.tray_menu_stop_action.setIcon(FluentIcon.CLOSE.icon(Theme.LIGHT))
            self.tray_menu_skip_action.setIcon(FluentIcon.CHEVRON_RIGHT.icon(Theme.LIGHT))
            self.tray_menu_show_hide_action.setIcon(FluentIcon.VIEW.icon(Theme.LIGHT))
            self.tray_menu_quit_action.setIcon(CustomFluentIcon.EXIT.icon(Theme.LIGHT))

    def updateSystemTrayActions(self, timerState) -> None:
        if timerState in [TimerState.WORK, TimerState.BREAK, TimerState.LONG_BREAK]:
            self.tray_menu_pause_resume_action.setEnabled(True)
            self.tray_menu_start_action.setEnabled(False)
        else:
            self.tray_menu_pause_resume_action.setEnabled(False)
            self.tray_menu_start_action.setEnabled(True)

    def showNotifications(self, timerState, isSkipped) -> None:
        from config_values import ConfigValues

        title = ""
        message = ""

        work_duration = ConfigValues.WORK_DURATION
        break_duration = ConfigValues.BREAK_DURATION
        long_break_duration = ConfigValues.LONG_BREAK_DURATION

        if timerState == TimerState.WORK:
            if ConfigValues.AUTOSTART_WORK or (not ConfigValues.AUTOSTART_WORK and isSkipped):
                # if ConfigValues.AUTOSTART_WORK:
                title = "Work Session Started"
                message = f"{work_duration}m work session has started"
            elif not ConfigValues.AUTOSTART_WORK and not self.parent.pomodoro_interface.isInitialWorkSession():
                # no point in showing that break has ended when work session is for the first time
                if self.parent.pomodoro_interface.pomodoro_timer_obj.getSessionProgress() == 0.5:  # long break ended
                    title = "Long Break Ended"
                    message = "Long break has ended. Start the next work session"
                else:  # break ended
                    title = "Break Ended"
                    message = "Break has ended. Start the next work session"
        elif timerState in [TimerState.BREAK, TimerState.LONG_BREAK]:
            if ConfigValues.AUTOSTART_BREAK or (not ConfigValues.AUTOSTART_BREAK and isSkipped):
                if (
                    self.parent.pomodoro_interface.pomodoro_timer_obj.getSessionProgress()
                    == ConfigValues.WORK_INTERVALS
                ):
                    title = "Long Break Session Started"
                    message = f"{long_break_duration}m long break session has started"
                else:
                    title = "Break Session Started"
                    message = f"{break_duration}m break session has started"
            else:
                if (
                    self.parent.pomodoro_interface.pomodoro_timer_obj.getSessionProgress()
                    == ConfigValues.WORK_INTERVALS
                ):
                    title = "Work Session Ended"
                    message = "Work session has ended. Start the next long break session"
                else:
                    title = "Work Session Ended"
                    message = "Work session has ended. Start the next break session"
        elif timerState == TimerState.NOTHING:
            title = "Timer Stopped"
            message = "Timer has stopped"

        if title and message:
            self.showMessage(
                title,
                message,
                QSystemTrayIcon.MessageIcon.Information,
                5000,
            )

    def onShouldMinimizeToSystemTraySettingChanged(self, value: bool) -> None:
        if value:
            self.tray_menu.insertAction(self.tray_menu_quit_action, self.tray_menu_show_hide_action)
            self.tray_menu.insertAction(self.tray_menu_quit_action, self.tray_menu_after_show_hide_separator)

            self.activated.connect(self.onSystemTrayActivated)
        else:
            self.tray_menu.removeAction(self.tray_menu_show_hide_action)
            self.tray_menu.removeAction(self.tray_menu_after_show_hide_separator)

            self.activated.disconnect(self.onSystemTrayActivated)

    def connectSignalsToSlots(self, pomodoro_interface, quit_callback, toggle_visibility_callback):
        """Connect system tray signals to main window callbacks"""
        self.tray_menu_start_action.triggered.connect(lambda: pomodoro_interface.pauseResumeButton.click())
        self.tray_menu_pause_resume_action.triggered.connect(lambda: pomodoro_interface.pauseResumeButton.click())
        self.tray_menu_stop_action.triggered.connect(lambda: pomodoro_interface.stopButton.click())
        self.tray_menu_skip_action.triggered.connect(lambda: pomodoro_interface.skipButton.click())
        self.tray_menu_show_hide_action.triggered.connect(toggle_visibility_callback)
        self.tray_menu_quit_action.triggered.connect(quit_callback)
