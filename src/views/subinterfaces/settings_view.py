import platform

from loguru import logger
from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QApplication, QWidget
from qfluentwidgets import (
    CustomColorSettingCard,
    FluentIcon,
    InfoBar,
    InfoBarIcon,
    OptionsSettingCard,
    PrimaryPushButton,
    PrimaryPushSettingCard,
    SettingCard,
    SettingCardGroup,
    SwitchSettingCard,
    setCustomStyleSheet,
    setTheme,
    setThemeColor,
)

from config_values import ConfigValues
from constants import APPLICATION_NAME, NEW_RELEASE_URL, UpdateCheckResult
from models.config import app_settings, workspace_specific_settings
from prefabs.customFluentIcon import CustomFluentIcon
from prefabs.setting_cards.RangeSettingCardSQL import RangeSettingCardSQL
from prefabs.setting_cards.SpinBoxSettingCard import SpinBoxSettingCard
from prefabs.setting_cards.SpinBoxSettingCardSQL import SpinBoxSettingCardSQL
from prefabs.setting_cards.SwitchSettingCardSQL import SwitchSettingCardSQL
from ui_py.ui_settings_view import Ui_SettingsView
from utils.check_for_updates import UpdateChecker
from utils.detect_windows_version import isWin11
from utils.get_app_version import get_app_version
from views.dialogs.uninstallMitmproxyCertificateDialog import UninstallMitmproxyCertificateDialog


class SettingsView(QWidget, Ui_SettingsView):
    """
    For settings view of the app
    """

    micaEnableChanged = Signal(bool)

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)

        self.update_checker = None  # Will initialize when needed

        self.initSettings()
        self.initLayout()
        self.initQss()
        self.onValueChanged()

    def initSettings(self) -> None:
        # Pomodoro Settings
        self.pomodoro_settings_group = SettingCardGroup("Pomodoro", self.scrollArea)
        self.work_duration_card = RangeSettingCardSQL(
            workspace_specific_settings.work_duration,
            CustomFluentIcon.WORK,
            "Work Duration",
            "Set the work duration in minutes",
            self.pomodoro_settings_group,
        )
        self.break_duration_card = RangeSettingCardSQL(
            workspace_specific_settings.break_duration,
            CustomFluentIcon.BREAK,
            "Break Duration",
            "Set the break duration in minutes",
            self.pomodoro_settings_group,
        )
        self.long_break_duration_card = RangeSettingCardSQL(
            workspace_specific_settings.long_break_duration,
            CustomFluentIcon.LONG_BREAK,
            "Long Break Duration",
            "Set the long break duration in minutes",
            self.pomodoro_settings_group,
        )
        self.work_interval_card = SpinBoxSettingCardSQL(
            workspace_specific_settings.work_intervals,
            CustomFluentIcon.WORK_INTERVAL,
            "Work Intervals",
            "Set the number of work intervals before a long break",
            self.pomodoro_settings_group,
        )
        self.autostart_work_card = SwitchSettingCardSQL(
            CustomFluentIcon.AUTOSTART_WORK,
            "Autostart Work",
            "Start work session automatically after break ends",
            workspace_specific_settings.autostart_work,
            self.pomodoro_settings_group,
        )
        self.autostart_break_card = SwitchSettingCardSQL(
            CustomFluentIcon.AUTOSTART_BREAK,
            "Autostart Break",
            "Start break session automatically after work ends",
            workspace_specific_settings.autostart_break,
            self.pomodoro_settings_group,
        )

        # Website Blocker Settings
        self.website_blocker_settings_group = SettingCardGroup("Website Blocker", self.scrollArea)
        self.enable_website_blocker_card = SwitchSettingCardSQL(
            CustomFluentIcon.WEBSITE_BLOCKER_VIEW,
            "Enable Website Blocker",
            "Enable website blocking",
            workspace_specific_settings.enable_website_blocker,
            self.website_blocker_settings_group,
        )
        self.proxy_port_card = SpinBoxSettingCard(
            app_settings.proxy_port,
            CustomFluentIcon.PORT,
            "Proxy Port",
            "Select the port where the website blocker runs",
            self.website_blocker_settings_group,
        )

        # Personalization Settings
        self.personalization_settings_group = SettingCardGroup(self.tr("Personalization"), self.scrollArea)
        self.theme_card = OptionsSettingCard(
            app_settings.themeMode,
            FluentIcon.BRUSH,
            self.tr("Application theme"),
            self.tr("Change the appearance of your application"),
            texts=[self.tr("Light"), self.tr("Dark"), self.tr("Use system setting")],
            parent=self.personalization_settings_group,
        )
        self.theme_color_card = CustomColorSettingCard(
            app_settings.themeColor,
            FluentIcon.PALETTE,
            self.tr("Theme color"),
            self.tr("Change the theme color of you application"),
            self.personalization_settings_group,
        )
        if isWin11():
            self.mica_card = SwitchSettingCard(
                FluentIcon.TRANSPARENT,
                "Mica effect",
                "Apply semi transparent to windows and surfaces",
                app_settings.mica_enabled,
                self.personalization_settings_group,
            )

        # Update Settings
        self.update_settings_group = SettingCardGroup("Updates", self.scrollArea)
        self.check_for_updates_on_start_card = SwitchSettingCard(
            FluentIcon.UPDATE,
            "Check For Updates On Start",
            "New updates would be more stable and have more features",
            app_settings.check_for_updates_on_start,
            self.update_settings_group,
        )

        # Setup Group
        self.setup_group = SettingCardGroup("Setup", self.scrollArea)
        self.setup_app_card = PrimaryPushSettingCard(
            f"Setup {APPLICATION_NAME}",
            CustomFluentIcon.SETUP_AGAIN,
            f"Setup {APPLICATION_NAME} again",
            f"Click to setup {APPLICATION_NAME} again",
            self.setup_group,
        )  # connected in main_window.py
        operating_system = platform.system()
        if operating_system == "Darwin":
            operating_system = "macOS"
        self.uninstall_mitmproxy_certificate_card = PrimaryPushSettingCard(
            "Uninstall Certificate",
            CustomFluentIcon.UNINSTALL,
            f"Uninstall mitmproxy certificate for {APPLICATION_NAME}",
            f"Click to uninstall mitmproxy certificate for {APPLICATION_NAME}",
            self.setup_group,
        )
        self.reset_proxy_settings = PrimaryPushSettingCard(
            "Reset Proxy",
            CustomFluentIcon.RESET_PROXY,
            "Reset Proxy Settings",
            f"Click to reset proxy settings for {APPLICATION_NAME} and {operating_system}",
            self.setup_group,
        )  # connected in main_window.py

        # About Group
        self.about_group = SettingCardGroup("About", self.scrollArea)
        self.check_for_updates_now_card = PrimaryPushSettingCard(
            "Check Update",
            FluentIcon.UPDATE,
            "Check for updates now",
            f"Current Version: {get_app_version()}",
            self.about_group,
        )

        self.__connectSignalToSlot()

    def initLayout(self) -> None:
        # Pomodoro Settings
        self.pomodoro_settings_group.addSettingCard(self.work_duration_card)
        self.pomodoro_settings_group.addSettingCard(self.break_duration_card)
        self.pomodoro_settings_group.addSettingCard(self.long_break_duration_card)
        self.pomodoro_settings_group.addSettingCard(self.work_interval_card)
        self.pomodoro_settings_group.addSettingCard(self.autostart_work_card)
        self.pomodoro_settings_group.addSettingCard(self.autostart_break_card)
        self.work_interval_card.spinBox.setMinimumWidth(125)
        self.scrollAreaWidgetContents.layout().addWidget(self.pomodoro_settings_group)

        # Website Blocker Settings
        self.website_blocker_settings_group.addSettingCard(self.enable_website_blocker_card)
        self.website_blocker_settings_group.addSettingCard(self.proxy_port_card)
        self.proxy_port_card.spinBox.setSymbolVisible(False)
        self.proxy_port_card.spinBox.setMinimumWidth(150)
        self.scrollAreaWidgetContents.layout().addWidget(self.website_blocker_settings_group)

        # Personalization Settings
        self.personalization_settings_group.addSettingCard(self.theme_card)
        self.personalization_settings_group.addSettingCard(self.theme_color_card)
        if isWin11():
            self.personalization_settings_group.addSettingCard(self.mica_card)
        self.scrollAreaWidgetContents.layout().addWidget(self.personalization_settings_group)

        # Update Settings
        self.update_settings_group.addSettingCard(self.check_for_updates_on_start_card)
        self.scrollAreaWidgetContents.layout().addWidget(self.update_settings_group)

        # Setup Group
        self.setup_group.addSettingCard(self.setup_app_card)
        if platform.system().lower() == "windows":
            self.setup_group.addSettingCard(self.uninstall_mitmproxy_certificate_card)
        self.setup_group.addSettingCard(self.reset_proxy_settings)
        self.scrollAreaWidgetContents.layout().addWidget(self.setup_group)

        # About Group
        self.about_group.addSettingCard(self.check_for_updates_now_card)
        self.scrollAreaWidgetContents.layout().addWidget(self.about_group)

    def initQss(self) -> None:
        # increase size of contentLabel to improve readability
        qss_light = """
        QLabel#contentLabel {
            font: 12px 'Segoe UI', 'Microsoft YaHei', 'PingFang SC';
        }
        """
        qss_dark = qss_light

        # from: https://github.com/zhiyiYo/PyQt-Fluent-Widgets/issues/707
        # self.style().unpolish(self)
        # self.style().polish(self)

        settingCards = self.scrollArea.findChildren(SettingCard)
        for card in settingCards:
            setCustomStyleSheet(card, qss_light, qss_dark)

    def onValueChanged(self) -> None:
        workspace_specific_settings.work_duration.valueChanged.connect(self.updateWorkDuration)
        workspace_specific_settings.break_duration.valueChanged.connect(self.updateBreakDuration)
        workspace_specific_settings.long_break_duration.valueChanged.connect(self.updateLongBreakDuration)
        workspace_specific_settings.work_intervals.valueChanged.connect(self.updateWorkIntervals)
        workspace_specific_settings.autostart_work.valueChanged.connect(self.updateAutostartWork)
        workspace_specific_settings.autostart_break.valueChanged.connect(self.updateAutostartBreak)
        workspace_specific_settings.enable_website_blocker.valueChanged.connect(self.updateEnableWebsiteBlocker)

        app_settings.proxy_port.valueChanged.connect(self.updateProxyPort)
        app_settings.check_for_updates_on_start.valueChanged.connect(self.updateCheckForUpdatesOnStart)

    def updateBreakDuration(self) -> None:
        ConfigValues.BREAK_DURATION = workspace_specific_settings.get(workspace_specific_settings.break_duration)
        logger.debug(
            f"Updated Break Duration to: {workspace_specific_settings.get(workspace_specific_settings.break_duration)}"
        )

    def updateWorkDuration(self) -> None:
        ConfigValues.WORK_DURATION = workspace_specific_settings.get(workspace_specific_settings.work_duration)
        logger.debug(
            f"Updated Work Duration to: {workspace_specific_settings.get(workspace_specific_settings.work_duration)}"
        )

    def updateLongBreakDuration(self) -> None:
        ConfigValues.LONG_BREAK_DURATION = workspace_specific_settings.get(
            workspace_specific_settings.long_break_duration
        )
        logger.debug(
            f"Updated Long Break Duration to: "
            f"{workspace_specific_settings.get(workspace_specific_settings.long_break_duration)}"
        )

    def updateWorkIntervals(self) -> None:
        ConfigValues.WORK_INTERVALS = workspace_specific_settings.get(workspace_specific_settings.work_intervals)
        logger.debug(
            f"Updated Work Intervals to: {workspace_specific_settings.get(workspace_specific_settings.work_intervals)}"
        )

    def updateAutostartWork(self) -> None:
        ConfigValues.AUTOSTART_WORK = workspace_specific_settings.get(workspace_specific_settings.autostart_work)
        logger.debug(
            f"Updated Autostart Work to: {workspace_specific_settings.get(workspace_specific_settings.autostart_work)}"
        )

    def updateAutostartBreak(self) -> None:
        ConfigValues.AUTOSTART_BREAK = workspace_specific_settings.get(workspace_specific_settings.autostart_break)
        logger.debug(
            f"Updated Autostart Break to: "
            f"{workspace_specific_settings.get(workspace_specific_settings.autostart_break)}"
        )

    def updateEnableWebsiteBlocker(self) -> None:
        ConfigValues.ENABLE_WEBSITE_BLOCKER = workspace_specific_settings.get(
            workspace_specific_settings.enable_website_blocker
        )
        logger.debug(
            f"Enable Website Blocker: {
                workspace_specific_settings.get(workspace_specific_settings.enable_website_blocker)
            }"
        )

    def updateProxyPort(self) -> None:
        ConfigValues.PROXY_PORT = app_settings.get(app_settings.proxy_port)
        logger.debug(f"Proxy Port: {app_settings.get(app_settings.proxy_port)}")

    def updateCheckForUpdatesOnStart(self) -> None:
        ConfigValues.CHECK_FOR_UPDATES_ON_START = app_settings.get(app_settings.check_for_updates_on_start)
        logger.debug(f"Check For Updates On Start: {app_settings.get(app_settings.check_for_updates_on_start)}")

    def checkForUpdatesNow(self) -> None:
        """Check for updates using the UpdateChecker class"""
        # Show a small info message to let the user know we're checking for updates
        InfoBar.info(
            title="Checking for Updates",
            content="Checking for application updates...",
            orient=Qt.Orientation.Vertical,
            isClosable=True,
            duration=3000,
            parent=self,
        )

        # Initialize the update checker if it doesn't exist
        if not self.update_checker:
            self.update_checker = UpdateChecker()
            # Connect signal to handle update check result
            self.update_checker.updateCheckComplete.connect(self.onUpdateCheckComplete)

        # Start the update check in a background thread
        self.update_checker.start()

    def onUpdateCheckComplete(self, result) -> None:
        """Handle the result of the update check from the background thread."""
        if result == UpdateCheckResult.UPDATE_AVAILABLE:
            infoBar = InfoBar.new(
                icon=InfoBarIcon.SUCCESS,
                title="An Update is Available",
                content="Click to download the latest version now",
                orient=Qt.Vertical,  # Qt.Horizontal doesn't work correctly due to library bug
                isClosable=True,
                duration=5000,
                parent=self,
            )

            push_button = PrimaryPushButton(infoBar)
            push_button.setText("Download Now")

            url = QUrl(NEW_RELEASE_URL)
            push_button.clicked.connect(lambda: QDesktopServices.openUrl(url))

            infoBar.addWidget(push_button)
        elif result == UpdateCheckResult.UP_TO_DATE:
            InfoBar.info(
                title="App is up to date",
                content="You have the latest version of the app",
                orient=Qt.Orientation.Vertical,
                isClosable=True,
                duration=5000,
                parent=self,
            )
        elif result == UpdateCheckResult.NETWORK_UNREACHABLE:
            InfoBar.error(
                title="Failed to check for updates",
                content="Network is unreachable",
                orient=Qt.Orientation.Vertical,
                isClosable=True,
                duration=5000,
                parent=self,
            )

    def __connectSignalToSlot(self) -> None:
        self.theme_card.optionChanged.connect(lambda ci: setTheme(workspace_specific_settings.get(ci)))
        self.theme_color_card.colorChanged.connect(lambda c: setThemeColor(c))
        if isWin11():
            self.mica_card.checkedChanged.connect(self.micaEnableChanged)
        # self.proxy_port_card.valueChanged.connect

        self.check_for_updates_now_card.clicked.connect(self.checkForUpdatesNow)
        self.uninstall_mitmproxy_certificate_card.clicked.connect(self.uninstallMitmproxyCertificate)

    def uninstallMitmproxyCertificate(self) -> None:
        dialog = UninstallMitmproxyCertificateDialog(self)
        dialog.exec()


if __name__ == "__main__":
    app = QApplication()
    w = SettingsView()
    w.show()
    app.exec()
