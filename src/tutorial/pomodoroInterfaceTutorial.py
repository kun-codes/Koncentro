from qfluentwidgets import FluentIcon, FluentWindow

from config_values import ConfigValues
from constants import InterfaceType, NavPanelButtonPosition
from models.config import app_settings
from prefabs.transientPopupTeachingTip import TransientPopupTeachingTip
from tutorial.interfaceTutorial import InterfaceTutorial
from utils.setNavButtonEnabled import setNavButtonEnabled


class PomodoroInterfaceTutorial(InterfaceTutorial):
    def __init__(self, main_window: FluentWindow, interface_type: InterfaceType):
        super().__init__(main_window, interface_type)

        self.tutorial_steps.append(self._first_step)
        self.tutorial_steps.append(self._show_pomodoro_timer_step)
        self.tutorial_steps.append(self._last_step)

    def _first_step(self):
        self.main_window.isSafeToShowTutorial = False  # block tutorials of other interfaces from showing

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.BACK_BUTTON, False)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.TASK_INTERFACE, False)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.WEBSITE_BLOCKER_INTERFACE, False)

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.WORKSPACE_MANAGER_DIALOG, False)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.SETTINGS_INTERFACE, False)
        self.next_step()

    def _show_pomodoro_timer_step(self):
        self._show_pomodoro_timer_step_tip = TransientPopupTeachingTip.create(
            target=self.main_window.pomodoro_interface.ProgressRing,
            title="This is the Pomodoro Timer",
            content="You can adjust Timer duration in the settings\n"
            "A copy of the timer is shown in the bottom bar for easy access",
            icon=FluentIcon.INFO,
            parent=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            mainWindow=self.main_window,
            isClosable=False,
            duration=-1,
            isDeleteOnClose=True,
        )
        self._show_pomodoro_timer_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._show_pomodoro_timer_step_tip)

    def _last_step(self):
        # this is the last step
        app_settings.set(app_settings.has_completed_pomodoro_view_tutorial, True)
        ConfigValues.HAS_COMPLETED_POMODORO_VIEW_TUTORIAL = True
        self.main_window.isSafeToShowTutorial = True  # allow other tutorials to show

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.BACK_BUTTON, True)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.TASK_INTERFACE, True)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.WEBSITE_BLOCKER_INTERFACE, True)

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.WORKSPACE_MANAGER_DIALOG, True)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.SETTINGS_INTERFACE, True)
