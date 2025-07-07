from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication, QHBoxLayout, QSizePolicy
from qfluentwidgets import BodyLabel, FluentIcon, SimpleCardWidget

from models.db_tables import Task, TaskType


class TaskCard(SimpleCardWidget):
    """
    TaskCard is a simple card widget that displays a task along with an icon of its own
    """

    def __init__(self, parent=None, task_name="") -> None:
        super().__init__(parent=parent)
        self.setAcceptDrops(True)

        palette = QPalette()
        transparent_colour = QColor(0, 0, 0, int(0.0 * 255))
        palette.setColor(QPalette.ColorRole.Window, transparent_colour)
        self.setPalette(palette)

        # TODO: See if icon is needed else remove it
        self.iconLabel = BodyLabel(self)
        self.iconLabel.setObjectName("iconLabel")
        self.iconLabel.setFixedSize(24, 24)
        self.iconLabel.setPixmap(FluentIcon.ADD.icon().pixmap(24, 24))

        self.taskLabel = BodyLabel(self)
        self.taskLabel.setObjectName("taskLabel")
        self.taskLabel.setText(task_name)

        self.layout = QHBoxLayout(self)

        self.layout.addWidget(self.iconLabel)
        self.layout.addWidget(self.taskLabel)

        self.setObjectName("taskCard")
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)

        self.task_record = Task(task_name=task_name, task_type=TaskType.TODO)

    # # Experimental
    # def drag(self, event):
    #     self.setBackgroundColor(QColor(255, 255, 255, 13 if isDarkTheme() else 170))
    #     event.accept()


if __name__ == "__main__":
    app = QApplication([])
    w = TaskCard(task_name="Hello World")
    w.show()

    app.exec()
