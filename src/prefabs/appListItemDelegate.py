from typing import Optional

from PySide6.QtCore import QModelIndex, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPixmap
from PySide6.QtWidgets import QListView, QStyle, QStyleOptionViewItem
from qfluentwidgets import FluentIcon, ListItemDelegate, drawIcon, isDarkTheme
from qfluentwidgets.common.color import autoFallbackThemeColor
from qfluentwidgets.common.font import getFont

from models.appListModel import AppListModel


class AppListItemDelegate(ListItemDelegate):
    ICON_SIZE = 32
    ICON_MARGIN = 16
    TEXT_MARGIN = 12
    ITEM_HEIGHT = 64
    NAME_PATH_GAP = 4

    def __init__(self, parent: QListView) -> None:
        super().__init__(parent)
        self.name_font = getFont(14)
        self.path_font = getFont(12)

    def _getIconRect(self, option: QStyleOptionViewItem) -> QRect:
        icon_x = option.rect.left() + self.ICON_MARGIN
        icon_y = option.rect.top() + (option.rect.height() - self.ICON_SIZE) // 2
        return QRect(icon_x, icon_y, self.ICON_SIZE, self.ICON_SIZE)

    def _getTextRect(self, option: QStyleOptionViewItem) -> QRect:
        text_x = self._getIconRect(option).right() + 1 + self.TEXT_MARGIN
        return QRect(
            text_x,
            option.rect.top(),
            option.rect.right() - self.TEXT_MARGIN - text_x,
            option.rect.height(),
        )

    def _paintBackgroundAndIndicator(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        ## pasted from TaskListItemDelegate.paint() which was pasted from TreeItemDelegate.paint()
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)

        if option.state & (QStyle.StateFlag.State_Selected | QStyle.StateFlag.State_MouseOver):
            painter.save()
            painter.setPen(Qt.PenStyle.NoPen)

            # draw background
            h = option.rect.height() - 4
            c = 255 if isDarkTheme() else 0
            painter.setBrush(QColor(c, c, c, 9))
            painter.drawRoundedRect(4, option.rect.y() + 2, self.parent().width() - 8, h, 4, 4)

            # draw indicator
            if option.state & QStyle.StateFlag.State_Selected and self.parent().horizontalScrollBar().value() == 0:
                painter.setBrush(autoFallbackThemeColor(self.lightCheckedColor, self.darkCheckedColor))
                painter.drawRoundedRect(4, 9 + option.rect.y(), 3, h - 13, 1.5, 1.5)

            painter.restore()

    def _paintIcon(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        icon_rect = self._getIconRect(option)
        pixmap: Optional[QPixmap] = index.data(AppListModel.AppIconRole)

        painter.save()
        if pixmap is not None and not pixmap.isNull():
            painter.drawPixmap(icon_rect, pixmap)
        else:
            # draw a rounded placeholder with an application icon when the app has no icon
            c = 255 if isDarkTheme() else 0
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(c, c, c, 9))
            painter.drawRoundedRect(icon_rect, 6, 6)

            icon_size = 20
            icon_rect_placeholder = QRect(
                icon_rect.center().x() - icon_size // 2,
                icon_rect.center().y() - icon_size // 2,
                icon_size,
                icon_size,
            )
            drawIcon(FluentIcon.APPLICATION, painter, icon_rect_placeholder)
        painter.restore()

    def _paintText(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        text_rect = self._getTextRect(option)

        app_name: str = index.data(AppListModel.AppNameRole) or ""
        app_path: str = str(index.data(AppListModel.AppPathRole) or "")

        name_rect = QRect(text_rect.left(), text_rect.top(), text_rect.width(), text_rect.height() // 2)
        path_rect = QRect(
            text_rect.left(), text_rect.top() + text_rect.height() // 2, text_rect.width(), text_rect.height() // 2
        )

        painter.save()

        # for the app name
        painter.setFont(self.name_font)
        painter.setPen(QColor(255, 255, 255) if isDarkTheme() else QColor(0, 0, 0))
        name_metrics = QFontMetrics(self.name_font)
        elided_name = name_metrics.elidedText(app_name, Qt.TextElideMode.ElideRight, name_rect.width())
        name_rect.adjust(0, 0, 0, -self.NAME_PATH_GAP // 2)
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, elided_name)

        # and now the app path
        painter.setFont(self.path_font)
        painter.setPen(QColor(255, 255, 255, 150) if isDarkTheme() else QColor(0, 0, 0, 150))
        path_metrics = QFontMetrics(self.path_font)
        elided_path = path_metrics.elidedText(app_path, Qt.TextElideMode.ElideMiddle, path_rect.width())
        path_rect.adjust(0, self.NAME_PATH_GAP // 2, 0, 0)
        painter.drawText(path_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, elided_path)

        painter.restore()

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        self._paintBackgroundAndIndicator(painter, option, index)

        self._paintIcon(painter, option, index)
        self._paintText(painter, option, index)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        size = super().sizeHint(option, index)
        size.setHeight(max(size.height(), self.ITEM_HEIGHT))
        return size
