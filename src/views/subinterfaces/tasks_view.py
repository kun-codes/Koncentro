from typing import Optional

from loguru import logger
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QApplication, QSizePolicy, QVBoxLayout, QWidget
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
from models.db_tables import TaskType
from models.task_list_model import TaskListModel, TaskNode
from prefabs.customFluentIcon import CustomFluentIcon
from prefabs.taskList import TaskList
from prefabs.taskListItemDelegate import TaskListItemDelegate
from ui_py.ui_tasks_list_view import Ui_TaskView
from views.dialogs.addSubTaskDialog import AddSubTaskDialog
from views.dialogs.addTaskDialog import AddTaskDialog
from views.dialogs.editTaskTimeDialog import EditTaskTimeDialog


class TaskListView(Ui_TaskView, QWidget):
    """
    For tasks view of the app
    """

    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)
        self.lastTriggeredAddTaskMenuAction: Optional[Action] = None  # keeps track of the last action selected from
        # self.addTaskMenu and so that Action in this variable is triggered when self.addTaskSplitButton is clicked
        self.initLayout()
        self.connectSignalsToSlots()
        self.setupSelectionBehavior()

    def initLayout(self) -> None:
        label_size_policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.todoTasksLabel = TitleLabel()
        self.todoTasksLabel.setText("To Do Tasks")
        self.todoTasksLabel.setSizePolicy(label_size_policy)
        self.scrollAreaWidgetContents.layout().addWidget(self.todoTasksLabel)

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
        self.addTaskAction = Action(text="Add Task")
        self.addSubTaskAction = Action(text="Add Subtask")
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

        self.addTaskSplitButton.setToolTip("Add Task")
        self.addTaskSplitButton.installEventFilter(
            ToolTipFilter(self.addTaskSplitButton, showDelay=300, position=ToolTipPosition.BOTTOM)
        )
        self.deleteTaskButton.setToolTip("Delete Task")
        self.deleteTaskButton.installEventFilter(
            ToolTipFilter(self.deleteTaskButton, showDelay=300, position=ToolTipPosition.BOTTOM)
        )
        self.editTaskTimeButton.setToolTip("Edit Task Time")
        self.editTaskTimeButton.installEventFilter(
            ToolTipFilter(self.editTaskTimeButton, showDelay=300, position=ToolTipPosition.BOTTOM)
        )

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

    def addTask(self) -> None:
        self.addTaskSplitButton.setIcon(FluentIcon.ADD)
        self.lastTriggeredAddTaskMenuAction = self.addTaskAction

        self.addTaskDialog = AddTaskDialog(self.window())
        # if user clicks on add task inside dialog
        if self.addTaskDialog.exec():
            task_name = self.addTaskDialog.taskEdit.text()
            row = self.todoTasksList.model().rowCount(QModelIndex())
            self.todoTasksList.model().insertRow(row, QModelIndex(), task_name=task_name, task_type=TaskType.TODO)

    def addSubTask(self) -> None:
        self.addTaskSplitButton.setIcon(CustomFluentIcon.ADD_SUBTASK)
        self.lastTriggeredAddTaskMenuAction = self.addSubTaskAction

        self.addSubTaskDialog = AddSubTaskDialog(self.window())

        selectedRootTask: bool = False

        # check if a parent task is selected
        if self.todoTasksList.selectionModel().hasSelection():
            selectedTaskIndex = self.todoTasksList.selectionModel().currentIndex()
            selectedTaskID = selectedTaskIndex.data(TaskListModel.IDRole)
            selectedTaskNode: TaskNode = self.todoTasksList.model().getTaskNodeById(selectedTaskID)

            if selectedTaskNode.is_root():
                selectedRootTask = True
        else:
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

            model.insertRow(
                row,
                parentTaskIndex,
                task_name=subtaskName,
                task_type=TaskType.TODO,
            )

            # set time of parent task as sum of all its subtask
            for childTask in parentTaskNode.children:
                parentTaskNode.elapsed_time += childTask.elapsed_time
                parentTaskNode.target_time += childTask.target_time

            self.todoTasksList.model().update_db()

    def findMainWindow(self):
        widget = self.parent()
        while widget:
            if widget.objectName() == "main_window":
                logger.debug("Found main window.")
                return widget
            widget = widget.parent()

        return None

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
            return

        model: TaskListModel = list.model()
        selectedIndex: QModelIndex = list.selectionModel().currentIndex()
        parent_index = model.parent(selectedIndex)

        model.deleteTask(selectedIndex.row(), parent_index)

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


if __name__ == "__main__":
    app = QApplication()
    w = TaskListView()
    w.show()
    app.exec()
