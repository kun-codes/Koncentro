from PySide6.QtCore import QTime
from qfluentwidgets import MessageBoxBase, SubtitleLabel, TimePicker

from models.task_lookup import TaskLookup


class EditTaskTimeDialog(MessageBoxBase):
    def __init__(self, parent=None, task_id=None) -> None:
        super().__init__(parent=parent)

        self.elapsedTimeLabel = SubtitleLabel("Elapsed Time", self)
        self.estimateTimeLabel = SubtitleLabel("Estimated Time", self)

        self.elapsedTimePicker = TimePicker(self, showSeconds=True)
        self.estimateTimePicker = TimePicker(self, showSeconds=True)

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

        self.elapsed_time_changed = False
        self.target_time_changed = False

        self.elapsedTimePicker.timeChanged.connect(lambda: self.setElapsedTimeChanged(True))
        self.estimateTimePicker.timeChanged.connect(lambda: self.setTargetTimeChanged(True))

    def setElapsedTimeChanged(self, value) -> None:
        self.elapsed_time_changed = value

    def setTargetTimeChanged(self, value) -> None:
        self.target_time_changed = value

    def convertMsToQTime(self, ms):
        seconds = ms // 1000
        minute, second = divmod(seconds, 60)
        hour, minute = divmod(minute, 60)
        return QTime(hour, minute, second)

    def getElapsedTime(self):
        if self.elapsed_time_changed:
            time = self.elapsedTimePicker.getTime()
            return (time.hour() * 60 * 60 + time.minute() * 60 + time.second()) * 1000
        return None

    def getTargetTime(self):
        if self.target_time_changed:
            time = self.estimateTimePicker.getTime()
            return (time.hour() * 60 * 60 + time.minute() * 60 + time.second()) * 1000
        return None


if __name__ == "__main__":
    import sys

    from PySide6.QtWidgets import QApplication

    app = QApplication(sys.argv)
    dialog = EditTaskTimeDialog()
    dialog.exec()
    sys.exit(app.exec())
