from typing import Optional

from PySide6.QtCore import QTime
from PySide6.QtWidgets import QWidget
from qfluentwidgets import MessageBoxBase, PickerColumnFormatter, SubtitleLabel, TimePicker

from models.task_lookup import TaskLookup


class TimeFormatter(PickerColumnFormatter):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text

    def encode(self, value: int) -> str:
        return str(value) + self.text

    def decode(self, value: str) -> int:
        return int(value[:-1])


class EditTaskTimeDialog(MessageBoxBase):
    def __init__(self, parent: Optional[QWidget], task_id: int) -> None:
        super().__init__(parent=parent)

        self.elapsedTimeLabel: SubtitleLabel = SubtitleLabel("Elapsed Time", self)
        self.estimateTimeLabel: SubtitleLabel = SubtitleLabel("Estimated Time", self)

        self.elapsedTimePicker: TimePicker = TimePicker(self, showSeconds=True)
        self.estimateTimePicker: TimePicker = TimePicker(self, showSeconds=True)

        self.elapsedTimePicker.setColumnFormatter(0, TimeFormatter("h"))
        self.elapsedTimePicker.setColumnFormatter(1, TimeFormatter("m"))
        self.elapsedTimePicker.setColumnFormatter(2, TimeFormatter("s"))
        self.estimateTimePicker.setColumnFormatter(0, TimeFormatter("h"))
        self.estimateTimePicker.setColumnFormatter(1, TimeFormatter("m"))
        self.estimateTimePicker.setColumnFormatter(2, TimeFormatter("s"))

        elapsed_time = TaskLookup.get_elapsed_time(task_id)
        target_time = TaskLookup.get_target_time(task_id)

        # convert ms to QTime
        elapsed_time_qtime = self.convertMsToQTime(elapsed_time)
        target_time_qtime = self.convertMsToQTime(target_time)

        self.elapsedTimePicker.setTime(elapsed_time_qtime)
        self.estimateTimePicker.setTime(target_time_qtime)

        self.viewLayout.addWidget(self.elapsedTimeLabel)
        self.viewLayout.addWidget(self.elapsedTimePicker)
        self.viewLayout.addWidget(self.estimateTimeLabel)
        self.viewLayout.addWidget(self.estimateTimePicker)

        self.elapsed_time_changed: bool = False
        self.target_time_changed: bool = False

        self.elapsedTimePicker.timeChanged.connect(lambda: self.setElapsedTimeChanged(True))
        self.estimateTimePicker.timeChanged.connect(lambda: self.setTargetTimeChanged(True))

    def setElapsedTimeChanged(self, value: bool) -> None:
        self.elapsed_time_changed = value

    def setTargetTimeChanged(self, value: bool) -> None:
        self.target_time_changed = value

    def convertMsToQTime(self, ms: int) -> QTime:
        seconds = ms // 1000
        minute, second = divmod(seconds, 60)
        hour, minute = divmod(minute, 60)
        return QTime(hour, minute, second)

    def getElapsedTime(self) -> Optional[int]:
        if self.elapsed_time_changed:
            time = self.elapsedTimePicker.getTime()
            return (time.hour() * 60 * 60 + time.minute() * 60 + time.second()) * 1000
        return None

    def getTargetTime(self) -> Optional[int]:
        if self.target_time_changed:
            time = self.estimateTimePicker.getTime()
            return (time.hour() * 60 * 60 + time.minute() * 60 + time.second()) * 1000
        return None
