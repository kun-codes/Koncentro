import os
import platform
import socket
import threading
from pathlib import Path

from loguru import logger
from PySide6.QtCore import QModelIndex, QSize, Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from qfluentwidgets import (
    FluentIcon,
    InfoBar,
    InfoBarPosition,
    MessageBox,
    NavigationItemPosition,
    PushButton,
    SystemThemeListener,
    Theme,
    qconfig,
)

from config_paths import settings_dir
from config_values import ConfigValues
from constants import (
    APPLICATION_NAME,
    FIRST_RUN_DOTFILE_NAME,
    InterfaceType,
    TimerState,
    UpdateCheckResult,
    URLListType,
    WebsiteBlockType,
    WindowGeometryKeys,
)
from models.config import app_settings, load_workspace_settings, settings, workspace_specific_settings
from models.db_tables import TaskType
from models.task_list_model import TaskListModel
from models.workspace_list_model import WorkspaceListModel
from prefabs.customFluentIcon import CustomFluentIcon
from prefabs.koncentroFluentWindow import KoncentroFluentWindow
from resources import logos_rc
from tutorial.pomodoroInterfaceTutorial import PomodoroInterfaceTutorial
from tutorial.taskInterfaceTutorial import TaskInterfaceTutorial
from tutorial.websiteBlockerInterfaceTutorial import WebsiteBlockerInterfaceTutorial
from tutorial.workspaceManagerDialogTutorial import WorkspaceManagerDialogTutorial
from utils.check_for_updates import UpdateChecker
from utils.check_internet_worker import CheckInternetWorker
from utils.detect_windows_version import isWin10OrEarlier
from utils.find_mitmdump_executable import get_mitmdump_path
from utils.isMitmdumpRunning import isMitmdumpRunningWorker
from utils.time_conversion import convert_ms_to_hh_mm_ss
from views.dialogs.preSetupConfirmationDialog import PreSetupConfirmationDialog
from views.dialogs.setupAppDialog import SetupAppDialog
from views.dialogs.updateDialog import UpdateDialog
from views.dialogs.workspaceManagerDialog import ManageWorkspaceDialog
from views.subinterfaces.pomodoro_view import PomodoroView
from views.subinterfaces.settings_view import SettingsView
from views.subinterfaces.tasks_view import TaskListView
from views.subinterfaces.website_blocker_view import WebsiteBlockerView
from website_blocker.website_blocker_manager import WebsiteBlockerManager


class MainWindow(KoncentroFluentWindow):
    def __init__(self) -> None:
        super().__init__()
        self.initial_launch = True  # this keeps track of whether the window is showing for the first time or not
        # when app is un-minimized after minimizing the app, self.showEvent() will still be called which will trigger
        # the dialogs mentioned in self.showEvent() to show again which is an undesirable behaviour. So, to prevent
        # this, self.initial_launch is set to False when self.showEvent() is called for the first time

        self.is_first_run = self.check_first_run()
        # self.checkForUpdates()

        # if current alembic revision is older than latest alembic revision then update db

        self.update_checker = None
        self.mitmdump_check_worker = None

        self.workplace_list_model = WorkspaceListModel()

        self.task_interface = TaskListView()
        self.task_interface.setObjectName("task_interface")

        self.pomodoro_interface = PomodoroView()
        self.pomodoro_interface.setObjectName("pomodoro_interface")

        self.settings_interface = SettingsView()
        self.settings_interface.setObjectName("settings_interface")

        self.website_blocker_interface = WebsiteBlockerView(self.workplace_list_model)
        self.website_blocker_interface.setObjectName("website_blocker_interface")

        self.setObjectName("main_window")

        self.manage_workspace_dialog = None

        self.website_blocker_manager = WebsiteBlockerManager()

        self.themeListener = SystemThemeListener(self)
        self.themeListener.start()

        self.isSafeToShowTutorial = False

        self.initNavigation()
        self.initWindow()
        self.initSystemTray()
        self.initBottomBar()
        self.connectSignalsToSlots()

        self.website_blocker_interface.setEnabled(ConfigValues.ENABLE_WEBSITE_BLOCKER)

        self.navigationInterface.panel.setFixedHeight(48)

        self.updateDialog = None

        self.restoreWindowGeometry()

        if self.is_first_run:
            self.preSetupMitmproxy()  # self.checkForUpdates() is eventually called later due to this method call
        else:
            if ConfigValues.CHECK_FOR_UPDATES_ON_START:
                self.handleUpdates()

        self.remainingFontSubstitutions()

    def initNavigation(self) -> None:
        # Add sub interface
        self.addSubInterface(self.task_interface, CustomFluentIcon.TASKS_VIEW, "Tasks")
        self.addSubInterface(self.pomodoro_interface, FluentIcon.STOP_WATCH, "Pomodoro")
        self.addSubInterface(self.website_blocker_interface, CustomFluentIcon.WEBSITE_BLOCKER_VIEW, "Website Blocker")

        # Add sub interface at bottom
        self.navigationInterface.addItem(
            routeKey="WorkspaceSelector",
            icon=CustomFluentIcon.WORKSPACE_SELECTOR_VIEW,
            text="Select Workspace",
            onClick=lambda: self.onWorkspaceManagerClicked(),
            selectable=False,
            tooltip="Select the workspace to work in",
            position=NavigationItemPosition.BOTTOM,
        )
        self.addSubInterface(self.settings_interface, FluentIcon.SETTING, "Settings", NavigationItemPosition.BOTTOM)

    def initWindow(self) -> None:
        self.setMinimumWidth(715)
        self.setWindowTitle(APPLICATION_NAME)
        self.setWindowIcon(QIcon(":/logosPrefix/logos/logo.svg"))

        self.setMicaEffectEnabled(app_settings.get(app_settings.mica_enabled))

    def initSystemTray(self) -> None:
        """Initialize system tray icon and notifications"""
        self.tray = QSystemTrayIcon(self)

        self.tray_menu = QMenu()

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
        self.tray_menu_start_action.triggered.connect(lambda: self.pomodoro_interface.pauseResumeButton.click())

        self.tray_menu_pause_resume_action = self.tray_menu.addAction("Pause/Resume")
        self.tray_menu_pause_resume_action.setIcon(
            CustomFluentIcon.PLAY_PAUSE.icon(Theme.DARK if dark_mode_condition else Theme.LIGHT)
        )
        self.tray_menu_pause_resume_action.triggered.connect(lambda: self.pomodoro_interface.pauseResumeButton.click())
        self.tray_menu_pause_resume_action.setEnabled(False)

        self.tray_menu_stop_action = self.tray_menu.addAction("Stop")
        self.tray_menu_stop_action.setIcon(FluentIcon.CLOSE.icon(Theme.DARK if dark_mode_condition else Theme.LIGHT))
        self.tray_menu_stop_action.triggered.connect(lambda: self.pomodoro_interface.stopButton.click())

        self.tray_menu_skip_action = self.tray_menu.addAction("Skip")
        self.tray_menu_skip_action.setIcon(
            FluentIcon.CHEVRON_RIGHT.icon(Theme.DARK if dark_mode_condition else Theme.LIGHT)
        )
        self.tray_menu_skip_action.triggered.connect(lambda: self.pomodoro_interface.skipButton.click())

        self.tray_menu.addSeparator()

        self.tray_menu_quit_action = self.tray_menu.addAction("Quit")
        self.tray_menu_quit_action.setIcon(
            CustomFluentIcon.EXIT.icon(Theme.DARK if dark_mode_condition else Theme.LIGHT)
        )
        self.tray_menu_quit_action.triggered.connect(self.close)

        self.tray.setContextMenu(self.tray_menu)

        self.tray_white_icon = QIcon(":/logosPrefix/logos/logo-monochrome-white.svg")
        self.tray_black_icon = QIcon(":/logosPrefix/logos/logo-monochrome-black.svg")

        if is_gnome:
            initial_icon = self.tray_white_icon
        elif is_os_dark_mode:
            initial_icon = self.tray_white_icon
        else:
            initial_icon = self.tray_black_icon

        self.tray.setIcon(initial_icon)
        self.tray.setVisible(True)

    def remainingFontSubstitutions(self) -> None:
        # This was unaffected by font substitution in __main__.py
        font = QFont("Selawik", 14)
        self.pomodoro_interface.ProgressRing.setFont(font)

    def updateSystemTrayIcon(self) -> None:
        logger.debug("Updating system tray icon")
        # context menu of Windows 10 system tray icon is always in light mode for qt apps.
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
        is_gnome = "gnome" in desktop
        if is_gnome:
            self.tray.setIcon(self.tray_white_icon)
        elif qconfig.theme == Theme.DARK:
            self.tray.setIcon(self.tray_white_icon)
        else:
            self.tray.setIcon(self.tray_black_icon)

        if isWin10OrEarlier():
            return

        if qconfig.theme == Theme.DARK:
            self.tray_menu_timer_status_action.setIcon(FluentIcon.STOP_WATCH.icon(Theme.DARK))
            self.tray_menu_start_action.setIcon(FluentIcon.PLAY.icon(Theme.DARK))
            self.tray_menu_pause_resume_action.setIcon(CustomFluentIcon.PLAY_PAUSE.icon(Theme.DARK))
            self.tray_menu_stop_action.setIcon(FluentIcon.CLOSE.icon(Theme.DARK))
            self.tray_menu_skip_action.setIcon(FluentIcon.CHEVRON_RIGHT.icon(Theme.DARK))
            self.tray_menu_quit_action.setIcon(CustomFluentIcon.EXIT.icon(Theme.DARK))
        else:
            self.tray_menu_timer_status_action.setIcon(FluentIcon.STOP_WATCH.icon(Theme.LIGHT))
            self.tray_menu_start_action.setIcon(FluentIcon.PLAY.icon(Theme.LIGHT))
            self.tray_menu_pause_resume_action.setIcon(CustomFluentIcon.PLAY_PAUSE.icon(Theme.LIGHT))
            self.tray_menu_stop_action.setIcon(FluentIcon.CLOSE.icon(Theme.LIGHT))
            self.tray_menu_skip_action.setIcon(FluentIcon.CHEVRON_RIGHT.icon(Theme.LIGHT))
            self.tray_menu_quit_action.setIcon(CustomFluentIcon.EXIT.icon(Theme.LIGHT))

    def updateSystemTrayActions(self, timerState) -> None:
        if timerState in [TimerState.WORK, TimerState.BREAK, TimerState.LONG_BREAK]:
            self.tray_menu_pause_resume_action.setEnabled(True)
            self.tray_menu_start_action.setEnabled(False)
        else:
            self.tray_menu_pause_resume_action.setEnabled(False)
            self.tray_menu_start_action.setEnabled(True)

    # below 2 methods are for the bottom bar
    def initBottomBar(self) -> None:
        self.update_bottom_bar_timer_label()

        self.bottomBar.skipButton.setEnabled(self.pomodoro_interface.skipButton.isEnabled())
        self.bottomBar.pauseResumeButton.setCheckable(True)
        self.bottomBar.pauseResumeButton.setChecked(False)
        self.bottomBar.pauseResumeButton.setIcon(FluentIcon.PLAY)
        self.bottomBar.pauseResumeButton.clicked.connect(self.bottomBarPauseResumeButtonClicked)
        self.bottomBar.skipButton.clicked.connect(self.pomodoro_interface.skipButtonClicked)
        self.bottomBar.stopButton.clicked.connect(self.pomodoro_interface.stopButtonClicked)

        self.bottomBar.taskLabel.setText("Current Task: None")

    def bottomBarPauseResumeButtonClicked(self) -> None:
        # Sync state with pomodoro view button
        self.pomodoro_interface.pauseResumeButton.setChecked(self.bottomBar.pauseResumeButton.isChecked())
        logger.debug(f"Window state: {self.windowState()}")
        self.pomodoro_interface.pauseResumeButtonClicked()

        # Update bottom bar button icon
        if not self.bottomBar.pauseResumeButton.isChecked():
            self.bottomBar.pauseResumeButton.setIcon(FluentIcon.PLAY)
        else:
            self.bottomBar.pauseResumeButton.setIcon(FluentIcon.PAUSE)

    def showNotifications(self, timerState, isSkipped) -> None:
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
            elif not ConfigValues.AUTOSTART_WORK and not self.pomodoro_interface.isInitialWorkSession():
                # no point in showing that break has ended when work session is for the first time
                if self.pomodoro_interface.pomodoro_timer_obj.getSessionProgress() == 0.5:  # long break ended
                    title = "Long Break Ended"
                    message = "Long break has ended. Start the next work session"
                else:  # break ended
                    title = "Break Ended"
                    message = "Break has ended. Start the next work session"
        elif timerState in [TimerState.BREAK, TimerState.LONG_BREAK]:
            if ConfigValues.AUTOSTART_BREAK or (not ConfigValues.AUTOSTART_BREAK and isSkipped):
                if self.pomodoro_interface.pomodoro_timer_obj.getSessionProgress() == ConfigValues.WORK_INTERVALS:
                    title = "Long Break Session Started"
                    message = f"{long_break_duration}m long break session has started"
                else:
                    title = "Break Session Started"
                    message = f"{break_duration}m break session has started"
            else:
                if self.pomodoro_interface.pomodoro_timer_obj.getSessionProgress() == ConfigValues.WORK_INTERVALS:
                    title = "Work Session Ended"
                    message = "Work session has ended. Start the next long break session"
                else:
                    title = "Work Session Ended"
                    message = "Work session has ended. Start the next break session"
        elif timerState == TimerState.NOTHING:
            title = "Timer Stopped"
            message = "Timer has stopped"

        if title and message:
            self.tray.showMessage(
                title,
                message,
                QSystemTrayIcon.Information,
                5000,
            )

    def onWorkspaceManagerClicked(self) -> None:
        if self.manage_workspace_dialog is None:
            self.manage_workspace_dialog = ManageWorkspaceDialog(
                parent=self.window(), workspaceListModel=self.workplace_list_model
            )

        self.manage_workspace_dialog.show()
        self.showWorkspaceManagerTutorial()

    def toggleUIElementsBasedOnTimerState(self, timerState, _) -> None:
        # TODO: show a tip to stop the timer before changing settings when timer is running
        workspace_selector_button = self.navigationInterface.panel.widget("WorkspaceSelector")
        if timerState in [TimerState.WORK, TimerState.BREAK, TimerState.LONG_BREAK]:
            self.settings_interface.pomodoro_settings_group.setDisabled(True)
            workspace_selector_button.setDisabled(True)
            self.settings_interface.proxy_port_card.setDisabled(True)
            self.settings_interface.setup_app_card.setDisabled(True)
            if platform.system().lower() == "windows":
                self.settings_interface.uninstall_mitmproxy_certificate_card.setDisabled(True)
            self.settings_interface.reset_proxy_settings.setDisabled(True)
            self.pomodoro_interface.skipButton.setEnabled(True)
            self.bottomBar.skipButton.setEnabled(True)
        else:
            self.settings_interface.pomodoro_settings_group.setDisabled(False)
            workspace_selector_button.setDisabled(False)
            self.settings_interface.proxy_port_card.setDisabled(False)
            if platform.system().lower() == "windows":
                self.settings_interface.uninstall_mitmproxy_certificate_card.setDisabled(False)
            self.settings_interface.setup_app_card.setDisabled(False)
            self.settings_interface.reset_proxy_settings.setDisabled(False)
            self.pomodoro_interface.skipButton.setEnabled(False)
            self.bottomBar.skipButton.setEnabled(False)

    def on_session_resumed(self) -> None:
        """Only for cases when autostart work/break is disabled and session is resumed manually"""
        current_timer_state = self.pomodoro_interface.pomodoro_timer_obj.getTimerState()
        if current_timer_state == TimerState.WORK and not ConfigValues.AUTOSTART_WORK:
            logger.debug("Work session resumed and autostart work is off, checking if mitmdump is running...")

            # clean up any existing worker
            if self.mitmdump_check_worker and self.mitmdump_check_worker.isRunning():
                self.mitmdump_check_worker.quit()
                self.mitmdump_check_worker.wait()

            self.mitmdump_check_worker = isMitmdumpRunningWorker()
            self.mitmdump_check_worker.checkCompleted.connect(
                # using a tuple to combine multiple expressions into one as a lambda function
                # only accepts one expression
                lambda is_running: (
                    self.start_website_blocking() if not is_running else logger.debug("Mitmdump is already running"),
                    self.mitmdump_check_worker.deleteLater() if self.mitmdump_check_worker else None,
                    setattr(self, "mitmdump_check_worker", None),
                )[-1]  # Return None from the tuple as setattr always returns None
            )
            self.mitmdump_check_worker.start()
        elif current_timer_state in [TimerState.BREAK, TimerState.LONG_BREAK] and not ConfigValues.AUTOSTART_BREAK:
            logger.debug("Break session resumed and autostart break is off, stopping website blocking")
            self.stop_website_blocking()

    def on_timer_state_changed(self, timerState: TimerState, _):
        """For cases when autostart work/break is enabled"""
        if timerState == TimerState.WORK and ConfigValues.AUTOSTART_WORK:
            logger.debug("Work session started and autostart work is on, starting website blocking")
            self.start_website_blocking()
        elif timerState in [TimerState.BREAK, TimerState.LONG_BREAK] and ConfigValues.AUTOSTART_BREAK:
            logger.debug("Break session started and autostart break is on, stopping website blocking")
            self.stop_website_blocking()

    def on_session_stopped(self) -> None:
        """Handle session stopped signal - stop website blocking"""
        logger.debug("Session stopped, stopping website blocking")
        self.stop_website_blocking()

    def start_website_blocking(self) -> None:
        """Start website blocking with current settings"""
        if not ConfigValues.ENABLE_WEBSITE_BLOCKER:
            logger.debug("Website blocking is disabled, so not starting website blocking")
            return

        logger.debug("Starting website blocking")
        website_block_type = self.website_blocker_interface.model.get_website_block_type()
        logger.debug(f"website_block_type: {website_block_type}")

        urls = None
        block_type = None
        joined_urls = ""

        if website_block_type == WebsiteBlockType.BLOCKLIST:  # blocklist
            urls = self.website_blocker_interface.model.get_urls(URLListType.BLOCKLIST)
            block_type = "blocklist"
        elif website_block_type == WebsiteBlockType.ALLOWLIST:  # allowlist
            urls = self.website_blocker_interface.model.get_urls(URLListType.ALLOWLIST)
            block_type = "allowlist"

        logger.debug(f"URLs: {urls}")
        logger.debug(f"Block type: {block_type}")

        if urls is not None:  # find what to do when there are no urls registered
            joined_urls = ",".join(urls)

        mitmdump_path = get_mitmdump_path()
        self.website_blocker_manager.start_blocking(ConfigValues.PROXY_PORT, joined_urls, block_type, mitmdump_path)

    def stop_website_blocking(self) -> None:
        """Stop website blocking"""
        logger.debug("Stopping website blocking")
        self.website_blocker_manager.stop_blocking(delete_proxy=True)

    def handle_website_blocker_settings_change(self) -> None:
        """Handle changes to website blocker settings - restart blocking if currently in a work session"""
        current_timer_state = self.pomodoro_interface.pomodoro_timer_obj.getTimerState()
        is_timer_running = self.pomodoro_interface.pomodoro_timer_obj.pomodoro_timer.isActive()

        if current_timer_state == TimerState.WORK and is_timer_running:
            # Only restart blocking if we're in a work session and timer is actually running
            logger.debug("Website blocker settings changed during active work session, restarting blocking")
            self.stop_website_blocking()
            self.start_website_blocking()
        else:
            # Just stop blocking if we're not in an active work session
            logger.debug("Website blocker settings changed, stopping blocking")
            self.stop_website_blocking()

    def is_task_beginning(self):
        current_state = self.pomodoro_interface.pomodoro_timer_obj.getTimerState()
        previous_state = self.pomodoro_interface.pomodoro_timer_obj.previous_timer_state

        return (
            previous_state in [TimerState.NOTHING, TimerState.BREAK, TimerState.LONG_BREAK]
            and current_state == TimerState.WORK
        )

    def get_current_task_id(self):
        """
        Convenience method to get the current task id from the todoTasksList model
        """
        return self.task_interface.todoTasksList.model().currentTaskID()

    def get_current_task_index(self):
        """
        Convenience method to get the current task index from the todoTasksList model
        """
        return self.task_interface.todoTasksList.model().currentTaskIndex()

    def get_todo_task_list_item_delegate(self):
        """
        Convenience method to get the item delegate of the todo list
        """
        return self.task_interface.todoTasksList.itemDelegate()

    def spawnTaskStartedInfoBar(self, triggering_button: PushButton) -> None:
        if self.get_current_task_id() is None:
            return  # current task index can be None only when there is no tasks in todo list since when timer starts
        # a task would be automatically selected as the current task if any number of tasks other than zero are present
        # in the todo list

        # get name of task by its ID
        current_task_name = self.task_interface.todoTasksList.model().getTaskNameById(self.get_current_task_id())

        if triggering_button.isChecked():
            InfoBar.success(
                title="Task Started",
                content=f'Task named "{current_task_name}" has started',
                orient=Qt.Orientation.Vertical,
                isClosable=True,
                duration=5000,
                position=InfoBarPosition.TOP_RIGHT,
                parent=self,
            )

    def check_current_task_deleted(self, task_id) -> None:
        if self.get_current_task_id() is not None and self.get_current_task_id() == task_id:
            self.task_interface.todoTasksList.model().setCurrentTaskID(None)
            if self.pomodoro_interface.pomodoro_timer_obj.getTimerState() in [
                TimerState.WORK,
                TimerState.BREAK,
                TimerState.LONG_BREAK,
            ]:
                # make sure that the current task is deleted and the timer is running, without timer being running
                # there is no need to show infobar
                InfoBar.warning(
                    title="Current Task Deleted",
                    content="The task you were working on has been deleted.\n"
                    "Select another task as soon as possible to save your progress."
                    if self.task_interface.todoTasksList.model().rowCount() > 0
                    else "The task you were working on has been deleted.\n"
                    "Select another task as soon as possible to save your progress.",
                    orient=Qt.Orientation.Vertical,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=5000,
                    parent=self,
                )
                logger.debug("Current Task has been deleted")

    def check_current_task_moved(self, task_id, task_type: TaskType) -> None:
        if self.get_current_task_id() is not None:
            current_task_id = self.get_current_task_id()
        else:
            return  # no need to check if current task is moved if there is no current task

        if task_id == current_task_id and task_type == TaskType.COMPLETED:
            self.task_interface.todoTasksList.model().setCurrentTaskID(None)

            if self.pomodoro_interface.pomodoro_timer_obj.getTimerState() in [
                TimerState.WORK,
                TimerState.BREAK,
                TimerState.LONG_BREAK,
            ]:
                # make sure that the current task is moved into completed task list and the timer is running,
                # without timer being running there is no need to show infobar
                InfoBar.warning(
                    title="Current Task Completed",
                    content="The task you were working on has been completed.\n"
                    "Select another task as soon as possible to save your progress."
                    if self.task_interface.todoTasksList.model().rowCount() > 0
                    else "The task you were working on has been completed.\n"
                    "Add another task as soon as possible to save your progress.",
                    orient=Qt.Orientation.Vertical,
                    isClosable=True,
                    position=InfoBarPosition.TOP_RIGHT,
                    duration=5000,
                    parent=self,
                )

            logger.debug("Current Task has been moved")

    def updateTaskTime(self) -> None:
        if self.get_current_task_id() is not None:
            if self.pomodoro_interface.pomodoro_timer_obj.getTimerState() in [TimerState.BREAK, TimerState.LONG_BREAK]:
                return

            final_elapsed_time = (
                self.task_interface.todoTasksList.model().data(
                    self.get_current_task_index(), TaskListModel.ElapsedTimeRole
                )
                + self.pomodoro_interface.pomodoro_timer_obj.timer_resolution
            )
            if final_elapsed_time % 1000 == 0:  # only update db when the elapsed time is a multiple of 1000
                self.task_interface.todoTasksList.model().setData(
                    self.get_current_task_index(), final_elapsed_time, TaskListModel.ElapsedTimeRole, update_db=False
                )
            if final_elapsed_time % 5000 == 0:
                self.updateTaskTimeDB()

    def updateTaskTimeDB(self) -> None:
        # since sessionStoppedSignal is emitted when the timer is stopped, we have to check if the current task index
        # is valid or not. Current Task Index can be invalid due to it being None when there are no tasks in todo list
        # when timer began or when current task is deleted and session is stopped automatically
        current_task_index = self.get_current_task_id()
        if current_task_index is None:
            return

        final_elapsed_time = self.task_interface.todoTasksList.model().data(
            self.get_current_task_index(), TaskListModel.ElapsedTimeRole
        )
        self.task_interface.todoTasksList.model().setData(
            self.get_current_task_index(), final_elapsed_time, TaskListModel.ElapsedTimeRole, update_db=True
        )
        logger.debug(f"Updated DB with elapsed time: {final_elapsed_time}")

    def connectSignalsToSlots(self) -> None:
        self.pomodoro_interface.pomodoro_timer_obj.timerStateChangedSignal.connect(
            self.toggleUIElementsBasedOnTimerState
        )

        # handle website blocking start and stop
        self.pomodoro_interface.pomodoro_timer_obj.sessionStartedSignal.connect(self.on_session_resumed)
        self.pomodoro_interface.pomodoro_timer_obj.sessionStoppedSignal.connect(self.on_session_stopped)
        self.pomodoro_interface.pomodoro_timer_obj.timerStateChangedSignal.connect(self.on_timer_state_changed)

        # Auto set current task whenever a work session begins. current task won't be overwritten if it is already set
        self.pomodoro_interface.pomodoro_timer_obj.timerStateChangedSignal.connect(
            lambda timerState: self.task_interface.autoSetCurrentTaskID() if timerState == TimerState.WORK else None
        )
        self.pomodoro_interface.pauseResumeButton.clicked.connect(
            lambda: self.spawnTaskStartedInfoBar(self.pomodoro_interface.pauseResumeButton)
        )
        self.bottomBar.pauseResumeButton.clicked.connect(
            lambda: self.spawnTaskStartedInfoBar(self.bottomBar.pauseResumeButton)
        )
        self.pomodoro_interface.pomodoro_timer_obj.pomodoro_timer.timeout.connect(self.updateTaskTime)
        self.task_interface.completedTasksList.model().taskMovedSignal.connect(self.check_current_task_moved)
        self.pomodoro_interface.pomodoro_timer_obj.sessionStoppedSignal.connect(self.updateTaskTimeDB)
        self.task_interface.todoTasksList.model().taskDeletedSignal.connect(self.check_current_task_deleted)
        self.pomodoro_interface.pomodoro_timer_obj.durationSkippedSignal.connect(self.updateTaskTimeDB)
        self.pomodoro_interface.pomodoro_timer_obj.sessionPausedSignal.connect(self.updateTaskTimeDB)
        self.website_blocker_interface.blockTypeComboBox.currentIndexChanged.connect(
            lambda: self.handle_website_blocker_settings_change()
        )
        self.website_blocker_interface.saveButton.clicked.connect(
            lambda: self.handle_website_blocker_settings_change()
        )  # todo: check if the list has changed before restarting the blocking
        self.workplace_list_model.current_workspace_changed.connect(load_workspace_settings)
        self.workplace_list_model.current_workspace_changed.connect(
            self.website_blocker_interface.onCurrentWorkspaceChanged
        )
        self.workplace_list_model.current_workspace_changed.connect(
            self.task_interface.onCurrentWorkspaceChanged  # update task list when workspace is changed
        )
        self.pomodoro_interface.pomodoro_timer_obj.pomodoro_timer.timeout.connect(self.update_bottom_bar_timer_label)
        self.pomodoro_interface.pomodoro_timer_obj.timerStateChangedSignal.connect(self.update_bottom_bar_timer_label)
        workspace_specific_settings.enable_website_blocker.valueChanged.connect(
            self.on_website_block_enabled_setting_changed
        )
        workspace_specific_settings.enable_website_blocker.valueChanged.connect(
            lambda: self.handle_website_blocker_settings_change()
        )
        self.stackedWidget.mousePressEvent = self.onStackedWidgetClicked
        self.settings_interface.proxy_port_card.valueChanged.connect(self.update_proxy_port)

        self.task_interface.todoTasksList.model().currentTaskChangedSignal.connect(
            lambda task_id: self.bottomBar.taskLabel.setText(
                f"Current Task: {self.task_interface.todoTasksList.model().getTaskNameById(task_id)}"
            )
        )
        self.task_interface.todoTasksList.model().dataChanged.connect(self.updateBottomBarTaskLabel)
        self.themeListener.systemThemeChanged.connect(self.updateSystemTrayIcon)
        # for system tray
        self.pomodoro_interface.pomodoro_timer_obj.timerStateChangedSignal.connect(self.updateSystemTrayActions)
        # for notifications
        self.pomodoro_interface.pomodoro_timer_obj.timerStateChangedSignal.connect(self.showNotifications)

        self.stackedWidget.currentChanged.connect(self.showTutorial)

        # for mica effect
        self.settings_interface.micaEnableChanged.connect(self.setMicaEffectEnabled)

        self.pomodoro_interface.pomodoro_timer_obj.sessionPausedSignal.connect(self.setPauseResumeButtonsToPlayIcon)
        self.pomodoro_interface.pomodoro_timer_obj.sessionStoppedSignal.connect(self.setPauseResumeButtonsToPlayIcon)
        self.pomodoro_interface.pomodoro_timer_obj.sessionStartedSignal.connect(self.setPauseResumeButtonsToPauseIcon)
        self.pomodoro_interface.pomodoro_timer_obj.waitForUserInputSignal.connect(self.setPauseResumeButtonsToPlayIcon)
        self.pomodoro_interface.pomodoro_timer_obj.durationSkippedSignal.connect(self.setPauseResumeButtonsToPauseIcon)
        self.task_interface.todoTasksList.itemDelegate().pauseResumeButtonClicked.connect(
            lambda task_id, checked: self.setPauseResumeButtonsToPauseIcon(True)
            if checked
            else self.setPauseResumeButtonsToPlayIcon(True)
        )

        self.settings_interface.setup_app_card.clicked.connect(lambda: self.preSetupMitmproxy(False))
        self.settings_interface.reset_proxy_settings.clicked.connect(self.resetProxySettings)

    def resetProxySettings(self) -> None:
        logger.debug("Reset proxy settings button clicked")
        self.website_blocker_manager.stop_blocking(delete_proxy=True)
        self.settings_interface.proxy_port_card.setValue(8080)

        InfoBar.success(
            title="Proxy Settings Reset",
            content="Proxy settings have been reset successfully.",
            orient=Qt.Orientation.Vertical,
            isClosable=True,
            duration=5000,
            position=InfoBarPosition.TOP_RIGHT,
            parent=self,
        )
        logger.debug("Proxy settings have been reset successfully")

    def setPauseResumeButtonsToPauseIcon(self, skip_delegate_button: bool = False) -> None:
        logger.debug("Inside setPauseResumeButtonsToPauseIcon of MainWindow")
        self.pomodoro_interface.pauseResumeButton.setIcon(FluentIcon.PAUSE)
        self.pomodoro_interface.pauseResumeButton.setChecked(True)

        self.bottomBar.pauseResumeButton.setIcon(FluentIcon.PAUSE)
        self.bottomBar.pauseResumeButton.setChecked(True)

        # todo: find why this is required
        if skip_delegate_button or self.get_current_task_id() is None:
            return

        self.get_todo_task_list_item_delegate().buttons[self.get_current_task_id()].setChecked(True)
        self.get_todo_task_list_item_delegate().setCheckedStateOfButton(
            checked=True, task_id=self.get_current_task_id()
        )

    def setPauseResumeButtonsToPlayIcon(self, skip_delegate_button: bool = False) -> None:
        self.pomodoro_interface.pauseResumeButton.setIcon(FluentIcon.PLAY)
        self.pomodoro_interface.pauseResumeButton.setChecked(False)

        self.bottomBar.pauseResumeButton.setIcon(FluentIcon.PLAY)
        self.bottomBar.pauseResumeButton.setChecked(False)

        if skip_delegate_button or self.get_current_task_id() is None:
            return

        self.get_todo_task_list_item_delegate().buttons[self.get_current_task_id()].setChecked(False)
        self.get_todo_task_list_item_delegate().setCheckedStateOfButton(
            checked=False, task_id=self.get_current_task_id()
        )

    def updateBottomBarTaskLabel(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles) -> None:
        # if task name has been updated and only one index is updated (topLeft == bottomRight)
        if Qt.ItemDataRole.DisplayRole in roles and topLeft == bottomRight:
            triggeredTaskID = self.task_interface.todoTasksList.model().data(topLeft, TaskListModel.IDRole)
            # and if the current task ID is the same as the triggered task ID
            if self.get_current_task_id() == triggeredTaskID:
                # then update the bottom bar task label
                self.bottomBar.taskLabel.setText(
                    f"Current Task: {self.task_interface.todoTasksList.model().getTaskNameById(triggeredTaskID)}"
                )

    def showTutorial(self, index: int) -> None:
        self.isSafeToShowTutorial = True

        if (
            not ConfigValues.HAS_COMPLETED_TASK_VIEW_TUTORIAL
            and self.isSafeToShowTutorial
            and index == InterfaceType.TASK_INTERFACE.value
        ):
            self.taskInterfaceTutorial = TaskInterfaceTutorial(self, InterfaceType.TASK_INTERFACE)
            self.taskInterfaceTutorial.start()

        if (
            not ConfigValues.HAS_COMPLETED_POMODORO_VIEW_TUTORIAL
            and self.isSafeToShowTutorial
            and index == InterfaceType.POMODORO_INTERFACE.value
        ):
            self.pomodoroInterfaceTutorial = PomodoroInterfaceTutorial(self, InterfaceType.POMODORO_INTERFACE)
            self.pomodoroInterfaceTutorial.start()

        if (
            not ConfigValues.HAS_COMPLETED_WEBSITE_BLOCKER_VIEW_TUTORIAL
            and self.isSafeToShowTutorial
            and index == InterfaceType.WEBSITE_BLOCKER_INTERFACE.value
        ):
            self.websiteBlockerInterfaceTutorial = WebsiteBlockerInterfaceTutorial(
                self, InterfaceType.WEBSITE_BLOCKER_INTERFACE
            )
            self.websiteBlockerInterfaceTutorial.start()

    def showWorkspaceManagerTutorial(self) -> None:
        self.isSafeToShowTutorial = True

        if not ConfigValues.HAS_COMPLETED_WORKSPACE_MANAGER_DIALOG_TUTORIAL and self.isSafeToShowTutorial:
            self.workspaceManagerTutorial = WorkspaceManagerDialogTutorial(self, InterfaceType.DIALOG)
            self.workspaceManagerTutorial.start()

    def on_website_block_enabled_setting_changed(self) -> None:
        enable_website_block_setting_value = ConfigValues.ENABLE_WEBSITE_BLOCKER

        self.website_blocker_interface.setEnabled(enable_website_block_setting_value)

    def onStackedWidgetClicked(self, event) -> None:
        if self.stackedWidget.currentIndex() == 2 and not self.website_blocker_interface.isEnabled():
            # show an infobar to inform the user that website blocker is disabled and how it can be enabled
            InfoBar.warning(
                title="Website Blocker is Disabled",
                content="You can enable the website blocker from the settings view",
                orient=Qt.Orientation.Vertical,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=5000,
                parent=self,
            )

    def update_proxy_port(self) -> None:
        self.website_blocker_manager.proxy.port = ConfigValues.PROXY_PORT

    def update_bottom_bar_timer_label(self) -> None:
        # check if timer is running
        current_timer_state = self.pomodoro_interface.pomodoro_timer_obj.getTimerState()
        if current_timer_state in [TimerState.WORK, TimerState.BREAK, TimerState.LONG_BREAK]:
            # timer is running

            total_session_length_ms = 0
            if current_timer_state == TimerState.WORK:
                total_session_length_ms = ConfigValues.WORK_DURATION * 60 * 1000
            elif current_timer_state == TimerState.BREAK:
                total_session_length_ms = ConfigValues.BREAK_DURATION * 60 * 1000
            elif current_timer_state == TimerState.LONG_BREAK:
                total_session_length_ms = ConfigValues.LONG_BREAK_DURATION * 60 * 1000

            remaining_time_ms = self.pomodoro_interface.pomodoro_timer_obj.remaining_time

            if remaining_time_ms <= 0:  # have to compensate that the first second is not shown
                remaining_time_ms = total_session_length_ms

            hh, mm, ss = convert_ms_to_hh_mm_ss(remaining_time_ms)
            t_hh, t_mm, t_ss = convert_ms_to_hh_mm_ss(total_session_length_ms)

            timer_text = f"{current_timer_state.value}\n{hh:02d}:{mm:02d}:{ss:02d} / {t_hh:02d}:{t_mm:02d}:{t_ss:02d}"
            self.bottomBar.timerLabel.setText(timer_text)
            self.tray_menu_timer_status_action.setText(timer_text)

        else:
            # timer is not running
            hh, mm, ss = 0, 0, 0
            t_hh, t_mm, t_ss = 0, 0, 0

            timer_text = f"Idle\n{hh:02d}:{mm:02d}:{ss:02d} / {t_hh:02d}:{t_mm:02d}:{t_ss:02d}"
            self.bottomBar.timerLabel.setText(timer_text)
            self.tray_menu_timer_status_action.setText(timer_text)

    def check_first_run(self) -> bool:
        settings_dir_path = Path(settings_dir)
        first_run_dotfile_path = settings_dir_path.joinpath(FIRST_RUN_DOTFILE_NAME)

        if not first_run_dotfile_path.exists():
            logger.debug("First run detected")

            # create the first run dotfile
            first_run_dotfile_path.touch()

            return True

            # self.setupMitmproxy()

        return False

    def hasInternet(self) -> bool:
        try:
            socket.setdefaulttimeout(2)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("194.242.2.2", 53))  # using mullvad dns service
            # to maintain privacy
            # https://mullvad.net/en/help/dns-over-https-and-dns-over-tls#specifications
            return True
        except OSError:
            return False

    def preSetupMitmproxy(self, setup_first_time: bool = True) -> None:
        self.checkInternetWorker = CheckInternetWorker()
        self.checkInternetWorker.internetCheckCompleted.connect(
            lambda has_internet: self.setupMitmproxy(has_internet, setup_first_time)
        )
        self.checkInternetWorker.start()

    def setupMitmproxy(self, has_internet: bool, setup_first_time: bool = True) -> None:
        logger.debug("Setting up mitmproxy")

        logger.debug(f"has_internet: {has_internet}")
        logger.debug(f"setup_first_time: {setup_first_time}")

        if not has_internet:
            logger.info("No internet connection detected")
            contentText = f"Internet connection is required to set up {APPLICATION_NAME}"
            contentText += " for the first time.\n\n" if setup_first_time else "\n\n"
            contentText += f"{APPLICATION_NAME}'s website blocker needs internet to setup and verify it.\n"
            contentText += f"You can use {APPLICATION_NAME} without internet after setup." if setup_first_time else ""
            self.notHasInternetDialog = MessageBox("No Internet Connection Detected", contentText, self.window())
            self.notHasInternetDialog.cancelButton.hide()
            if setup_first_time:
                self.notHasInternetDialog.yesButton.clicked.connect(
                    self.onSetupAppConfirmationDialogRejected
                )  # this is
            # equivalent to clicking the cancel button to setting up mitmproxy
            else:
                self.notHasInternetDialog.yesButton.clicked.connect(self.notHasInternetDialog.close)  # close the dialog
                # when activated from settings interface, will not delete first run dotfile used to check if app
                # is running for the first time

            self.notHasInternetDialog.show()
            return

        logger.info("Internet connection detected. Proceeding with setup")
        if setup_first_time:
            self.setupAppConfirmationDialog = PreSetupConfirmationDialog(parent=self.window())

            # setupAppDialog is a modal dialog, so it will block the main window until it is closed
            self.setupAppConfirmationDialog.accepted.connect(
                lambda: self.handleUpdates() if ConfigValues.CHECK_FOR_UPDATES_ON_START else None
            )
            self.setupAppConfirmationDialog.rejected.connect(self.onSetupAppConfirmationDialogRejected)
            self.setupAppConfirmationDialog.show()
        else:
            self.setupAppDialog = SetupAppDialog(self.window(), False)  # skip setupAppConfirmationDialog as user
            # gave permission already
            self.setupAppDialog.show()

    def onSetupAppConfirmationDialogRejected(self) -> None:
        # delete the first run file so that the setup dialog is shown again when the app is started next time
        settings_dir_path = Path(settings_dir)
        first_run_dotfile_path = settings_dir_path.joinpath(FIRST_RUN_DOTFILE_NAME)

        if first_run_dotfile_path.exists():
            first_run_dotfile_path.unlink()

        self.quitApplication()

    def handleUpdates(self) -> None:
        # Using the threaded update checker to avoid freezing the GUI
        if not self.update_checker:
            self.update_checker = UpdateChecker()
            # Connect signal to handle update check result
            self.update_checker.updateCheckComplete.connect(self.onUpdateCheckComplete)

        # Start the update check in a background thread
        self.update_checker.start()

    def onUpdateCheckComplete(self, result) -> None:
        """Handle the result of the update check from the background thread."""
        # The result is now already an UpdateCheckResult enum instance, no conversion needed

        if result == UpdateCheckResult.UPDATE_AVAILABLE:
            # making the updateDialog
            self.updateDialog = UpdateDialog(parent=self.window())

            # for first run, the control flow is like this
            # self.setupMitmproxy() ---MainWindow is show---> self.setupAppDialog.show() ---
            # ---setupAppDialog is closed---> self.handleUpdates()

            # for runs which aren't first run, self.setupMitmproxy() is not run, so self.updateDialog is shown
            # when MainWindow is shown, in self.showEvent()
            if self.updateDialog is not None:
                self.updateDialog.finished.connect(lambda: self.showTutorial(InterfaceType.TASK_INTERFACE.value))
                self.updateDialog.show()
        elif result == UpdateCheckResult.UP_TO_DATE:
            self.showTutorial(InterfaceType.TASK_INTERFACE.value)
        elif result == UpdateCheckResult.NETWORK_UNREACHABLE:
            InfoBar.error(
                title="Update Check Failed",
                content="Failed to check for updates: Network is unreachable",
                orient=Qt.Orientation.Vertical,
                isClosable=True,
                duration=5000,
                position=InfoBarPosition.TOP_RIGHT,
                parent=self.window(),
            )
            self.showTutorial(InterfaceType.TASK_INTERFACE.value)
        elif result == UpdateCheckResult.UPDATE_URL_DOES_NOT_EXIST or UpdateCheckResult.RATE_LIMITED:
            self.showTutorial(InterfaceType.TASK_INTERFACE.value)

    def showEvent(self, event) -> None:
        logger.debug("MainWindow showEvent")
        super().showEvent(event)

        if not self.initial_launch:
            return

        self.initial_launch = False
        if self.is_first_run and self.setupAppConfirmationDialog is not None:
            self.setupAppConfirmationDialog.show()
        elif self.updateDialog is not None:
            self.updateDialog.show()

    def quitApplication(self) -> None:
        logger.debug("Quitting application...")
        app_instance = QApplication.instance()
        app_instance.exit()

    def closeEvent(self, event) -> None:
        self.saveWindowGeometry()

        # Accept the event immediately to close the window
        event.accept()
        logger.debug("Closing window immediately...")

        # Run cleanup tasks in a background thread
        cleanup_thread = threading.Thread(
            target=self._cleanup_background_tasks,
        )
        cleanup_thread.start()

    def _cleanup_background_tasks(self) -> None:
        logger.debug("Running cleanup tasks in background thread...")
        try:
            self.updateTaskTimeDB()
            self.website_blocker_manager.stop_blocking(delete_proxy=True)
            self.website_blocker_manager.cleanup()
            self.themeListener.terminate()
            self.themeListener.deleteLater()
            logger.debug("Cleanup tasks completed successfully.")
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
        finally:
            self.quitApplication()

    def saveWindowGeometry(self) -> None:
        settings.setValue(WindowGeometryKeys.GEOMETRY.value, self.saveGeometry())
        settings.setValue(WindowGeometryKeys.IS_MAXIMIZED.value, self.isMaximized())
        settings.sync()

    def restoreWindowGeometry(self) -> None:
        # set default size depending on the screen size
        screen = QApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        default_width = int(screen_geometry.width() * 0.60)
        default_height = int(screen_geometry.height() * 0.80)
        default_size = QSize(default_width, default_height)

        if settings.contains(WindowGeometryKeys.GEOMETRY.value):
            geometry = settings.value(WindowGeometryKeys.GEOMETRY.value)
            is_maximized = settings.value(WindowGeometryKeys.IS_MAXIMIZED.value, False, type=bool)

            if geometry:
                self.restoreGeometry(geometry)
            if is_maximized:
                self.showMaximized()
        else:
            self.resize(default_size)
