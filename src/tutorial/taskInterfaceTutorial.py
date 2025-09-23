from typing import Optional

from loguru import logger
from PySide6.QtCore import QModelIndex, QRect, Qt, QTimer
from PySide6.QtWidgets import QStyleOptionViewItem, QWidget
from qfluentwidgets import FluentIcon, FluentWindow, TeachingTipTailPosition

from config_values import ConfigValues
from constants import InterfaceType, NavPanelButtonPosition
from models.config import app_settings
from models.task_list_model import TaskListModel
from prefabs.customFluentIcon import CustomFluentIcon
from prefabs.targetClickTeachingTip import TargetClickTeachingTip
from prefabs.taskList import TaskList
from prefabs.transientPopupTeachingTip import TransientPopupTeachingTip
from tutorial.interfaceTutorial import InterfaceTutorial
from utils.setNavButtonEnabled import setNavButtonEnabled
from views.dialogs.addSubTaskDialog import AddSubTaskDialog
from views.dialogs.addTaskDialog import AddTaskDialog
from views.dialogs.editTaskTimeDialog import EditTaskTimeDialog


class TaskInterfaceTutorial(InterfaceTutorial):
    def __init__(self, main_window: FluentWindow, interface_type: InterfaceType) -> None:
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
        self.tutorial_steps.append(self._select_new_task_step_pre_requisite)
        self.tutorial_steps.append(self._select_new_task_step)
        self.tutorial_steps.append(self._invoke_add_new_subtask_dialog_step_part_1)
        self.tutorial_steps.append(self._name_new_subtask_step)
        self.tutorial_steps.append(self._save_new_subtask_step)
        self.tutorial_steps.append(self._start_first_task_step_pre_requisite)
        self.tutorial_steps.append(self._start_first_task_step)
        self.tutorial_steps.append(self._move_to_completed_task_list_step)
        self.tutorial_steps.append(self._stop_timer_step)
        self.tutorial_steps.append(self._enable_buttons)
        self.tutorial_steps.append(self._last_step)

        self.overlay: Optional[QWidget] = None

    def _first_step(self) -> None:
        self.main_window.isSafeToShowTutorial = False  # block tutorials of other interfaces from showing

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.BACK_BUTTON, False)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.POMODORO_INTERFACE, False)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.WEBSITE_BLOCKER_INTERFACE, False)

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.WORKSPACE_MANAGER_DIALOG, False)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.SETTINGS_INTERFACE, False)

        self.next_step()

    def _todo_task_list_step(self) -> None:
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
            isDeleteOnClose=True,
        )
        self._todo_task_list_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._todo_task_list_step_tip)

    def _completed_task_list_step(self) -> None:
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
            isDeleteOnClose=True,
        )
        self._completed_task_list_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._completed_task_list_step_tip)

    def _select_first_task_step(self) -> None:
        # Get the todo task list
        todoTaskList = self.main_window.task_interface.todoTasksList
        todoTaskListModel: TaskListModel = todoTaskList.model()
        firstParentTask = todoTaskListModel.index(0, 0)
        firstChildTask = todoTaskListModel.index(0, 0, firstParentTask)

        # check if firstParentTask has a child task
        targetTask: QModelIndex = firstChildTask
        if not firstChildTask.isValid():
            targetTask = firstParentTask

        rect = todoTaskList.visualRect(targetTask)

        self.overlay = QWidget(todoTaskList.viewport())
        self.overlay.setGeometry(rect)
        self.overlay.show()

        self.main_window.task_interface.editTaskTimeButton.setDisabled(True)
        self.main_window.task_interface.deleteTaskButton.setDisabled(True)
        self.main_window.task_interface.addTaskSplitButton.setDisabled(True)

        # Create teaching tip targeting the first item
        self._select_first_task_step_tip = TargetClickTeachingTip.create(
            target=self.overlay,
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

    def _invoke_first_task_edit_task_time_step(self) -> None:
        self.overlay.hide()
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

    def _edit_first_task_elapsed_time_step(self) -> None:
        if not hasattr(self.main_window.task_interface, "editTaskTimeDialog"):
            logger.debug("EditTaskTimeDialog not found, retrying in 100ms")
            QTimer.singleShot(100, self._edit_first_task_elapsed_time_step)
            return

        edit_task_time_dialog: EditTaskTimeDialog = self.main_window.task_interface.editTaskTimeDialog
        logger.debug("Found EditTaskTimeDialog")

        # User has to change the time, there is no other choice
        edit_task_time_dialog.cancelButton.setDisabled(True)
        edit_task_time_dialog.yesButton.setDisabled(True)

        def on_key_press(event) -> None:
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

    def _edit_first_task_estimate_time_step(self) -> None:
        if not hasattr(self.main_window.task_interface, "editTaskTimeDialog"):
            logger.debug("EditTaskTimeDialog not found, retrying in 100ms")
            QTimer.singleShot(100, self._edit_first_task_elapsed_time_step)
            return

        edit_task_time_dialog: EditTaskTimeDialog = self.main_window.task_interface.editTaskTimeDialog
        logger.debug("Found EditTaskTimeDialog")

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

    def _edit_first_task_save_changed_time_step(self) -> None:
        if not hasattr(self.main_window.task_interface, "editTaskTimeDialog"):
            logger.debug("EditTaskTimeDialog not found, retrying in 100ms")
            QTimer.singleShot(100, self._edit_first_task_elapsed_time_step)
            return

        edit_task_time_dialog: EditTaskTimeDialog = self.main_window.task_interface.editTaskTimeDialog
        logger.debug("Found EditTaskTimeDialog")

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

    def _delete_first_task_step(self) -> None:
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

    def _invoke_add_new_task_dialog_step(self) -> None:
        self.main_window.task_interface.deleteTaskButton.setDisabled(True)
        self.main_window.task_interface.addTaskSplitButton.setDisabled(False)

        self._invoke_add_new_task_dialog_step_tip = TargetClickTeachingTip.create(
            target=self.main_window.task_interface.addTaskSplitButton.button,
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

    def _name_new_task_step(self) -> None:
        if not hasattr(self.main_window.task_interface, "addTaskDialog"):
            logger.debug("AddTaskDialog not found, retrying in 100ms")
            QTimer.singleShot(100, self._invoke_add_new_task_dialog_step)
            return

        add_task_dialog: AddTaskDialog = self.main_window.task_interface.addTaskDialog
        logger.debug("Found AddTaskDialog")

        add_task_dialog.cancelButton.setDisabled(True)
        add_task_dialog.yesButton.setDisabled(True)

        def on_key_press(event) -> None:
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
            tailPosition=TeachingTipTailPosition.TOP,
            parent=self.main_window,
            customSignalToDestroy=add_task_dialog.taskEdit.textEdited,
        )
        self._name_new_task_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._name_new_task_step_tip)

    def _save_new_task_step(self) -> None:
        todo_task_list = self.main_window.task_interface.todoTasksList

        if not hasattr(self.main_window.task_interface, "addTaskDialog"):
            logger.debug("AddTaskDialog not found, retrying in 100ms")
            QTimer.singleShot(100, self._invoke_add_new_task_dialog_step)
            return

        add_task_dialog: AddTaskDialog = self.main_window.task_interface.addTaskDialog
        logger.debug("Found AddTaskDialog")

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

    def _select_new_task_step_pre_requisite(self) -> None:
        self._scroll_todo_task_list_to_bottom()

        QTimer.singleShot(1000, self.next_step)  # wait for 1 second for scroll animation to complete before
        # going to next step

    def _select_new_task_step(self) -> None:
        todoTaskList: TaskList = self.main_window.task_interface.todoTasksList

        self._scroll_todo_task_list_to_bottom()

        todoTaskListModel: TaskListModel = todoTaskList.model()
        lastParentIndex: QModelIndex = todoTaskListModel.index(todoTaskListModel.rowCount() - 1, 0)
        lastParentIndexRect: QRect = todoTaskList.visualRect(lastParentIndex)

        self.overlay = QWidget(todoTaskList.viewport())
        self.overlay.setGeometry(lastParentIndexRect)
        self.overlay.show()

        self._select_new_task_step_tip = TargetClickTeachingTip.create(
            target=self.overlay,
            title="Select the new task. We will add a new subtask to it",
            content="",
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            icon=CustomFluentIcon.CLICK,
            tailPosition=TeachingTipTailPosition.TOP,
            parent=self.main_window,
            customSignalToDestroy=todoTaskList.selectionModel().selectionChanged,
        )
        self._select_new_task_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._select_new_task_step_tip)

    def _invoke_add_new_subtask_dialog_step_part_1(self) -> None:
        self.overlay.hide()

        self.main_window.task_interface.deleteTaskButton.setDisabled(True)
        self.main_window.task_interface.addTaskSplitButton.setDisabled(False)
        self.main_window.task_interface.addTaskSplitButton.button.setDisabled(True)
        self.main_window.task_interface.editTaskTimeButton.setDisabled(True)

        self.main_window.task_interface.addTaskAction.setEnabled(False)

        self._invoke_add_new_subtask_dialog_step_part_1_tip = TargetClickTeachingTip.create(
            target=self.main_window.task_interface.addTaskSplitButton.dropButton,
            title="Click on this dropdown button and then click on the add subtask button to add a new subtask",
            content="",
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            icon=CustomFluentIcon.CLICK,
            tailPosition=TeachingTipTailPosition.TOP,
            parent=self.main_window,
            customSignalToDestroy=self.main_window.task_interface.subTaskDialogAboutToOpen,
        )
        self._invoke_add_new_subtask_dialog_step_part_1_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._invoke_add_new_subtask_dialog_step_part_1_tip)

    def _name_new_subtask_step(self) -> None:
        self.main_window.task_interface.addTaskAction.setEnabled(True)

        if not hasattr(self.main_window.task_interface, "addSubTaskDialog"):
            logger.debug("AddSubTaskDialog not found, retrying in 100ms")
            QTimer.singleShot(100, self._name_new_subtask_step)
            return

        addSubTaskDialog: AddSubTaskDialog = self.main_window.task_interface.addSubTaskDialog
        logger.debug("Found AddSubTaskDialog")

        addSubTaskDialog.cancelButton.setDisabled(True)
        addSubTaskDialog.yesButton.setDisabled(True)

        def on_key_press(event) -> None:
            if event.key() in [Qt.Key_Escape, Qt.Key_Return, Qt.Key_Enter]:
                event.ignore()
            else:
                super(AddTaskDialog, self).keyPressEvent(event)

        addSubTaskDialog.keyPressEvent = on_key_press  # disabling enter and escape key so that user cannot
        # close the dialog

        self._name_new_subtask_step_tip = TargetClickTeachingTip.create(
            target=addSubTaskDialog.taskEdit,
            title="Enter the name of the new subtask",
            content="",
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            icon=CustomFluentIcon.TEXT_ADD,
            tailPosition=TeachingTipTailPosition.TOP,
            parent=self.main_window,
            customSignalToDestroy=addSubTaskDialog.taskEdit.textEdited,
        )
        self._name_new_subtask_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._name_new_subtask_step_tip)

    def _save_new_subtask_step(self) -> None:
        if not hasattr(self.main_window.task_interface, "addSubTaskDialog"):
            logger.debug("AddSubTaskDialog not found, retrying in 100ms")
            QTimer.singleShot(100, self._invoke_add_new_subtask_dialog_step_part_2)
            return
        addSubTaskDialog: AddSubTaskDialog = self.main_window.task_interface.addSubTaskDialog
        logger.debug("Found AddSubTaskDialog")

        addSubTaskDialog.yesButton.setDisabled(False)

        self._save_new_subtask_step_tip = TargetClickTeachingTip.create(
            target=addSubTaskDialog.yesButton,
            title="Save the new subtask",
            content="",
            mainWindow=self.main_window,
            interface_type=InterfaceType.TASK_INTERFACE,
            icon=CustomFluentIcon.CLICK,
            tailPosition=TeachingTipTailPosition.TOP,
            parent=self.main_window,
            customSignalToDestroy=self.main_window.task_interface.todoTasksList.model().rowsInserted,
        )
        self._save_new_subtask_step_tip.destroyed.connect(self.next_step)
        self.teaching_tips.append(self._save_new_subtask_step_tip)

    def _start_first_task_step_pre_requisite(self) -> None:
        # scroll todoTaskList to the bottom to show child task of last parent task
        self._scroll_todo_task_list_to_bottom()

        QTimer.singleShot(1000, self.next_step)

    def _start_first_task_step(self) -> None:
        self.main_window.task_interface.addTaskSplitButton.setDisabled(True)

        todoTaskList: TaskList = self.main_window.task_interface.todoTasksList
        todoTaskListModel: TaskListModel = todoTaskList.model()

        if todoTaskList.model().rowCount() > 0:
            lastParentRow = todoTaskListModel.rowCount() - 1
            lastParentIndex = todoTaskListModel.index(lastParentRow, 0)
            firstChildOfLastParentIndex = todoTaskListModel.index(0, 0, lastParentIndex)
            firstChildOfLastParentTaskID = todoTaskListModel.data(firstChildOfLastParentIndex, todoTaskListModel.IDRole)

            item_rect = todoTaskList.visualRect(firstChildOfLastParentIndex)

            delegate = todoTaskList.itemDelegate()
            option = QStyleOptionViewItem()
            option.rect = item_rect
            button_rect = delegate._getButtonRect(option)

            overlay = QWidget(todoTaskList.viewport())
            overlay.setGeometry(button_rect)
            overlay.show()

            self._start_first_task_step_tip = TargetClickTeachingTip.create(
                overlay,  # target
                "Start this new subtask",  # title
                "Click on it's play button to start the subtask",  # content
                self.main_window,  # mainWindow
                InterfaceType.TASK_INTERFACE,  # interface_type
                CustomFluentIcon.CLICK,  # icon
                None,  # image
                TeachingTipTailPosition.TOP,  # tailPosition
                self.main_window,  # parent
                todoTaskList.itemDelegate().pauseResumeButtonClicked,  # customSignalToDestroy
                firstChildOfLastParentTaskID,  # task_id and True are Expected signal parameters
                True,  # True because button should be checked
            )
            self._start_first_task_step_tip.destroyed.connect(self.next_step)
            self.teaching_tips.append(self._start_first_task_step_tip)
        else:
            # No tasks in list, skip step
            logger.debug("No tasks in todo list, skipping step")
            self.next_step()

    def _move_to_completed_task_list_step(self) -> None:
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
                title="Drag its parent task to the completed task list to mark it as completed",
                content="",
                mainWindow=self.main_window,
                interface_type=InterfaceType.TASK_INTERFACE,
                tailPosition=TeachingTipTailPosition.TOP,
                icon=CustomFluentIcon.CLICK,
                parent=self.main_window,
                customSignalToDestroy=completed_task_list.model().rowsInserted,
            )
            self._move_to_completed_task_list_step_tip.destroyed.connect(self.next_step)
            self.teaching_tips.append(self._move_to_completed_task_list_step_tip)
        else:
            # No tasks in list, skip step
            logger.debug("No tasks in todo list, skipping step")
            self.next_step()

    def _stop_timer_step(self) -> None:
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

    def _enable_buttons(self) -> None:
        self.main_window.task_interface.editTaskTimeButton.setDisabled(False)
        self.main_window.task_interface.deleteTaskButton.setDisabled(False)
        self.main_window.task_interface.addTaskSplitButton.setDisabled(False)
        self.main_window.task_interface.addTaskSplitButton.button.setDisabled(False)
        self.main_window.task_interface.addTaskSplitButton.dropButton.setDisabled(False)

        self.main_window.task_interface.addTaskAction.setEnabled(True)

        self.next_step()

    def _last_step(self) -> None:
        # this is the last step
        app_settings.set(app_settings.has_completed_task_view_tutorial, True)
        ConfigValues.HAS_COMPLETED_TASK_VIEW_TUTORIAL = True
        self.main_window.isSafeToShowTutorial = True  # allow other tutorials to show

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.BACK_BUTTON, True)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.POMODORO_INTERFACE, True)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.WEBSITE_BLOCKER_INTERFACE, True)

        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.WORKSPACE_MANAGER_DIALOG, True)
        setNavButtonEnabled(self.main_window, NavPanelButtonPosition.SETTINGS_INTERFACE, True)

    def _scroll_todo_task_list_to_bottom(self) -> None:
        todo_task_list = self.main_window.task_interface.todoTasksList
        todo_task_list.scrollDelagate.vScrollBar.scrollTo(todo_task_list.scrollDelagate.vScrollBar.maximum())
