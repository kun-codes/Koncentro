from qfluentwidgets import FluentIcon, FluentWindow, TeachingTipTailPosition

from configValues import ConfigValues
from constants import InterfaceType, NavPanelButtonPosition, WebsiteBlockType
from models.config import app_settings
from prefabs.transientPopupTeachingTip import TransientPopupTeachingTip
from tutorial.interfaceTutorial import InterfaceTutorial
from utils.setNavButtonEnabled import setNavButtonEnabled


class WebsiteBlockerInterfaceTutorial(InterfaceTutorial):
    def __init__(self, main_window: FluentWindow, interface_type: InterfaceType) -> None:
        super().__init__(main_window, interface_type)

        self.tutorial_steps.append(self._first_step)
        self.tutorial_steps.append(self._select_website_block_type_step)
        self.tutorial_steps.append(self._enter_websites_step)
        self.tutorial_steps.append(self._save_websites_step)
        self.tutorial_steps.append(self._last_step)

    def _first_step(self) -> None:
        self.main_window.isSafeToShowTutorial = False

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.BACK_BUTTON, False)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.TASK_INTERFACE, False)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.POMODORO_INTERFACE, False)

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.WORKSPACE_MANAGER_DIALOG, False)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.SETTINGS_INTERFACE, False)
        self.next_step()

    def _select_website_block_type_step(self) -> None:
        self._select_website_block_type_step_tip = TransientPopupTeachingTip.create(
            target=self.main_window.website_blocker_interface.blockTypeComboBox,
            title="You can select the type of website block",
            content='"Blocklist" will block the websites you add to the list\n'
            '"Allowlist" will only allow the websites you add to the list and block all others',
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            tailPosition=TeachingTipTailPosition.TOP,
            icon=FluentIcon.INFO,
            parent=self.main_window,
            isClosable=False,
            duration=-1,
            isDeleteOnClose=True,
        )
        self._select_website_block_type_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._select_website_block_type_step_tip)

    def _enter_websites_step(self) -> None:
        current_website_block_type: WebsiteBlockType = (
            self.main_window.website_blocker_interface.model.get_website_block_type()
        )
        active_code_editor = (
            self.main_window.website_blocker_interface.blockListTextEdit
            if current_website_block_type == WebsiteBlockType.BLOCKLIST
            else self.main_window.website_blocker_interface.allowListTextEdit
        )

        action = "block" if current_website_block_type == WebsiteBlockType.BLOCKLIST else "allow"
        self._enter_website_block_tip = TransientPopupTeachingTip.create(
            target=active_code_editor,
            title=f"You can enter websites to {action} here",
            content="Multiple websites can be entered by typing them in separate lines.\n",
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            tailPosition=TeachingTipTailPosition.BOTTOM,
            icon=FluentIcon.INFO,
            parent=self.main_window,
            isClosable=False,
            duration=-1,
            isDeleteOnClose=True,
        )
        self._enter_website_block_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._enter_website_block_tip)

    def _save_websites_step(self) -> None:
        self._save_websites_step_tip = TransientPopupTeachingTip.create(
            target=self.main_window.website_blocker_interface.saveButton,
            title="Always save your changes after editing the list",
            content="",
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            tailPosition=TeachingTipTailPosition.TOP,
            icon=FluentIcon.INFO,
            parent=self.main_window,
            isClosable=False,
            duration=-1,
            isDeleteOnClose=True,
        )
        self._save_websites_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._save_websites_step_tip)

    def _last_step(self) -> None:
        # this is the last step
        app_settings.set(app_settings.has_completed_website_blocker_view_tutorial, True)
        ConfigValues.HAS_COMPLETED_WEBSITE_BLOCKER_VIEW_TUTORIAL = True
        self.main_window.isSafeToShowTutorial = True

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.BACK_BUTTON, True)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.TASK_INTERFACE, True)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.POMODORO_INTERFACE, True)

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.WORKSPACE_MANAGER_DIALOG, True)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.SETTINGS_INTERFACE, True)

        self.teaching_tips.clear()
        self.current_step = 0
