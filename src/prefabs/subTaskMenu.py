from typing import Optional

from PySide6.QtWidgets import QWidget
from qfluentwidgets import Action, FluentIcon, RoundMenu

from prefabs.customFluentIcon import CustomFluentIcon


class SubTaskMenu(RoundMenu):
    def __init__(self, title: str = "", parent: Optional[QWidget] = None) -> None:
        super().__init__(title, parent)

        self.addSubTaskAction = Action(CustomFluentIcon.ADD_SUBTASK, "Add Subtask")
        self.editTimeAction = Action(FluentIcon.EDIT, "Edit Time")
        self.deleteSubTaskAction = Action(FluentIcon.DELETE, "Delete Subtask")

        self.addAction(self.addSubTaskAction)
        self.addAction(self.editTimeAction)
        self.addAction(self.deleteSubTaskAction)
