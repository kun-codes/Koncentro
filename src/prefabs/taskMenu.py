from typing import Optional

from PySide6.QtWidgets import QWidget
from qfluentwidgets import Action, FluentIcon, RoundMenu

from prefabs.customFluentIcon import CustomFluentIcon


class TaskMenu(RoundMenu):
    def __init__(self, title: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(title, parent)

        self.addTaskAction = Action(FluentIcon.ADD, "Add Task")
        self.addSubTaskAction = Action(CustomFluentIcon.ADD_SUBTASK, "Add Subtask")
        self.editTimeAction = Action(FluentIcon.EDIT, "Edit Time")
        self.markTaskAsIncompleteAction = Action(FluentIcon.VPN, "Mark as Incomplete")
        self.markTaskAsCompletedAction = Action(FluentIcon.VPN, "Mark as Completed")
        self.deleteTaskAction = Action(FluentIcon.DELETE, "Delete Subtask")

        self.addAction(self.addTaskAction)
        self.addAction(self.addSubTaskAction)
        self.addAction(self.editTimeAction)
        self.addAction(self.markTaskAsIncompleteAction)
        self.addAction(self.markTaskAsCompletedAction)
        self.addSeparator()
        self.addAction(self.deleteTaskAction)
