from qfluentwidgets import FluentIcon, FluentWindow

from config_values import ConfigValues
from constants import InterfaceType
from models.config import app_settings
from prefabs.transientPopupTeachingTip import TransientPopupTeachingTip
from tutorial.interfaceTutorial import InterfaceTutorial


class WorkspaceManagerDialogTutorial(InterfaceTutorial):
    def __init__(self, main_window: FluentWindow, interface_type: InterfaceType):
        super().__init__(main_window, interface_type)

        self.tutorial_steps.append(self._first_step)
        self.tutorial_steps.append(self._introduce_website_manager_dialog_step)
        self.tutorial_steps.append(self._last_step)

    def _first_step(self):
        self.main_window.isSafeToShowTutorial = False
        self.next_step()

    def _introduce_website_manager_dialog_step(self):
        self._show_website_manager_dialog_step_tip = TransientPopupTeachingTip.create(
            target=self.main_window.manage_workspace_dialog.titleLabel,
            title="You can create and delete new workspaces here",
            content="Each workspace has its own tasks, pomodoro timer and website blocking settings.",
            icon=FluentIcon.INFO,
            parent=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            mainWindow=self.main_window,
            isClosable=False,
            duration=-1,
            isDeleteOnClose=True,
        )
        self._show_website_manager_dialog_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._show_website_manager_dialog_step_tip)

    def _last_step(self):
        app_settings.set(app_settings.has_completed_workspace_manager_dialog_tutorial, True)
        ConfigValues.HAS_COMPLETED_WORKSPACE_MANAGER_DIALOG_TUTORIAL = True
        self.main_window.isSafeToShowTutorial = True
