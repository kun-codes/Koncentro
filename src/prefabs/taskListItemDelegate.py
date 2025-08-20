from loguru import logger
from PySide6.QtCore import QModelIndex, QRect, Qt, Signal
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
    ToolTipFilter,
    ToolTipPosition,
    TransparentToggleToolButton,
    TreeItemDelegate,
    isDarkTheme,
)
from qfluentwidgets.common.color import autoFallbackThemeColor

from models.task_list_model import TaskListModel
from utils.time_conversion import convert_ms_to_hh_mm_ss


class TaskListItemDelegate(TreeItemDelegate):
    """List item delegate"""

    pauseResumeButtonClicked = Signal(int, bool)  # task_id of clicked button, checked state of clicked button

    def __init__(self, parent: QTreeView) -> None:
        super().__init__(parent)
        self.buttons = {}  # Store buttons for each row
        self.button_size = 24  # Size of the tool button
        self.button_margin = 5  # Margin around the button
        self.margin = 2

        # Connect to the parent's viewport to listen for mouse events
        parent.viewport().installEventFilter(self)

        self._pomodoro_interface = None

    def deleteAllButtons(self) -> None:
        """Delete all buttons when there are no tasks"""
        for button in list(self.buttons.values()):
            button.deleteLater()
        self.buttons.clear()

    def createButton(self, index):
        """Create a ToolButton for the specified index"""
        model = self.parent().model()
        task_id = model.data(index, TaskListModel.IDRole)  # Get task ID

        button = TransparentToggleToolButton(self.parent().viewport())

        if self.parent().objectName() == "completedTasksList":
            button.setCheckable(False)  # buttons in completedTasksList cannot be clicked

        button.setIcon(model.data(index, TaskListModel.IconRole))

        button.setFixedSize(self.button_size, self.button_size)
        if self.parent().objectName() == "todoTasksList":
            button.setToolTip("Pause/Resume")
            button.installEventFilter(ToolTipFilter(button, showDelay=300, position=ToolTipPosition.BOTTOM))

        button.clicked.connect(lambda checked, tid=task_id: self.onButtonClicked(checked, tid))

        # Store button with task_id as key
        self.buttons[task_id] = button
        return button

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

    def onButtonClicked(self, checked, task_id) -> None:
        """Handle button clicks using task_id"""
        if self.parent().objectName() == "completedTasksList":
            return

        model = self.parent().model()

        # Find the row for this task_id
        row = -1
        for i in range(model.rowCount()):
            index = model.index(i, 0)
            if model.data(index, TaskListModel.IDRole) == task_id:
                row = i
                break

        if row == -1:
            logger.warning(f"Triggered after clicking buttons inside taskList. Task ID {task_id} not found in model.")
            return

        # simulate the click the pauseResumeButton of pomodoro_interface but don't actually click it
        button = self.buttons[task_id]
        self.pauseResumeButtonClicked.emit(task_id, button.isChecked())

        if self._pomodoro_interface is None:  # get the pomodoro_interface only if it is not already set
            self._pomodoro_interface = self._get_pomodoro_interface()

        # hack to stop the timer so that when another item in this delegate is clicked while timer is running, the
        # duration isn't restarted. Its similar to pausing and resuming but the pause in this case has almost no
        # downtime
        self._pomodoro_interface.pomodoro_timer_obj.pomodoro_timer.stop()
        self._pomodoro_interface.pauseResumeButtonClicked()

        index = model.index(row, 0)
        task_name = model.data(index, Qt.DisplayRole)
        logger.debug(f"Button clicked for task ID {task_id}, row {row}: {task_name}, checked: {checked}")

        icon = FluentIcon.PAUSE if checked else FluentIcon.PLAY
        model.setData(index, icon, TaskListModel.IconRole, update_db=False)
        button.setIcon(icon)

        # Set every other button to unchecked
        for i in range(model.rowCount()):
            idx = model.index(i, 0)
            tid = model.data(idx, TaskListModel.IDRole)
            if tid != task_id and tid in self.buttons:
                self.buttons[tid].setChecked(False)
                model.setData(idx, FluentIcon.PLAY, TaskListModel.IconRole, update_db=False)
                self.buttons[tid].setIcon(FluentIcon.PLAY)

        if self.parent().objectName() == "todoTasksList":
            model.setCurrentTaskID(task_id)
            self.parent().viewport().update()

    def setCheckedStateOfButton(self, task_id, checked) -> None:
        button = self.buttons.get(task_id)
        if button:
            button.setChecked(checked)
            button.setIcon(FluentIcon.PAUSE if checked else FluentIcon.PLAY)

    def paint(self, painter, option, index) -> None:
        ## pasted from TreeItemDelegate.paint()
        painter.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing)

        if index.data(Qt.CheckStateRole) is not None:
            self._drawCheckBox(painter, option, index)

        if option.state & (QStyle.State_Selected | QStyle.State_MouseOver):
            painter.save()
            painter.setPen(Qt.NoPen)

            # draw background
            h = option.rect.height() - 4
            c = 255 if isDarkTheme() else 0
            painter.setBrush(QColor(c, c, c, 9))
            painter.drawRoundedRect(4, option.rect.y() + 2, self.parent().width() - 8, h, 4, 4)

            # draw indicator
            if option.state & QStyle.State_Selected and self.parent().horizontalScrollBar().value() == 0:
                painter.setBrush(autoFallbackThemeColor(self.lightCheckedColor, self.darkCheckedColor))
                painter.drawRoundedRect(4, 9 + option.rect.y(), 3, h - 13, 1.5, 1.5)

            painter.restore()
        ## pasted till above line

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

        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(option.rect, 5, 5)

        # draw time elapsed and target time
        painter.setPen(Qt.GlobalColor.white if isDark else Qt.GlobalColor.black)
        font_metrics = QFontMetrics(option.font)

        elapsed_time_ms = index.data(TaskListModel.ElapsedTimeRole)
        target_time_ms = index.data(TaskListModel.TargetTimeRole)

        ehh, emm, ess = convert_ms_to_hh_mm_ss(elapsed_time_ms)
        thh, tmm, tss = convert_ms_to_hh_mm_ss(target_time_ms)

        time_text = f"{ehh:02d}:{emm:02d}:{ess:02d} / {thh:02d}:{tmm:02d}:{tss:02d}"
        time_text_width = font_metrics.horizontalAdvance(time_text)
        hello_world_x = option.rect.right() - time_text_width - 10
        hello_world_rect = QRect(hello_world_x, option.rect.top(), time_text_width, option.rect.height())
        painter.drawText(hello_world_rect, Qt.AlignRight | Qt.AlignVCenter, time_text)

        # Get task ID
        task_id = index.data(TaskListModel.IDRole)

        # Delete buttons for tasks that no longer exist
        task_ids = set()
        model = self.parent().model()
        for i in range(model.rowCount()):
            idx = model.index(i, 0)
            task_ids.add(model.data(idx, TaskListModel.IDRole))

        for tid in list(self.buttons.keys()):
            if tid not in task_ids:
                button = self.buttons.pop(tid)
                button.deleteLater()

        # Create or position the button for this task
        if task_id not in self.buttons:
            self.createButton(index)

        button = self.buttons[task_id]
        button_x = option.rect.left() + self.button_margin
        button_y = option.rect.top() + (option.rect.height() - self.button_size) // 2
        button.setGeometry(button_x, button_y, self.button_size, self.button_size)
        button.setVisible(True)

        # Adjust option.rect to account for button and time text
        button_width = self.button_size + 2 * self.button_margin
        adjusted_option = QStyleOptionViewItem(option)
        adjusted_option.rect.adjust(button_width, 0, -time_text_width - 10, 0)

        QStyledItemDelegate.paint(self, painter, adjusted_option, index)

    def updateEditorGeometry(self, editor: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> None:
        rect = option.rect
        y = rect.y() + (rect.height() - editor.height()) // 2

        # Account for button width
        button_width = self.button_size + 2 * self.button_margin
        x = max(5, rect.x() + button_width)
        w = rect.width() - button_width - 5  # Adjust width for button

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
        size.setHeight(size.height() * SIZE_MULTIPLIER)

        min_height = self.button_size + 2 * self.margin
        if size.height() < min_height:
            size.setHeight(min_height)
        return size

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
        lineEdit = LineEdit(parent.parent())
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

    def setModelData(self, editor, model, index) -> None:
        text = editor.text()
        if text:
            model.setData(index, text, Qt.ItemDataRole.DisplayRole)
        # else:
        #     model.setData(index, "", Qt.ItemDataRole.DisplayRole)
