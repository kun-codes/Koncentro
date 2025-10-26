from PySide6.QtCore import QModelIndex
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QListView, QStyle, QStyleOptionViewItem, QWidget
from qfluentwidgets import ListItemDelegate, isDarkTheme, themeColor


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
