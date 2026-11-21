from typing import Optional

from PySide6.QtCore import QModelIndex, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFontMetrics, QPainter, QPixmap
from PySide6.QtWidgets import QListView, QStyle, QStyleOptionViewItem
from qfluentwidgets import FluentIcon, ListItemDelegate, drawIcon, isDarkTheme
from qfluentwidgets.common.color import autoFallbackThemeColor, themeColor
from qfluentwidgets.common.font import getFont

from app_blocker.appBlockerBackend import AppKind
from models.appPickerListModel import AppPickerListModel, AppPickerModelItem


class AppPickerItemDelegate(ListItemDelegate):
    """Row layout: checkbox -> icon -> name/app-id -> kind badge"""

    CHECKBOX_SIZE = 20
    CHECKBOX_MARGIN = 16
    ICON_SIZE = 32
    TEXT_MARGIN = 12
    ITEM_HEIGHT = 56
    SUBTITLE_GAP = 4
    BADGE_HEIGHT = 18
    BADGE_RADIUS = 5
    BADGE_PADDING = 8
    # the badge is hidden when the remaining name/app-id space gets narrower than this
    MIN_BADGE_TEXT_WIDTH = 120

    def __init__(self, parent: QListView) -> None:
        super().__init__(parent)
        self.name_font = getFont(14)
        self.subtitle_font = getFont(12)
        self.badge_font = getFont(11)

    def _getCheckboxRect(self, option: QStyleOptionViewItem) -> QRect:
        return QRect(
            option.rect.left() + self.CHECKBOX_MARGIN,
            option.rect.top() + (option.rect.height() - self.CHECKBOX_SIZE) // 2,
            self.CHECKBOX_SIZE,
            self.CHECKBOX_SIZE,
        )

    def _getIconRect(self, option: QStyleOptionViewItem) -> QRect:
        checkbox = self._getCheckboxRect(option)
        return QRect(
            checkbox.right() + 1 + self.TEXT_MARGIN,
            option.rect.top() + (option.rect.height() - self.ICON_SIZE) // 2,
            self.ICON_SIZE,
            self.ICON_SIZE,
        )

    def _getTextRect(self, option: QStyleOptionViewItem) -> QRect:
        icon = self._getIconRect(option)
        text_x = icon.right() + 1 + self.TEXT_MARGIN
        return QRect(text_x, option.rect.top(), option.rect.right() - self.TEXT_MARGIN - text_x, option.rect.height())

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

    def _paintCheckbox(self, painter: QPainter, option: QStyleOptionViewItem, item: AppPickerModelItem) -> None:
        rect = self._getCheckboxRect(option)
        painter.save()

        border_color = QColor(255, 255, 255, 130) if isDarkTheme() else QColor(0, 0, 0, 130)
        fill_color = QColor(0, 0, 0, 0)
        if item.checked:
            fill_color = themeColor()
        elif item.already_blocked:
            border_color = QColor(255, 255, 255, 60) if isDarkTheme() else QColor(0, 0, 0, 60)

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(border_color)
        painter.setBrush(fill_color)
        painter.drawRoundedRect(rect, 5, 5)

        if item.checked:
            check_rect = QRect(rect.center().x() - 8, rect.center().y() - 8, 16, 16)
            drawIcon(FluentIcon.ACCEPT, painter, check_rect)

        painter.restore()

    def _paintIcon(self, painter: QPainter, icon_rect: QRect, pixmap: Optional[QPixmap]) -> None:
        painter.save()
        if pixmap is not None and not pixmap.isNull():
            painter.drawPixmap(icon_rect, pixmap)
        else:
            # draw a rounded placeholder with an application icon when the app has no icon
            c = 255 if isDarkTheme() else 0
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(c, c, c, 9))
            painter.drawRoundedRect(icon_rect, 6, 6)

            placeholder_size = 20
            placeholder_rect = QRect(
                icon_rect.center().x() - placeholder_size // 2,
                icon_rect.center().y() - placeholder_size // 2,
                placeholder_size,
                placeholder_size,
            )
            drawIcon(FluentIcon.VPN, painter, placeholder_rect)
        painter.restore()

    def _paintText(
        self,
        painter: QPainter,
        text_rect: QRect,
        name: str,
        subtitle: str,
        name_color: Optional[QColor] = None,
    ) -> None:
        name_rect = QRect(text_rect.left(), text_rect.top(), text_rect.width(), text_rect.height() // 2)
        subtitle_rect = QRect(
            text_rect.left(), text_rect.top() + text_rect.height() // 2, text_rect.width(), text_rect.height() // 2
        )

        painter.save()

        # for the name
        painter.setFont(self.name_font)
        if name_color is not None:
            painter.setPen(name_color)
        else:
            painter.setPen(QColor(255, 255, 255) if isDarkTheme() else QColor(0, 0, 0))
        name_metrics = QFontMetrics(self.name_font)
        elided_name = name_metrics.elidedText(name, Qt.TextElideMode.ElideRight, name_rect.width())
        name_rect.adjust(0, 0, 0, -self.SUBTITLE_GAP // 2)
        painter.drawText(name_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom, elided_name)

        # and the subtitle
        painter.setFont(self.subtitle_font)
        painter.setPen(QColor(255, 255, 255, 150) if isDarkTheme() else QColor(0, 0, 0, 150))
        subtitle_metrics = QFontMetrics(self.subtitle_font)
        elided_subtitle = subtitle_metrics.elidedText(subtitle, Qt.TextElideMode.ElideMiddle, subtitle_rect.width())
        subtitle_rect.adjust(0, self.SUBTITLE_GAP // 2, 0, 0)
        painter.drawText(subtitle_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, elided_subtitle)

        painter.restore()

    def _badgeRect(self, option: QStyleOptionViewItem, word: str) -> Optional[QRect]:
        width = QFontMetrics(self.badge_font).horizontalAdvance(word) + 2 * self.BADGE_PADDING
        text_rect = self._getTextRect(option)
        if text_rect.width() - width < self.MIN_BADGE_TEXT_WIDTH:
            return None

        return QRect(
            text_rect.right() - width,
            option.rect.top() + (option.rect.height() - self.BADGE_HEIGHT) // 2,
            width,
            self.BADGE_HEIGHT,
        )

    def _paintBadge(self, painter: QPainter, rect: QRect, word: str, fill: QColor, text_color: QColor) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fill)
        painter.drawRoundedRect(rect, self.BADGE_RADIUS, self.BADGE_RADIUS)
        painter.setFont(self.badge_font)
        painter.setPen(text_color)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, word)
        painter.restore()

    def _paintKindBadge(self, painter: QPainter, rect: QRect, kind: AppKind) -> None:
        c = 255 if isDarkTheme() else 0
        self._paintBadge(painter, rect, kind.value.capitalize(), QColor(c, c, c, 31), QColor(c, c, c, 155))

    def _paintBlockedBadge(self, painter: QPainter, rect: QRect) -> None:
        color = themeColor()
        fill = QColor(color.red(), color.green(), color.blue(), 40)
        text = QColor(color.red(), color.green(), color.blue(), 200)
        self._paintBadge(painter, rect, "Blocked", fill, text)

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        item: Optional[AppPickerModelItem] = index.data(AppPickerListModel.AppRole)
        if item is None:
            return

        self._paintBackgroundAndIndicator(painter, option, index)
        self._paintCheckbox(painter, option, item)

        self._paintIcon(painter, self._getIconRect(option), item.app.app_icon)

        badge_word = "Blocked" if item.already_blocked else item.app.kind.value.capitalize()
        text_rect = self._getTextRect(option)
        badge_rect = self._badgeRect(option, badge_word)
        if badge_rect is not None:
            text_rect = QRect(
                text_rect.left(),
                text_rect.top(),
                badge_rect.left() - self.TEXT_MARGIN - text_rect.left(),
                text_rect.height(),
            )

        self._paintText(painter, text_rect, item.app.app_name, item.app.app_id)

        if badge_rect is not None:
            if item.already_blocked:
                self._paintBlockedBadge(painter, badge_rect)
            else:
                self._paintKindBadge(painter, badge_rect, item.app.kind)

    def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
        size = super().sizeHint(option, index)
        size.setHeight(max(size.height(), self.ITEM_HEIGHT))
        return size
