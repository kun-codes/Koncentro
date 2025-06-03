
from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, FluentWindow, TeachingTipTailPosition

from config_values import ConfigValues
from constants import InterfaceType, NavPanelButtonPosition
from models.config import app_settings
from models.task_list_model import TaskListModel
from prefabs.customFluentIcon import CustomFluentIcon
from prefabs.targetClickTeachingTip import TargetClickTeachingTip
from prefabs.transientPopupTeachingTip import TransientPopupTeachingTip
from tutorial.interfaceTutorial import InterfaceTutorial
from utils.setNavButtonEnabled import setNavButtonEnabled
from views.dialogs.addTaskDialog import AddTaskDialog
from views.dialogs.editTaskTimeDialog import EditTaskTimeDialog


class TaskInterfaceTutorial(InterfaceTutorial):
    def __init__(self, main_window: FluentWindow, interface_type: InterfaceType):
        super().__init__(main_window, interface_type)

        self.tutorial_steps.append(self._first_step)
        self.tutorial_steps.append(self._todo_task_list_step)
        self.tutorial_steps.append(self._completed_task_list_step)
        self.tutorial_steps.append(self._select_first_task_step)
        self.tutorial_steps.append(self._invoke_first_task_edit_task_time_step)
        self.tutorial_steps.append(self._edit_first_task_elapsed_time_step)
        self.tutorial_steps.append(self._edit_first_task_estimate_time_step)
        self.tutorial_steps.append(self._edit_first_task_save_changed_time_step)
        self.tutorial_steps.append(self._delete_first_task_step)
        self.tutorial_steps.append(self._invoke_add_new_task_dialog_step)
        self.tutorial_steps.append(self._name_new_task_step)
        self.tutorial_steps.append(self._save_new_task_step)
        self.tutorial_steps.append(self._start_first_task_step)
        self.tutorial_steps.append(self._move_to_completed_task_list_step)
        self.tutorial_steps.append(self._stop_timer_step)
        self.tutorial_steps.append(self._enable_buttons)
        self.tutorial_steps.append(self._last_step)

    def _first_step(self):
        self.main_window.isSafeToShowTutorial = False  # block tutorials of other interfaces from showing

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.BACK_BUTTON, False)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.POMODORO_INTERFACE, False)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.WEBSITE_FILTER_INTERFACE, False)

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.WORKSPACE_MANAGER_DIALOG, False)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.SETTINGS_INTERFACE, False)

        self.next_step()

    def _todo_task_list_step(self):
        self._todo_task_list_step_tip = TransientPopupTeachingTip.create(
            target=self.main_window.task_interface.todoTasksList,
            title="This card contains all the tasks which you have to do",
            content="",
            icon=FluentIcon.INFO,
            parent=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            mainWindow=self.main_window,
            isClosable=False,
            duration=-1,
            isDeleteOnClose=True
        )
        self._todo_task_list_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._todo_task_list_step_tip)

    def _completed_task_list_step(self):
        self._completed_task_list_step_tip = TransientPopupTeachingTip.create(
            target=self.main_window.task_interface.completedTasksList,
            title="This card contains all the tasks which you have completed",
            content="",
            icon=FluentIcon.INFO,
            parent=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            mainWindow=self.main_window,
            isClosable=False,
            duration=-1,
            isDeleteOnClose=True
        )
        self._completed_task_list_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._completed_task_list_step_tip)

    def _select_first_task_step(self):
        # Get the todo task list
        todo_task_list = self.main_window.task_interface.todoTasksList
        first_index = todo_task_list.model().index(0, 0)
        rect = todo_task_list.visualRect(first_index)

        overlay = QWidget(todo_task_list.viewport())
        overlay.setGeometry(rect)
        # overlay.setAttribute(Qt.WA_TransparentForMouseEvents)  # Let clicks go through
        overlay.show()

        self.main_window.task_interface.editTaskTimeButton.setDisabled(True)
        self.main_window.task_interface.deleteTaskButton.setDisabled(True)
        self.main_window.task_interface.addTaskButton.setDisabled(True)

        # Create teaching tip targeting the first item
        self._select_first_task_step_tip = TargetClickTeachingTip.create(
            target=overlay,
            title="Select this task",
            content="Click on this task to select it",
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            tailPosition=TeachingTipTailPosition.TOP,
            icon=CustomFluentIcon.CLICK,
            parent=self.main_window,
        )
        self._select_first_task_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._select_first_task_step_tip)

    def _invoke_first_task_edit_task_time_step(self):

        self.main_window.task_interface.editTaskTimeButton.setDisabled(False)

        self._invoke_first_task_edit_task_time_step_tip = TargetClickTeachingTip.create(
            target=self.main_window.task_interface.editTaskTimeButton,
            title="Edit the time of the selected task",
            content="",
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            icon=CustomFluentIcon.CLICK,
            tailPosition=TeachingTipTailPosition.TOP,
            parent=self.main_window,
        )
        self._invoke_first_task_edit_task_time_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._invoke_first_task_edit_task_time_step_tip)

    def _edit_first_task_elapsed_time_step(self):
        edit_task_time_dialog = self.main_window.task_interface.window().findChild(EditTaskTimeDialog)

        # User has to change the time, there is no other choice
        edit_task_time_dialog.cancelButton.setDisabled(True)
        edit_task_time_dialog.yesButton.setDisabled(True)

        def on_key_press(event):
            if event.key() in [Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter]:
                event.ignore()
            else:
                super(EditTaskTimeDialog, self).keyPressEvent(event)

        edit_task_time_dialog.keyPressEvent = on_key_press  # disabling enter and escape key so that user cannot
        # close the dialog

        self._edit_first_task_time_elapsed_step_tip = TargetClickTeachingTip.create(
            target=edit_task_time_dialog.elapsedTimePicker,
            title="Try editing the elapsed time of the selected task",
            content="Elapsed time is the time you have already spent on this task",
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            icon=CustomFluentIcon.CLICK,
            tailPosition=TeachingTipTailPosition.LEFT,
            parent=self.main_window,
            customSignalToDestroy=edit_task_time_dialog.elapsedTimePicker.timeChanged,
        )
        self._edit_first_task_time_elapsed_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._edit_first_task_time_elapsed_step_tip)

    def _edit_first_task_estimate_time_step(self):
        edit_task_time_dialog = self.main_window.task_interface.window().findChild(EditTaskTimeDialog)
        self._edit_first_task_time_estimate_step_tip = TargetClickTeachingTip.create(
            target=edit_task_time_dialog.estimateTimePicker,
            title="Now lets edit the estimated time of the selected task",
            content="Esimated time is the time you think you will need to complete this task"
                    "\nThis is an important part of Time Boxing",
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            icon=CustomFluentIcon.CLICK,
            tailPosition=TeachingTipTailPosition.LEFT,
            parent=self.main_window,
            customSignalToDestroy=edit_task_time_dialog.estimateTimePicker.timeChanged,
        )
        self._edit_first_task_time_estimate_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._edit_first_task_time_estimate_step_tip)

    def _edit_first_task_save_changed_time_step(self):
        edit_task_time_dialog = self.main_window.task_interface.window().findChild(EditTaskTimeDialog)

        edit_task_time_dialog.yesButton.setDisabled(False)

        self._edit_first_task_save_changed_time_step_tip = TargetClickTeachingTip.create(
            target=edit_task_time_dialog.yesButton,
            title="Now lets save the changes",
            content="",
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            icon=CustomFluentIcon.CLICK,
            tailPosition=TeachingTipTailPosition.TOP,
            parent=self.main_window,
        )
        self._edit_first_task_save_changed_time_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._edit_first_task_save_changed_time_step_tip)

    def _delete_first_task_step(self):

        self.main_window.task_interface.editTaskTimeButton.setDisabled(True)
        self.main_window.task_interface.deleteTaskButton.setDisabled(False)

        self._delete_first_task_step_tip = TargetClickTeachingTip.create(
            target=self.main_window.task_interface.deleteTaskButton,
            title="Try deleting the selected task",
            content="Don't worry, we will add a new task soon",
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            icon=CustomFluentIcon.CLICK,
            tailPosition=TeachingTipTailPosition.TOP,
            parent=self.main_window,
        )
        self._delete_first_task_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._delete_first_task_step_tip)

    def _invoke_add_new_task_dialog_step(self):

        self.main_window.task_interface.deleteTaskButton.setDisabled(True)
        self.main_window.task_interface.addTaskButton.setDisabled(False)

        self._invoke_add_new_task_dialog_step_tip = TargetClickTeachingTip.create(
            target=self.main_window.task_interface.addTaskButton,
            title="Now lets add a new task",
            content="",
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            icon=CustomFluentIcon.CLICK,
            tailPosition=TeachingTipTailPosition.TOP,
            parent=self.main_window,
        )
        self._invoke_add_new_task_dialog_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._invoke_add_new_task_dialog_step_tip)

    def _name_new_task_step(self):
        add_task_dialog = self.main_window.task_interface.window().findChild(AddTaskDialog)
        add_task_dialog.cancelButton.setDisabled(True)
        add_task_dialog.yesButton.setDisabled(True)

        def on_key_press(event):
            if event.key() in [Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter]:
                event.ignore()
            else:
                super(AddTaskDialog, self).keyPressEvent(event)

        add_task_dialog.keyPressEvent = on_key_press  # disabling enter and escape key so that user cannot
        # close the dialog

        self._name_new_task_step_tip = TargetClickTeachingTip.create(
            target=add_task_dialog.taskEdit,
            title="Enter the name of the new task",
            content="Name it something short and meaningful\n"
                    "Good goals are SMART: Specific, Measurable, Achievable, Relevant, Time-bound",
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            icon=CustomFluentIcon.TEXT_ADD,
            tailPosition=TeachingTipTailPosition.RIGHT,
            parent=self.main_window,
            customSignalToDestroy=add_task_dialog.taskEdit.textEdited
        )
        self._name_new_task_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._name_new_task_step_tip)

    def _save_new_task_step(self):
        todo_task_list = self.main_window.task_interface.todoTasksList

        add_task_dialog = self.main_window.task_interface.window().findChild(AddTaskDialog)

        add_task_dialog.yesButton.setDisabled(False)

        self._save_new_task_step_tip = TargetClickTeachingTip.create(
            target=add_task_dialog.yesButton,
            title="Save the new task",
            content="",
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            icon=CustomFluentIcon.CLICK,
            tailPosition=TeachingTipTailPosition.TOP,
            parent=self.main_window,
            customSignalToDestroy=todo_task_list.model().rowsInserted,
        )
        self._save_new_task_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._save_new_task_step_tip)

    def _start_first_task_step(self):
        self.main_window.task_interface.addTaskButton.setDisabled(True)

        todo_task_list = self.main_window.task_interface.todoTasksList

        if todo_task_list.model().rowCount() > 0:
            last_row = todo_task_list.model().rowCount() - 1
            last_index = todo_task_list.model().index(last_row, 0)
            task_id = todo_task_list.model().data(last_index, TaskListModel.IDRole)

            # Get the delegate to access the buttons dictionary
            delegate = todo_task_list.itemDelegate()

            # Find the button for the first task
            button = delegate.buttons.get(task_id)

            self._start_first_task_step_tip = TargetClickTeachingTip.create(
                target=button,
                title="Start this new task",
                content="Click on it's play button to start the task",
                mainWindow=self.main_window,
                interface_type=InterfaceType.TASK_INTERFACE,
                tailPosition=TeachingTipTailPosition.TOP,  # on wayland it doesn't point at the play button
                # instead points at task name
                icon=CustomFluentIcon.CLICK,
                parent=self.main_window,
            )
            self._start_first_task_step_tip.destroyed.connect(self.next_step)
            self.teaching_tips.append(self._start_first_task_step_tip)
        else:
            # No tasks in list, skip step
            logger.debug("No tasks in todo list, skipping step")
            self.next_step()

    def _move_to_completed_task_list_step(self):
        # Get the completed task list
        todo_task_list = self.main_window.task_interface.todoTasksList
        completed_task_list = self.main_window.task_interface.completedTasksList

        if todo_task_list.model().rowCount() > 0:
            last_row = todo_task_list.model().rowCount() - 1
            last_index = todo_task_list.model().index(last_row, 0)
            rect = todo_task_list.visualRect(last_index)

            overlay = QWidget(todo_task_list.viewport())
            overlay.setGeometry(rect)
            overlay.show()

            self._move_to_completed_task_list_step_tip = TargetClickTeachingTip.create(
                target=overlay,
                title="Drag this task to the completed task list to mark it as completed",
                content="",
                mainWindow=self.main_window,
                interface_type=InterfaceType.TASK_INTERFACE,
                tailPosition=TeachingTipTailPosition.TOP,
                icon=CustomFluentIcon.CLICK,
                parent=self.main_window,
                customSignalToDestroy=completed_task_list.model().modelReset
            )
            self._move_to_completed_task_list_step_tip.destroyed.connect(self.next_step)
            self.teaching_tips.append(self._move_to_completed_task_list_step_tip)
        else:
            # No tasks in list, skip step
            logger.debug("No tasks in todo list, skipping step")
            self.next_step()

    def _stop_timer_step(self):
        # Get the completed task list
        bottom_bar = self.main_window.bottomBar

        if self.main_window.pomodoro_interface.pomodoro_timer_obj.pomodoro_timer.isActive():
            self._stop_timer_step_tip = TargetClickTeachingTip.create(
                target=bottom_bar.stopButton,
                title="Click this button to stop the timer",
                content="",
                mainWindow=self.main_window,
                interface_type=InterfaceType.TASK_INTERFACE,
                tailPosition=TeachingTipTailPosition.BOTTOM,
                icon=CustomFluentIcon.CLICK,
                parent=self.main_window,
            )
            self._stop_timer_step_tip.destroyed.connect(self.next_step)
            self.teaching_tips.append(self._stop_timer_step_tip)
        else:
            self.next_step()

    def _enable_buttons(self):
        self.main_window.task_interface.editTaskTimeButton.setDisabled(False)
        self.main_window.task_interface.deleteTaskButton.setDisabled(False)
        self.main_window.task_interface.addTaskButton.setDisabled(False)

        self.next_step()

    def _last_step(self):
        # this is the last step
        app_settings.set(app_settings.has_completed_task_view_tutorial, True)
        ConfigValues.HAS_COMPLETED_TASK_VIEW_TUTORIAL = True
        self.main_window.isSafeToShowTutorial = True  # allow other tutorials to show

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.BACK_BUTTON, True)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.POMODORO_INTERFACE, True)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.WEBSITE_FILTER_INTERFACE, True)

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.WORKSPACE_MANAGER_DIALOG, True)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.SETTINGS_INTERFACE, True)
