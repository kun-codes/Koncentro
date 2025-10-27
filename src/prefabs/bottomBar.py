from typing import Optional

from loguru import logger
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, ToolTipFilter, ToolTipPosition

from models.taskListModel import TaskListModel
from ui_py.ui_bottom_bar_widget import Ui_BottomBarWidget
from views.subinterfaces.pomodoroView import PomodoroView
from views.subinterfaces.tasksView import TaskListView


class BottomBar(Ui_BottomBarWidget, QWidget):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent=None)
        self.parent: Optional[QWidget] = parent
        self.setupUi(self)

        self.initWidget()

    def initWidget(self) -> None:
        self.stopButton.setIcon(FluentIcon.CLOSE)
        self.pauseResumeButton.setIcon(FluentIcon.PLAY)
        self.skipButton.setIcon(FluentIcon.CHEVRON_RIGHT)

        self.stopButton.setCheckable(False)
        self.pauseResumeButton.setCheckable(True)
        self.pauseResumeButton.setChecked(False)  # Changed from True to False to match PLAY icon
        self.skipButton.setCheckable(False)

        self.stopButton.setToolTip("Stop")
        self.stopButton.installEventFilter(ToolTipFilter(self.stopButton, showDelay=300, position=ToolTipPosition.TOP))
        self.pauseResumeButton.setToolTip("Pause/Resume")
        self.pauseResumeButton.installEventFilter(
            ToolTipFilter(self.pauseResumeButton, showDelay=300, position=ToolTipPosition.TOP)
        )
        self.skipButton.setToolTip("Skip")
        self.skipButton.installEventFilter(ToolTipFilter(self.skipButton, showDelay=300, position=ToolTipPosition.TOP))

        self.timerLabel.setText("Idle\n00:00:00 / 00:00:00")  # text shown by update_bottom_bar_timer_label of
        # MainWindow when timer is idle

    def initBottomBar(self, pomodoro_interface: PomodoroView, task_interface: TaskListView) -> None:
        self.pomodoro_interface: PomodoroView = pomodoro_interface
        self.task_interface: TaskListView = task_interface

        self.skipButton.setEnabled(self.pomodoro_interface.skipButton.isEnabled())
        self.pauseResumeButton.setCheckable(True)
        self.pauseResumeButton.setChecked(False)
        self.pauseResumeButton.setIcon(FluentIcon.PLAY)
        self.pauseResumeButton.clicked.connect(self.bottomBarPauseResumeButtonClicked)
        self.skipButton.clicked.connect(self.pomodoro_interface.skipButtonClicked)
        self.stopButton.clicked.connect(self.pomodoro_interface.stopButtonClicked)

        self.taskLabel.setText("Current Task: None")

    def bottomBarPauseResumeButtonClicked(self) -> None:
        # Sync state with pomodoro view button
        self.pomodoro_interface.pauseResumeButton.setChecked(self.pauseResumeButton.isChecked())
        logger.debug(f"Window state: {self.parent.windowState()}")
        self.pomodoro_interface.pauseResumeButtonClicked()

        # Update bottom bar button icon
        if not self.pauseResumeButton.isChecked():
            self.pauseResumeButton.setIcon(FluentIcon.PLAY)
        else:
            self.pauseResumeButton.setIcon(FluentIcon.PAUSE)

    def updateBottomBarTaskLabel(
        self, topLeft: QModelIndex, bottomRight: QModelIndex, roles: list[Qt.ItemDataRole]
    ) -> None:
        # if task name has been updated and only one index is updated (topLeft == bottomRight)
        if Qt.ItemDataRole.DisplayRole in roles and topLeft == bottomRight:
            triggeredTaskID = self.task_interface.todoTasksList.model().data(topLeft, TaskListModel.IDRole)
            # and if the current task ID is the same as the triggered task ID
            if self.parent.get_current_task_id() == triggeredTaskID:
                # then update the bottom bar task label
                self.taskLabel.setText(
                    f"Current Task: {self.task_interface.todoTasksList.model().getTaskNameById(triggeredTaskID)}"
                )
