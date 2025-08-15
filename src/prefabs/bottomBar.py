from loguru import logger
from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon, ToolTipFilter, ToolTipPosition

from config_values import ConfigValues
from constants import TimerState
from models.task_list_model import TaskListModel
from ui_py.ui_bottom_bar_widget import Ui_BottomBarWidget
from utils.time_conversion import convert_ms_to_hh_mm_ss


class BottomBar(Ui_BottomBarWidget, QWidget):
    def __init__(self, parent=None) -> None:
        super().__init__(parent=None)
        self.parent = parent
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

    def initBottomBar(self) -> None:
        self.update_bottom_bar_timer_label()

        self.skipButton.setEnabled(self.parent.pomodoro_interface.skipButton.isEnabled())
        self.pauseResumeButton.setCheckable(True)
        self.pauseResumeButton.setChecked(False)
        self.pauseResumeButton.setIcon(FluentIcon.PLAY)
        self.pauseResumeButton.clicked.connect(self.bottomBarPauseResumeButtonClicked)
        self.skipButton.clicked.connect(self.parent.pomodoro_interface.skipButtonClicked)
        self.stopButton.clicked.connect(self.parent.pomodoro_interface.stopButtonClicked)

        self.taskLabel.setText("Current Task: None")

    def bottomBarPauseResumeButtonClicked(self) -> None:
        # Sync state with pomodoro view button
        self.parent.pomodoro_interface.pauseResumeButton.setChecked(self.pauseResumeButton.isChecked())
        logger.debug(f"Window state: {self.parent.windowState()}")
        self.parent.pomodoro_interface.pauseResumeButtonClicked()

        # Update bottom bar button icon
        if not self.pauseResumeButton.isChecked():
            self.pauseResumeButton.setIcon(FluentIcon.PLAY)
        else:
            self.pauseResumeButton.setIcon(FluentIcon.PAUSE)

    def update_bottom_bar_timer_label(self) -> None:
        # check if timer is running
        current_timer_state = self.parent.pomodoro_interface.pomodoro_timer_obj.getTimerState()
        if current_timer_state in [TimerState.WORK, TimerState.BREAK, TimerState.LONG_BREAK]:
            # timer is running

            total_session_length_ms = 0
            if current_timer_state == TimerState.WORK:
                total_session_length_ms = ConfigValues.WORK_DURATION * 60 * 1000
            elif current_timer_state == TimerState.BREAK:
                total_session_length_ms = ConfigValues.BREAK_DURATION * 60 * 1000
            elif current_timer_state == TimerState.LONG_BREAK:
                total_session_length_ms = ConfigValues.LONG_BREAK_DURATION * 60 * 1000

            remaining_time_ms = self.parent.pomodoro_interface.pomodoro_timer_obj.remaining_time

            if remaining_time_ms <= 0:  # have to compensate that the first second is not shown
                remaining_time_ms = total_session_length_ms

            hh, mm, ss = convert_ms_to_hh_mm_ss(remaining_time_ms)
            t_hh, t_mm, t_ss = convert_ms_to_hh_mm_ss(total_session_length_ms)

            timer_text = f"{current_timer_state.value}\n{hh:02d}:{mm:02d}:{ss:02d} / {t_hh:02d}:{t_mm:02d}:{t_ss:02d}"
            self.timerLabel.setText(timer_text)
            self.parent.systemTray.tray_menu_timer_status_action.setText(timer_text)

        else:
            # timer is not running
            hh, mm, ss = 0, 0, 0
            t_hh, t_mm, t_ss = 0, 0, 0

            timer_text = f"Idle\n{hh:02d}:{mm:02d}:{ss:02d} / {t_hh:02d}:{t_mm:02d}:{t_ss:02d}"
            self.timerLabel.setText(timer_text)
            self.parent.systemTray.tray_menu_timer_status_action.setText(timer_text)

    def updateBottomBarTaskLabel(self, topLeft: QModelIndex, bottomRight: QModelIndex, roles) -> None:
        # if task name has been updated and only one index is updated (topLeft == bottomRight)
        if Qt.ItemDataRole.DisplayRole in roles and topLeft == bottomRight:
            triggeredTaskID = self.parent.task_interface.todoTasksList.model().data(topLeft, TaskListModel.IDRole)
            # and if the current task ID is the same as the triggered task ID
            if self.parent.get_current_task_id() == triggeredTaskID:
                # then update the bottom bar task label
                self.taskLabel.setText(
                    f"Current Task: {self.parent.task_interface.todoTasksList.model().getTaskNameById(triggeredTaskID)}"
                )
