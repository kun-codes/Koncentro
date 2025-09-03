from loguru import logger
from PySide6.QtCore import QEvent, QModelIndex, QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFontMetrics, QPainter
from PySide6.QtWidgets import (
    QApplication,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
    QTreeView,
    QWidget,
)
from qfluentwidgets import (
    FluentIcon,
    LineEdit,
    TreeItemDelegate,
    drawIcon,
    isDarkTheme,
)
from qfluentwidgets.common.color import autoFallbackThemeColor

from models.config import app_settings
from models.task_list_model import TaskListModel
from utils.time_conversion import convert_ms_to_hh_mm_ss


class TaskListItemDelegate(TreeItemDelegate):
    """List item delegate"""

    pauseResumeButtonClicked = Signal(int, bool)  # task_id of clicked button, checked state of clicked button

    def __init__(self, parent: QTreeView) -> None:
        super().__init__(parent)
        self.button_size = 24  # Size of the tool button
        self.button_margin = 5  # Margin around the button
        self.margin = 2
        self._pomodoro_interface = None
        # Track button states for checked appearance
        self._button_states = {}  # task_id -> bool (checked state)
        # Track which button is currently being hovered
        self._hovered_button_task_id = None

    def _get_pomodoro_interface(self):
        # find the parent widget with the name "pomodoro_interface"
        if self._pomodoro_interface:
            return self._pomodoro_interface

        parent = self.parent()
        while parent:
            if parent.objectName() == "main_window":
                break
            parent = parent.parent()

        # find child of parent with name pomodoro_interface
        return parent.findChild(QWidget, "pomodoro_interface", options=Qt.FindChildOption.FindChildrenRecursively)

    def setCheckedStateOfButton(self, task_id, checked) -> None:
        """Update the checked state of a button"""
        self._button_states[task_id] = checked
        # Trigger a repaint to update the visual state
        self.parent().viewport().update()

    def syncWithMainButtons(self) -> None:
        """Sync the current task button state with pomodoro and bottom bar buttons"""
        model = self.parent().model()
        current_task_id = model.currentTaskID()

        if current_task_id is None:
            return

        if self._pomodoro_interface is None:
            self._pomodoro_interface = self._get_pomodoro_interface()

        if self._pomodoro_interface:
            pomodoro_checked = self._pomodoro_interface.pauseResumeButton.isChecked()

            self._button_states[current_task_id] = pomodoro_checked

            icon = FluentIcon.PAUSE if pomodoro_checked else FluentIcon.PLAY
            current_index = model.currentTaskIndex()
            if current_index and current_index.isValid():
                model.setData(current_index, icon, TaskListModel.IconRole, update_db=False)

            # Trigger repaint
            self.parent().viewport().update()

    def _getButtonRect(self, option: QStyleOptionViewItem) -> QRect:
        """Get the rectangle where the button should be drawn"""
        button_x = option.rect.left() + 3 * self.button_margin
        button_y = option.rect.top() + (option.rect.height() - self.button_size) // 2
        return QRect(button_x, button_y, self.button_size, self.button_size)

    def _getTimeTextRect(self, option: QStyleOptionViewItem, index: QModelIndex) -> QRect:
        """Get the rectangle where the time text is drawn"""
        font_metrics = QFontMetrics(option.font)

        elapsed_time_ms = index.data(TaskListModel.ElapsedTimeRole)
        target_time_ms = index.data(TaskListModel.TargetTimeRole)

        ehh, emm, ess = convert_ms_to_hh_mm_ss(elapsed_time_ms)
        thh, tmm, tss = convert_ms_to_hh_mm_ss(target_time_ms)

        time_text = f"{ehh:02d}:{emm:02d}:{ess:02d} / {thh:02d}:{tmm:02d}:{tss:02d}"
        time_text_width = font_metrics.horizontalAdvance(time_text)
        time_text_x = option.rect.right() - time_text_width - 10

        return QRect(time_text_x, option.rect.top(), time_text_width, option.rect.height())

    def _getTreeArrowRect(self, option: QStyleOptionViewItem, index: QModelIndex) -> QRect:
        """Get the rectangle where the tree expand/collapse arrow is drawn"""
        # Based on the actual implementation in tree_view.py
        indent_size = self.parent().indentation()

        level = 0
        current_index = index
        while current_index.parent().isValid():
            current_index = current_index.parent()
            level += 1

        # arrow positioning is based on pyqt-fluent-widget's TreeView.viewportEvent() logic
        # arrow click area is between indent and indent + 10 in the above mentioned logic
        indent = level * indent_size + 20
        arrow_x = indent
        arrow_width = 10  # width of the clickable arrow area
        arrow_height = 16  # guessed the height of the arrow
        arrow_y = option.rect.top() + (option.rect.height() - arrow_height) // 2

        return QRect(arrow_x, arrow_y, arrow_width, arrow_height)

    def _paintButton(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        """Paint the button manually"""
        task_id = index.data(TaskListModel.IDRole)
        if task_id is None:
            return

        # check if this is the current task to sync state with main buttons
        model = self.parent().model()
        is_current_task = model.currentTaskID() == task_id

        # For current task, sync state with pomodoro interface
        if is_current_task:
            if self._pomodoro_interface is None:
                self._pomodoro_interface = self._get_pomodoro_interface()

            if self._pomodoro_interface:
                # Sync with pomodoro button state
                pomodoro_checked = self._pomodoro_interface.pauseResumeButton.isChecked()
                self._button_states[task_id] = pomodoro_checked

        is_checked = self._button_states.get(task_id, False)

        is_button_hovered = self._hovered_button_task_id == task_id

        if is_current_task and self._pomodoro_interface:
            # use the same icon as the pomodoro button for current task
            icon = FluentIcon.PAUSE if is_checked else FluentIcon.PLAY
        else:
            icon = index.data(TaskListModel.IconRole)
            if icon is None:
                icon = FluentIcon.PLAY

        button_rect = self._getButtonRect(option)

        # draw button background only when checked or when specifically hovering over button
        if is_checked or is_button_hovered:
            painter.save()
            painter.setPen(Qt.PenStyle.NoPen)

            if is_checked:
                theme_color = app_settings.get(app_settings.themeColor)
                painter.setBrush(theme_color)
            else:
                if isDarkTheme():
                    painter.setBrush(QColor(255, 255, 255, int(255 * 0.09)))  # colour from button.qss in
                    # pyqt-fluent-widgets repo
                else:
                    painter.setBrush(QColor(0, 0, 0, int(255 * 0.09)))  # colour from button.qss in
                    # pyqt-fluent-widgets repo

            painter.drawRoundedRect(button_rect, 4, 4)
            painter.restore()

        # Draw the icon
        painter.save()

        # Set opacity based on state (similar to ToolButton paintEvent)
        if not self.parent().isEnabled():
            painter.setOpacity(0.43)
        elif is_button_hovered:
            painter.setOpacity(0.8)

        # Draw icon centered in button rect
        icon_size = min(self.button_size - 4, 16)  # Leave some padding
        icon_x = button_rect.center().x() - icon_size // 2
        icon_y = button_rect.center().y() - icon_size // 2
        icon_rect = QRect(icon_x, icon_y, icon_size, icon_size)
        # translating +1 across x axis because FluentIconEngine.paint() moves the icon by 1 pixel to the right
        # translating +1 across y axis because experimentally found that it centers the icon on the background
        icon_rect.translate(QPoint(1, 1))

        drawIcon(icon, painter, icon_rect)
        painter.restore()

    def editorEvent(self, event: QEvent, model, option: QStyleOptionViewItem, index: QModelIndex) -> bool:
        """Handle mouse events for button clicks and hover"""

        # make buttons of completed tasks list non interactive
        if self.parent().objectName() == "completedTasksList":
            return False

        task_id = index.data(TaskListModel.IDRole)
        if task_id is None:
            return False

        button_rect = self._getButtonRect(option)

        if event.type() == QEvent.Type.MouseMove:
            mouse_event = event
            if hasattr(mouse_event, "pos"):
                if button_rect.contains(mouse_event.pos()):
                    if self._hovered_button_task_id != task_id:
                        self._hovered_button_task_id = task_id
                        # repaint to show hover effect
                        self.parent().viewport().update()
                else:
                    if self._hovered_button_task_id == task_id:
                        self._hovered_button_task_id = None
                        # repaint to remove hover effect
                        self.parent().viewport().update()

        elif event.type() == QEvent.Type.Leave:
            # clear hover state as mouse left the view entirely
            if self._hovered_button_task_id is not None:
                self._hovered_button_task_id = None
                self.parent().viewport().update()

        elif event.type() == QEvent.Type.MouseButtonRelease:
            mouse_event = event
            if hasattr(mouse_event, "pos"):
                if button_rect.contains(mouse_event.pos()):
                    # Toggle button state
                    current_state = self._button_states.get(task_id, False)
                    new_state = not current_state
                    self._button_states[task_id] = new_state

                    self._onButtonClicked(new_state, task_id, index)
                    return True

        elif event.type() == QEvent.Type.MouseButtonDblClick:
            # handle double-click events to prevent editor spawning when double clicked on restricted areas
            mouse_event = event
            if hasattr(mouse_event, "pos"):
                button_rect = self._getButtonRect(option)
                time_text_rect = self._getTimeTextRect(option, index)

                if button_rect.contains(mouse_event.pos()) or time_text_rect.contains(mouse_event.pos()):
                    return True  # Consume the event to prevent editor spawning

                # Check if double-click is on tree arrow (only for parent items)
                if model.hasChildren(index):
                    tree_arrow_rect = self._getTreeArrowRect(option, index)
                    if tree_arrow_rect.contains(mouse_event.pos()):
                        return True  # Consume the event to prevent editor spawning

        return False

    def _onButtonClicked(self, checked: bool, task_id: int, index: QModelIndex) -> None:
        """Handle button clicks"""
        logger.debug(f"Button clicked for task ID {task_id}, checked: {checked}")
        if self.parent().objectName() == "completedTasksList":
            return

        model = self.parent().model()

        self.pauseResumeButtonClicked.emit(task_id, checked)

        if self._pomodoro_interface is None:
            self._pomodoro_interface = self._get_pomodoro_interface()

        # hack to stop the timer so that when another item in this delegate is clicked while timer is running, the
        # duration isn't restarted. Its similar to pausing and resuming but the pause in this case has almost no
        # downtime
        self._pomodoro_interface.pomodoro_timer_obj.pomodoro_timer.stop()
        self._pomodoro_interface.pauseResumeButtonClicked()

        icon = FluentIcon.PAUSE if checked else FluentIcon.PLAY
        model.setData(index, icon, TaskListModel.IconRole, update_db=False)

        # Set every other button to unchecked
        for i in range(model.rowCount()):
            root_idx = model.index(i, 0)
            root_tid = model.data(root_idx, TaskListModel.IDRole)
            if root_tid != task_id and root_tid in self._button_states:
                self._button_states[root_tid] = False
                model.setData(root_idx, FluentIcon.PLAY, TaskListModel.IconRole, update_db=False)

            # check subtasks
            for j in range(model.rowCount(root_idx)):
                subtask_idx = model.index(j, 0, root_idx)
                subtask_tid = model.data(subtask_idx, TaskListModel.IDRole)
                if subtask_tid != task_id and subtask_tid in self._button_states:
                    self._button_states[subtask_tid] = False
                    model.setData(subtask_idx, FluentIcon.PLAY, TaskListModel.IconRole, update_db=False)

        if self.parent().objectName() == "todoTasksList":
            model.setCurrentTaskID(task_id)
            self.parent().viewport().update()

    def paint(self, painter, option, index) -> None:
        ## pasted from TreeItemDelegate.paint()
        painter.setRenderHints(QPainter.RenderHint.Antialiasing | QPainter.RenderHint.TextAntialiasing)

        if index.data(Qt.ItemDataRole.CheckStateRole) is not None:
            self._drawCheckBox(painter, option, index)

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
        ## pasted till above line

        self._paintBackground(painter, option, index)

        # Paint the button manually
        self._paintButton(painter, option, index)

        time_text_width: int = self._paintTimeText(painter, option, index)

        # Adjust option.rect to account for button and time text
        button_width = self.button_size + 2 * self.button_margin
        adjusted_option = QStyleOptionViewItem(option)
        adjusted_option.rect.adjust(button_width, 0, -time_text_width - 10, 0)

        QStyledItemDelegate.paint(self, painter, adjusted_option, index)

    def _paintBackground(self, painter, option, index):
        isDark = isDarkTheme()
        c = 255 if isDark else 0
        alpha = 0

        if index.data(Qt.ItemDataRole.BackgroundRole):
            theme_color: QColor = index.data(Qt.ItemDataRole.BackgroundRole)
            alpha_boost = 45 if isDark else 30
            theme_color.setAlpha(
                alpha + alpha_boost if alpha != 0 else 17 + alpha_boost
            )  # increasing alpha to make it more visible
            # 17 because the alpha of a selected row is 17
            painter.setBrush(theme_color)
        else:
            painter.setBrush(QColor(c, c, c, alpha))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(option.rect, 5, 5)

    def _paintTimeText(self, painter, option, index) -> int:
        """
        will draw time text and return the width of the text
        """
        isDark = isDarkTheme()
        # draw time elapsed and target time
        painter.setPen(Qt.GlobalColor.white if isDark else Qt.GlobalColor.black)

        time_text_rect = self._getTimeTextRect(option, index)

        elapsed_time_ms = index.data(TaskListModel.ElapsedTimeRole)
        target_time_ms = index.data(TaskListModel.TargetTimeRole)

        ehh, emm, ess = convert_ms_to_hh_mm_ss(elapsed_time_ms)
        thh, tmm, tss = convert_ms_to_hh_mm_ss(target_time_ms)

        time_text = f"{ehh:02d}:{emm:02d}:{ess:02d} / {thh:02d}:{tmm:02d}:{tss:02d}"

        painter.drawText(time_text_rect, Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, time_text)

        return time_text_rect.width()

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        rect = option.rect
        y = rect.y() + (rect.height() - editor.height()) // 2

        # Account for button width
        button_width = self.button_size + 4 * self.button_margin  # 4 seems to make the editor appear on top of
        # the label in a pixel perfect way
        x = max(5, rect.x() + button_width)
        w = rect.width() - button_width  # Adjust width for button

        editor.setGeometry(x, y, w, rect.height())

    def sizeHint(self, option, index):
        """Ensure the item is tall enough for the button"""
        size = super().sizeHint(option, index)
        # I derived this value of 1.3 constant from the previous implementation of TaskListItemDelegate when it
        # inherited from ListItemDelegate. The height was calculated to 39px on a 1920x1080 screen on KDE Wayland
        # When TaskListItemDelegate was changed to inherit from TreeItemDelegate, the height was calculated as 30px
        # To make 30px into 39px, 1.3 has to be multiplied to 30px. This multiplication is done for consistency of
        # looks across app versions. I am using the multiplier instead of a fixed value of 39px because the
        # QStyledItemDelegate.sizeHint() can return a different height based on the font size and other factors
        SIZE_MULTIPLIER = 1.3
        size.setHeight(int(size.height() * SIZE_MULTIPLIER))

        min_height = self.button_size + 2 * self.margin
        if size.height() < min_height:
            size.setHeight(min_height)
        return size

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        lineEdit = LineEdit(parent)
        lineEdit.setProperty("transparent", False)
        lineEdit.setStyle(QApplication.style())
        return lineEdit

    def setEditorData(self, editor, index) -> None:
        """
        Is also called every time the elapsed time of a task is updated which resets the task name in the editor
        when editing is in progress. Hence the below check is necessary to avoid interrupting user input.
        """
        if editor.hasFocus():
            return

        text = self.parent().model().data(index, Qt.ItemDataRole.DisplayRole)
        editor.setText(text)

    def setModelData(self, editor, model, index: QModelIndex) -> None:
        text = editor.text()
        if text:
            model.setData(index, text, Qt.ItemDataRole.DisplayRole)
