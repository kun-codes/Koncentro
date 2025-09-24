from views.dialogs.addTaskDialog import AddTaskDialog


class AddSubTaskDialog(AddTaskDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.titleLabel.setText("Add Subtask")
        self.taskEdit.setPlaceholderText("Enter Subtask name")
        self.yesButton.setText("Add Subtask")
