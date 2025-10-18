from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QListView, QStyle, QStyleOptionViewItem, QWidget
from qfluentwidgets import ListItemDelegate, isDarkTheme, themeColor

from models.task_list_model import TaskListModel


class RoundedListItemDelegate(ListItemDelegate):
    """Round List item delegate"""

    def __init__(self, parent: QListView) -> None:
        super().__init__(parent)

    def _drawBackground(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        painter.save()
        rect = option.rect.adjusted(1, 1, -1, -1)  # Adjust to fit within the background
        if option.state & QStyle.State_Selected:
            painter.setBrush(option.palette.highlight())
        else:
            painter.setBrush(QColor(255, 255, 255, 13 if isDarkTheme() else 170))
        if isDarkTheme():
            painter.setPen(QColor(0, 0, 0, 48))
        else:
            painter.setPen(QColor(0, 0, 0, 12))
        painter.drawRoundedRect(rect, 5, 5)
        painter.restore()

    def _drawIndicator(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        if option.state & QStyle.State_Selected:
            rect = option.rect.adjusted(1, 1, -1, -1)  # Adjust to fit within the background
            painter.setPen(QPen(themeColor(), 2))  # Set pen with theme color and width 2
            painter.drawRoundedRect(rect, 5, 5)  # Draw rounded rectangle border

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        rect = option.rect
        y = rect.y() + (rect.height() - editor.height()) // 2

        x, w = max(1, rect.x()), rect.width() - 2  # max(1, rect.x()), 1 because indicator border is 2 and half of 2 is
        # 1 and subtract 2 from width because border width is 2

        editor.setGeometry(x, y, w, rect.height())


class RoundedListItemDelegateDisplayTime(RoundedListItemDelegate):
    def __init__(self, parent: QListView) -> None:
        super().__init__(parent)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        super().paint(painter, option, index)
        painter.save()
        rect = option.rect

        # Fetch the time data from the model
        elapsed_time = index.data(TaskListModel.ElapsedTimeRole)
        target_time = index.data(TaskListModel.TargetTimeRole)

        # Convert milliseconds to HH:MM format
        def ms_to_hhmm(ms: int) -> str:
            seconds = ms // 1000
            minutes = seconds // 60
            hours = minutes // 60
            seconds = seconds % 60
            minutes = minutes % 60
            return f"{hours:02}:{minutes:02}:{seconds:02}"

        elapsed_time_str = ms_to_hhmm(elapsed_time)
        target_time_str = ms_to_hhmm(target_time)
        time_str = f"{elapsed_time_str}/{target_time_str}"

        # Draw the time string on the right side
        if isDarkTheme():
            painter.setPen(QColor(255, 255, 255))
        else:
            painter.setPen(QColor(0, 0, 0))
        painter.drawText(rect.adjusted(-100, 0, -10, 0), Qt.AlignRight | Qt.AlignVCenter, time_str)

        painter.restore()

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """
        re-implement this method since the parent method takes into account the original indicator,
        but we have a custom indicator
        """
        rect = option.rect
        y = rect.y() + (rect.height() - editor.height()) // 2
        x, w = rect.x(), rect.width()
        w = w - 2  # subtract 2 to fit within the indicator
        x = x + 1  # add 1 to fit within the indicator

        editor.setGeometry(x, y, w, rect.height())
