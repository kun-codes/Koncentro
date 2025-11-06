import platform
from functools import wraps
from typing import Any, Callable, Optional, TypeVar

from PySide6.QtCore import QModelIndex, Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QSizePolicy, QVBoxLayout, QWidget
from qfluentwidgets import (
    Action,
    FluentIcon,
    InfoBar,
    RoundMenu,
    SimpleCardWidget,
    TitleLabel,
    ToolTipFilter,
    ToolTipPosition,
)

from constants import InvalidTaskDrop
from models.dbTables import TaskType
from models.taskListModel import TaskListModel, TaskNode
from prefabs.customFluentIcon import CustomFluentIcon
from prefabs.taskList import TaskList
from prefabs.taskListItemDelegate import TaskListItemDelegate
from ui_py.ui_tasks_list_view import Ui_TaskView
from views.dialogs.addSubTaskDialog import AddSubTaskDialog
from views.dialogs.addTaskDialog import AddTaskDialog
from views.dialogs.editTaskTimeDialog import EditTaskTimeDialog

T = TypeVar("T", bound="TaskListView")


def restoreFocus(method: Callable[..., None]) -> Callable[..., None]:
    """
    Focus has to be restored to the TaskListView instance from dialogs which are children of TaskListView after they
    are invoked (as they steal the focus) so that self.editTaskTimeShortcut and other similar shortcuts can be used
    again. These shortcuts have their parent set to TaskListView and their context set to
    Qt.ShortcutContext.WidgetWithChildrenShortcut
    (https://doc.qt.io/qtforpython-6/PySide6/QtCore/Qt.html#PySide6.QtCore.Qt.ShortcutContext)
    Although focus can be restored to the last used taskView since it is a child of TaskListView as well, focus is
    being restored to the TaskListView instance as it is easier and more convenient to do so.
    """

    @wraps(method)
    def wrapper(self: T, *args: Any, **kwargs: Any) -> None:
        result = method(self, *args, **kwargs)
        self.setFocus(Qt.FocusReason.PopupFocusReason)
        return result

    return wrapper


controlKeyText = "Cmd" if platform.system() == "Darwin" else "Ctrl"


class TaskListView(Ui_TaskView, QWidget):
    """
    For tasks view of the app
    """

    subTaskDialogAboutToOpen = Signal()  # emitted right before AddSubTaskDialog is opened

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.lastTriggeredAddTaskMenuAction: Optional[Action] = None  # keeps track of the last action selected from
        # self.addTaskMenu and so that Action in this variable is triggered when self.addTaskSplitButton is clicked
        self.initLayout()
        self.connectSignalsToSlots()
        self.setupSelectionBehavior()
        self.setupShortcuts()

    def setupShortcuts(self) -> None:
        # not setting up shortcuts like the below because the shortcut can get activated when focus is on a dialog
        # like add task dialog etc
        # self.deleteTaskButton.setShortcut(QKeySequence(Qt.Key.Key_Delete))

        self.deleteShortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        self.deleteShortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        # connecting to self.deleteTaskButton.click() as the shortcut will have no effect on activation when the
        # deleteTaskButton is deactivated (that is during tutorials)
        self.deleteShortcut.activated.connect(self.deleteTaskButton.click)

        self.editTaskTimeShortcut = QShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_T), self)
        self.editTaskTimeShortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.editTaskTimeShortcut.activated.connect(self.editTaskTimeButton.click)

        self.addTaskShortcut = QShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_N), self)
        self.addTaskShortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.addTaskShortcut.activated.connect(self.addTaskAction.trigger)

        self.addSubTaskShortcut = QShortcut(
            QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier | Qt.Key.Key_N), self
        )
        self.addSubTaskShortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.addSubTaskShortcut.activated.connect(self.addSubTaskAction.trigger)
        self.addSubTaskShortcut.activated.connect(lambda: print("Add Subtask Shortcut Activated"))

        self.addTaskSplitButton.button.setToolTip(
            f"Add Task ({self.addTaskShortcut.key().toString(QKeySequence.SequenceFormat.NativeText)})"
        )
        self.addTaskSplitButton.button.installEventFilter(
            ToolTipFilter(self.addTaskSplitButton.button, showDelay=300, position=ToolTipPosition.BOTTOM)
        )
        self.addTaskSplitButton.dropButton.setToolTip("More actions")
        self.addTaskSplitButton.dropButton.installEventFilter(
            ToolTipFilter(self.addTaskSplitButton.dropButton, showDelay=300, position=ToolTipPosition.BOTTOM)
        )
        self.deleteTaskButton.setToolTip(
            f"Delete Task ({self.deleteShortcut.key().toString(QKeySequence.SequenceFormat.NativeText)})"
        )
        self.deleteTaskButton.installEventFilter(
            ToolTipFilter(self.deleteTaskButton, showDelay=300, position=ToolTipPosition.BOTTOM)
        )
        self.editTaskTimeButton.setToolTip(
            f"Edit Task Time ({self.editTaskTimeShortcut.key().toString(QKeySequence.SequenceFormat.NativeText)})"
        )
        self.editTaskTimeButton.installEventFilter(
            ToolTipFilter(self.editTaskTimeButton, showDelay=300, position=ToolTipPosition.BOTTOM)
        )

        self.addTaskAction.setToolTip(
            f"Add Task ({self.addTaskShortcut.key().toString(QKeySequence.SequenceFormat.NativeText)})"
        )
        self.addTaskAction.installEventFilter(
            ToolTipFilter(self.addTaskAction, showDelay=300, position=ToolTipPosition.RIGHT)
        )
        self.addSubTaskAction.setToolTip(
            f"Add Subtask ({self.addSubTaskShortcut.key().toString(QKeySequence.SequenceFormat.NativeText)})"
        )
        self.addSubTaskAction.installEventFilter(
            ToolTipFilter(self.addSubTaskAction, showDelay=300, position=ToolTipPosition.RIGHT)
        )

    def initLayout(self) -> None:
        label_size_policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        # card inside which todo tasks list will be kept
        self.todoTasksCard = SimpleCardWidget()
        self.todoTasksCard.setLayout(QVBoxLayout())
        self.scrollAreaWidgetContents.layout().addWidget(self.todoTasksCard)

        self.todoTasksList = TaskList(self.todoTasksCard)
        self.todoTasksList.setModel(TaskListModel(TaskType.TODO))
        self.todoTasksList.setObjectName("todoTasksList")
        self.todoTasksCard.layout().addWidget(self.todoTasksList)

        self.completedTasksLabel = TitleLabel()
        self.completedTasksLabel.setText("Completed Tasks")
        self.completedTasksLabel.setSizePolicy(label_size_policy)
        self.scrollAreaWidgetContents.layout().addWidget(self.completedTasksLabel)

        # card inside which completed tasks list will be kept
        self.completedTasksCard = SimpleCardWidget()
        self.completedTasksCard.setLayout(QVBoxLayout())
        self.scrollAreaWidgetContents.layout().addWidget(self.completedTasksCard)

        self.completedTasksList = TaskList(self.completedTasksCard)
        self.completedTasksList.setModel(TaskListModel(TaskType.COMPLETED))
        self.completedTasksList.setObjectName("completedTasksList")
        self.completedTasksCard.layout().addWidget(self.completedTasksList)

        self.addTaskMenu = RoundMenu(parent=self)
        self.addTaskAction = Action(icon=FluentIcon.ADD, text="Add Task")
        self.addSubTaskAction = Action(icon=CustomFluentIcon.ADD_SUBTASK, text="Add Subtask")

        self.addTaskMenu.addActions(
            [
                self.addTaskAction,
                self.addSubTaskAction,
            ]
        )

        # set icons of buttons
        self.addTaskSplitButton.setIcon(FluentIcon.ADD)
        self.deleteTaskButton.setIcon(FluentIcon.DELETE)
        self.editTaskTimeButton.setIcon(FluentIcon.EDIT)

        self.addTaskSplitButton.setFlyout(self.addTaskMenu)
        self.lastTriggeredAddTaskMenuAction = self.addTaskAction

    def connectSignalsToSlots(self) -> None:
        self.addTaskSplitButton.clicked.connect(self.addTaskSplitButtonClicked)
        self.deleteTaskButton.clicked.connect(self.deleteTask)
        self.editTaskTimeButton.clicked.connect(self.editTaskTime)

        self.todoTasksList.model().invalidTaskDropSignal.connect(self.onInvalidDrop)
        self.completedTasksList.model().invalidTaskDropSignal.connect(self.onInvalidDrop)

        todoTasksListItemDelegate: TaskListItemDelegate = self.todoTasksList.itemDelegate()
        todoTasksListItemDelegate.parentTaskWithChildrenStartDeniedSignal.connect(self.showParentTaskStartDeniedInfoBar)

        self.addTaskAction.triggered.connect(self.addTask)
        self.addSubTaskAction.triggered.connect(self.addSubTask)

    def addTaskSplitButtonClicked(self) -> None:
        self.lastTriggeredAddTaskMenuAction.trigger()

    @restoreFocus
    def addTask(self) -> None:
        self.addTaskSplitButton.setIcon(FluentIcon.ADD)
        self.addTaskSplitButton.button.setToolTip(
            f"Add Task ({self.addTaskShortcut.key().toString(QKeySequence.SequenceFormat.NativeText)})"
        )
        self.lastTriggeredAddTaskMenuAction = self.addTaskAction

        self.addTaskDialog = AddTaskDialog(self.window())
        # if user clicks on add task inside dialog
        if self.addTaskDialog.exec():
            task_name = self.addTaskDialog.taskEdit.text()
            row = self.todoTasksList.model().rowCount(QModelIndex())
            self.todoTasksList.model().insertRow(row, QModelIndex(), task_name=task_name, task_type=TaskType.TODO)

    @restoreFocus
    def addSubTask(self) -> None:
        self.addTaskSplitButton.setIcon(CustomFluentIcon.ADD_SUBTASK)
        self.addTaskSplitButton.button.setToolTip(
            f"Add Subtask ({self.addSubTaskShortcut.key().toString(QKeySequence.SequenceFormat.NativeText)})"
        )
        self.lastTriggeredAddTaskMenuAction = self.addSubTaskAction

        self.addSubTaskDialog = AddSubTaskDialog(self.window())
        self.subTaskDialogAboutToOpen.emit()

        selectedRootTask: bool = False
        isFirstSubTask: bool = False

        # check if a parent task is selected
        if self.todoTasksList.selectionModel().hasSelection():
            selectedTaskIndex = self.todoTasksList.selectionModel().currentIndex()
            selectedTaskID = selectedTaskIndex.data(TaskListModel.IDRole)
            selectedTaskNode: TaskNode = self.todoTasksList.model().getTaskNodeById(selectedTaskID)

            if selectedTaskNode.is_root():
                selectedRootTask = True
        else:
            InfoBar.warning(
                "No Task Selected",
                "Select a parent task (or one of its subtasks) to add a new subtask to it.",
                orient=Qt.Orientation.Vertical,
                duration=3000,
                parent=self,
            )
            return

        model: TaskListModel = self.todoTasksList.model()

        if self.addSubTaskDialog.exec():
            subtaskName = self.addSubTaskDialog.taskEdit.text()

            if selectedRootTask:
                row = self.todoTasksList.model().rowCount(selectedTaskIndex)
                # selected task is a parent(root) task
                parentTaskIndex: QModelIndex = selectedTaskIndex
                parentTaskNode: TaskNode = selectedTaskNode
            else:
                parentTaskIndex: QModelIndex = selectedTaskIndex.parent()
                parentTaskNode: TaskNode = parentTaskIndex.internalPointer()
                row = self.todoTasksList.model().rowCount(parentTaskIndex)

            if len(parentTaskNode.children) == 0:
                isFirstSubTask = True

            model.insertRow(
                row,
                parentTaskIndex,
                task_name=subtaskName,
                task_type=TaskType.TODO,
            )

            # if this is the first subtask of the parent task then make time of child task = time of parent task
            if isFirstSubTask:
                childTaskNode: TaskNode = parentTaskNode.children[0]
                childTaskNode.elapsed_time = parentTaskNode.elapsed_time
                childTaskNode.target_time = parentTaskNode.target_time

            # set time of parent task as sum of all its subtask
            parentTaskNode.elapsed_time = 0
            parentTaskNode.target_time = 0
            for childTask in parentTaskNode.children:
                parentTaskNode.elapsed_time += childTask.elapsed_time
                parentTaskNode.target_time += childTask.target_time

            self.todoTasksList.model().update_db()

    def onInvalidDrop(self, dropType: InvalidTaskDrop) -> None:
        if dropType == InvalidTaskDrop.DROPPED_PARENT_TASK_AT_CHILD_LEVEL:
            InfoBar.warning(
                "Invalid Drop",
                "You cannot transform a task to a subtask.",
                orient=Qt.Orientation.Vertical,
                duration=3000,
                parent=self,
            )
        elif dropType == InvalidTaskDrop.DROPPED_CHILD_TASK_AT_ROOT_LEVEL:
            InfoBar.warning(
                "Invalid Drop",
                "You cannot transform a subtask to a task.",
                orient=Qt.Orientation.Vertical,
                duration=3000,
                parent=self,
            )
        elif dropType == InvalidTaskDrop.DROPPED_CHILD_TASK_IN_ANOTHER_PARENT_TASK:
            InfoBar.warning(
                "Invalid Drop",
                "You cannot change a subtask's parent task.",
                orient=Qt.Orientation.Vertical,
                duration=3000,
                parent=self,
            )

    def deleteTask(self) -> None:
        # one task would be selected from one of these task lists
        if self.todoTasksList.selectionModel().hasSelection():
            list: TaskList = self.todoTasksList
        elif self.completedTasksList.selectionModel().hasSelection():
            list: TaskList = self.completedTasksList
        else:
            InfoBar.warning(
                "No Task Selected",
                "Select a task to delete it.",
                orient=Qt.Orientation.Vertical,
                duration=3000,
                parent=self,
            )
            return

        model: TaskListModel = list.model()
        selectedIndex: QModelIndex = list.selectionModel().currentIndex()
        parent_index = model.parent(selectedIndex)

        model.deleteTask(selectedIndex.row(), parent_index)

    @restoreFocus
    def editTaskTime(self) -> None:
        row = None
        task_list_model = None
        if self.todoTasksList.selectionModel().hasSelection():
            row = self.todoTasksList.selectionModel().currentIndex()
            task_list_model: TaskListModel = self.todoTasksList.model()
        elif self.completedTasksList.selectionModel().hasSelection():
            row = self.completedTasksList.selectionModel().currentIndex()
            task_list_model: TaskListModel = self.completedTasksList.model()

        if row is None:
            InfoBar.warning(
                "No Task Selected",
                "Select a task to edit its time.",
                orient=Qt.Orientation.Vertical,
                duration=3000,
                parent=self,
            )
            return

        task_id = row.data(TaskListModel.IDRole)
        self.editTaskTimeDialog = EditTaskTimeDialog(self.window(), task_id)

        taskIndex: QModelIndex = task_list_model.getIndexByTaskId(task_id)
        isChildTask: bool = taskIndex.parent().isValid()
        taskNode: TaskNode = task_list_model.get_node(taskIndex)

        # if is a parent task and has child tasks
        if not isChildTask and len(taskNode.children) > 0:
            InfoBar.warning(
                "Cannot Edit Time for Parent Task",
                "You cannot edit time for a parent task. Edit time for its subtasks instead.",
                orient=Qt.Orientation.Vertical,
                duration=3000,
                parent=self,
            )
            return

        if self.editTaskTimeDialog.exec():
            if isChildTask:
                childElapsedTime = self.editTaskTimeDialog.getElapsedTime()
                childEstimatedTime = self.editTaskTimeDialog.getTargetTime()

                parentTaskIndex = task_list_model.parent(row)
                parentTaskNode = task_list_model.get_node(parentTaskIndex)
                children = parentTaskNode.children

                parentElapsedTime = 0
                parentEstimatedTime = 0
                for child in children:
                    if child.task_id != task_id:
                        parentElapsedTime += child.elapsed_time
                        parentEstimatedTime += child.target_time
                    else:
                        if childElapsedTime is not None:
                            parentElapsedTime += childElapsedTime
                        else:
                            parentElapsedTime += child.elapsed_time

                        if childEstimatedTime is not None:
                            parentEstimatedTime += childEstimatedTime
                        else:
                            parentEstimatedTime += child.target_time

                if childElapsedTime is not None:
                    task_list_model.setData(row, childElapsedTime, TaskListModel.ElapsedTimeRole, update_db=True)
                    task_list_model.setData(
                        parentTaskIndex, parentElapsedTime, TaskListModel.ElapsedTimeRole, update_db=True
                    )

                if childEstimatedTime is not None:
                    task_list_model.setData(row, childEstimatedTime, TaskListModel.TargetTimeRole, update_db=True)
                    task_list_model.setData(
                        parentTaskIndex, parentEstimatedTime, TaskListModel.TargetTimeRole, update_db=True
                    )

            else:
                elapsed_time = self.editTaskTimeDialog.getElapsedTime()
                if elapsed_time is not None:
                    task_list_model.setData(row, elapsed_time, TaskListModel.ElapsedTimeRole, update_db=True)
                estimated_time = self.editTaskTimeDialog.getTargetTime()
                if estimated_time is not None:
                    task_list_model.setData(row, estimated_time, TaskListModel.TargetTimeRole, update_db=True)

    def setupSelectionBehavior(self) -> None:
        """
        To ensure that only one item is selected out of both the lists
        """
        self.todoTasksList.selectionModel().selectionChanged.connect(self.onTodoTasksSelectionChanged)
        self.completedTasksList.selectionModel().selectionChanged.connect(self.onCompletedTasksSelectionChanged)

    def showParentTaskStartDeniedInfoBar(self, _taskID: int) -> None:
        InfoBar.warning(
            "Task Start Denied",
            "You cannot start a task with subtasks. Start one of its subtasks instead.",
            orient=Qt.Orientation.Vertical,
            duration=3000,
            parent=self,
        )

    def onTodoTasksSelectionChanged(self) -> None:
        if self.todoTasksList.selectionModel().hasSelection():
            # disconnecting and connecting again so that the other SelectionChanged method is not called
            # when selection is cleared
            self.completedTasksList.selectionModel().selectionChanged.disconnect(self.onCompletedTasksSelectionChanged)
            self.completedTasksList.clearSelection()
            self.completedTasksList.selectionModel().selectionChanged.connect(self.onCompletedTasksSelectionChanged)

    def onCompletedTasksSelectionChanged(self) -> None:
        if self.completedTasksList.selectionModel().hasSelection():
            # disconnecting and connecting again so that the other SelectionChanged method is not called
            # when selection is cleared
            self.todoTasksList.selectionModel().selectionChanged.disconnect(self.onTodoTasksSelectionChanged)
            self.todoTasksList.clearSelection()
            self.todoTasksList.selectionModel().selectionChanged.connect(self.onTodoTasksSelectionChanged)

    def onCurrentWorkspaceChanged(self) -> None:
        self.todoTasksList.model().load_data()
        self.completedTasksList.model().load_data()

        self.todoTasksList._restoreExpansionStateOfAllTasks()
        self.completedTasksList._restoreExpansionStateOfAllTasks()

    def autoSetCurrentTaskID(self) -> None:
        model: TaskListModel = self.todoTasksList.model()

        if model.currentTaskID() is not None:  # if current task is already set then return
            return
        # else set current task according to below rules
        if self.todoTasksList.selectionModel().hasSelection():
            selectedIndex: QModelIndex = self.todoTasksList.selectionModel().currentIndex()
            selectedNode: TaskNode = selectedIndex.internalPointer()

            # if selected index is a parent task and has child tasks
            if not selectedIndex.parent().isValid() and len(selectedNode.children) > 0:
                # set current task as first child of selected parent task
                firstChildIndex = self.todoTasksList.model().index(0, 0, selectedIndex)
                model.setCurrentTaskID(firstChildIndex.data(TaskListModel.IDRole))
            else:  # set current task as selected task
                model.setCurrentTaskID(selectedIndex.data(TaskListModel.IDRole))
        elif self.todoTasksList.model().rowCount(QModelIndex()) > 0:
            firstIndex: QModelIndex = model.index(0, 0)
            firstNode: TaskNode = firstIndex.internalPointer()

            if not firstIndex.parent().isValid() and len(firstNode.children) > 0:
                # set current task as first child of first parent task
                firstChildIndex = self.todoTasksList.model().index(0, 0, firstIndex)
                model.setCurrentTaskID(firstChildIndex.data(TaskListModel.IDRole))
            else:  # set current task as first task
                model.setCurrentTaskID(firstIndex.data(TaskListModel.IDRole))
        else:
            self.todoTasksList.model().setCurrentTaskID(None)

        self.todoTasksList.viewport().update()
