from loguru import logger
from PySide6.QtCore import QModelIndex
from PySide6.QtWidgets import QApplication, QSizePolicy, QVBoxLayout, QWidget
from qfluentwidgets import (
    FluentIcon,
    SimpleCardWidget,
    TitleLabel,
    ToolTipFilter,
    ToolTipPosition,
)

from models.db_tables import TaskType
from models.task_list_model import TaskListModel
from prefabs.taskList import TaskList
from ui_py.ui_tasks_list_view import Ui_TaskView
from views.dialogs.addTaskDialog import AddTaskDialog
from views.dialogs.editTaskTimeDialog import EditTaskTimeDialog


class TaskListView(Ui_TaskView, QWidget):
    """
    For tasks view of the app
    """

    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.initLayout()
        self.connectSignalsToSlots()
        self.setupSelectionBehavior()

    def initLayout(self):
        label_size_policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.todoTasksLabel = TitleLabel()
        self.todoTasksLabel.setText("Todo Tasks")
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

        # set icons of buttons
        self.addTaskButton.setIcon(FluentIcon.ADD)
        self.deleteTaskButton.setIcon(FluentIcon.DELETE)
        self.editTaskTimeButton.setIcon(FluentIcon.EDIT)

        self.addTaskButton.setToolTip("Add Task")
        self.addTaskButton.installEventFilter(
            ToolTipFilter(self.addTaskButton, showDelay=300, position=ToolTipPosition.BOTTOM)
        )
        self.deleteTaskButton.setToolTip("Delete Task")
        self.deleteTaskButton.installEventFilter(
            ToolTipFilter(self.deleteTaskButton, showDelay=300, position=ToolTipPosition.BOTTOM)
        )
        self.editTaskTimeButton.setToolTip("Edit Task Time")
        self.editTaskTimeButton.installEventFilter(
            ToolTipFilter(self.editTaskTimeButton, showDelay=300, position=ToolTipPosition.BOTTOM)
        )

    def connectSignalsToSlots(self):
        self.addTaskButton.clicked.connect(self.addTask)
        self.deleteTaskButton.clicked.connect(self.deleteTask)
        self.editTaskTimeButton.clicked.connect(self.editTaskTime)

    def addTask(self):
        dialog = AddTaskDialog(self.window())
        # if user clicks on add task inside dialog
        if dialog.exec():
            task_name = dialog.taskEdit.text()
            row = self.todoTasksList.model().rowCount(QModelIndex())
            self.todoTasksList.model().insertRow(row, QModelIndex(), task_name=task_name, task_type=TaskType.TODO)

    def findMainWindow(self):
        widget = self.parent()
        while widget:
            if widget.objectName() == "main_window":
                logger.debug("Found main window.")
                return widget
            widget = widget.parent()

        return None

    def deleteTask(self):
        # either one of the following will be selected
        todo_selected_index = self.todoTasksList.selectionModel().currentIndex()
        completed_selected_index = self.completedTasksList.selectionModel().currentIndex()

        if self.todoTasksList.selectionModel().hasSelection():
            self.todoTasksList.model().deleteTask(todo_selected_index.row())
        elif self.completedTasksList.selectionModel().hasSelection():
            self.completedTasksList.model().deleteTask(completed_selected_index.row())

    def editTaskTime(self):
        row = None
        task_list_model = None
        if self.todoTasksList.selectionModel().hasSelection():
            row = self.todoTasksList.selectionModel().currentIndex()
            task_list_model = self.todoTasksList.model()
        elif self.completedTasksList.selectionModel().hasSelection():
            row = self.completedTasksList.selectionModel().currentIndex()
            task_list_model = self.completedTasksList.model()

        if row is not None:
            task_id = row.data(TaskListModel.IDRole)
            dialog = EditTaskTimeDialog(self.window(), task_id)

            if dialog.exec():
                elapsed_time = dialog.getElapsedTime()
                if elapsed_time is not None:
                    task_list_model.setData(row, elapsed_time, TaskListModel.ElapsedTimeRole, update_db=True)
                estimated_time = dialog.getTargetTime()
                if estimated_time is not None:
                    task_list_model.setData(row, estimated_time, TaskListModel.TargetTimeRole, update_db=True)

    def setupSelectionBehavior(self):
        """
        To ensure that only one item is selected out of both the lists
        """
        self.todoTasksList.selectionModel().selectionChanged.connect(self.onTodoTasksSelectionChanged)
        self.completedTasksList.selectionModel().selectionChanged.connect(self.onCompletedTasksSelectionChanged)

    def onTodoTasksSelectionChanged(self):
        if self.todoTasksList.selectionModel().hasSelection():
            # disconnecting and connecting again so that the other SelectionChanged method is not called
            # when selection is cleared
            self.completedTasksList.selectionModel().selectionChanged.disconnect(self.onCompletedTasksSelectionChanged)
            self.completedTasksList.clearSelection()
            self.completedTasksList.selectionModel().selectionChanged.connect(self.onCompletedTasksSelectionChanged)

    def onCompletedTasksSelectionChanged(self):
        if self.completedTasksList.selectionModel().hasSelection():
            # disconnecting and connecting again so that the other SelectionChanged method is not called
            # when selection is cleared
            self.todoTasksList.selectionModel().selectionChanged.disconnect(self.onTodoTasksSelectionChanged)
            self.todoTasksList.clearSelection()
            self.todoTasksList.selectionModel().selectionChanged.connect(self.onTodoTasksSelectionChanged)

    def onCurrentWorkspaceChanged(self):
        self.todoTasksList.model().load_data()
        self.completedTasksList.model().load_data()

    def autoSetCurrentTaskID(self):
        if self.todoTasksList.model().currentTaskID() is not None:  # if current task is already set then return
            return
        # else set current task according to below rules
        if self.todoTasksList.selectionModel().hasSelection():
            self.todoTasksList.model().setCurrentTaskID(
                self.todoTasksList.selectionModel().currentIndex().data(TaskListModel.IDRole)
            )
        elif self.todoTasksList.model().rowCount(QModelIndex()) > 0:
            self.todoTasksList.model().setCurrentTaskID(self.todoTasksList.model().index(0).data(TaskListModel.IDRole))
        else:
            self.todoTasksList.model().setCurrentTaskID(None)

        self.todoTasksList.viewport().update()


if __name__ == "__main__":
    app = QApplication()
    w = TaskListView()
    w.show()
    app.exec()
