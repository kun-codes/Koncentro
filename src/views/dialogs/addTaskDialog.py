from typing import Optional

from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent, QShowEvent
from PySide6.QtWidgets import QWidget
from qfluentwidgets import LineEdit, MessageBoxBase, SubtitleLabel


class AddTaskDialog(MessageBoxBase):
    """
    For the add task dialog in tasks view
    """

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=parent)
        self.titleLabel = SubtitleLabel("Add Task", self)
        self.taskEdit = LineEdit(self)

        self.taskEdit.setPlaceholderText("Enter task name")

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.taskEdit)

        self.yesButton.setText("Add Task")
        self.cancelButton.setText("Cancel")

        self.widget.setMinimumWidth(max(350, int(parent.width() * 0.3)))
        self.yesButton.setDisabled(True)
        self.taskEdit.textChanged.connect(self.onTaskTextChanged)

    def onTaskTextChanged(self) -> None:
        self.yesButton.setDisabled(self.taskEdit.text().strip() == "")

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.taskEdit.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in [Qt.Key_Return, Qt.Key_Enter] and self.yesButton.isEnabled():
            self.yesButton.click()
        else:
            super().keyPressEvent(event)
