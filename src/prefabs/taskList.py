from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QBrush, QColor, QPainter, QPen
from PySide6.QtWidgets import QAbstractItemView, QListView, QWidget
from qfluentwidgets import ListItemDelegate, ListView, isDarkTheme

from prefabs.taskListItemDelegate import TaskListItemDelegate
from ui_py.ui_tasks_list_view import Ui_TaskView


class TaskList(ListView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAutoScroll(True)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.current_editor = None

        self._mousePressedOnItem = False

        self.entered.disconnect()  # see mouseMoveEvent method's docstring

        self.setItemDelegate(TaskListItemDelegate(self))

        self.editor_width_reduction = 5  # the same number in TaskListItemDelegate's updateEditorGeometry method

        # Custom drop indicator properties
        self.dropIndicatorRect = QRect()
        self.dropIndicatorPosition = -1

    def paintEvent(self, event):
        """
        Override the paint event to add custom drop indicator drawing
        source: https://oglop.gitbooks.io/pyqt-pyside-cookbook/content/tree/drop_indicator.html
        """
        # Delete all buttons when there are no items in the model
        if self.model() and self.model().rowCount() == 0:
            delegate = self.itemDelegate()
            if hasattr(delegate, "deleteAllButtons"):
                delegate.deleteAllButtons()

        super().paintEvent(event)
        if self.state() == QAbstractItemView.State.DraggingState:
            painter = QPainter(self.viewport())
            self.paintDropIndicator(painter)

    def paintDropIndicator(self, painter):
        """
        Draw a custom white drop indicator
        source: https://oglop.gitbooks.io/pyqt-pyside-cookbook/content/tree/drop_indicator.html
        """
        if not self.dropIndicatorRect.isNull():
            rect = self.dropIndicatorRect
            if isDarkTheme():
                brush = QBrush(QColor(Qt.white))
            else:
                brush = QBrush(QColor(Qt.black))

            if rect.height() == 0:
                # Draw a horizontal line for above/below positions
                rect.setWidth(rect.width() - 6)  # subtract 6 pixels so that right side of drop indicator
                # shows within bounds of TaskList
                pen = QPen(brush, 1, Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.drawLine(rect.topLeft(), rect.topRight())
            else:
                # Draw a rectangle for on-item position
                rect.setWidth(rect.width() - 6)  # subtract 6 pixels so that right side of drop indicator
                # shows within bounds of TaskList
                pen = QPen(brush, 1, Qt.PenStyle.SolidLine)
                painter.setPen(pen)
                painter.drawRect(rect)

    def dragMoveEvent(self, event):
        """
        Update the drop indicator position during drag move events
        source: https://oglop.gitbooks.io/pyqt-pyside-cookbook/content/tree/drop_indicator.html
        """
        super().dragMoveEvent(event)

        pos = event.position().toPoint()
        index = self.indexAt(pos)

        if index.isValid():
            rect = self.visualRect(index)

            # Determine drop position (above, on, or below item)
            margin = 5
            if pos.y() - rect.top() < margin:
                # Above item
                self.dropIndicatorPosition = QAbstractItemView.DropIndicatorPosition.AboveItem
                self.dropIndicatorRect = QRect(rect.left(), rect.top(), rect.width(), 0)
            elif rect.bottom() - pos.y() < margin:
                # Below item
                self.dropIndicatorPosition = QAbstractItemView.DropIndicatorPosition.BelowItem
                self.dropIndicatorRect = QRect(rect.left(), rect.bottom(), rect.width(), 0)
            else:
                # On item
                self.dropIndicatorPosition = QAbstractItemView.DropIndicatorPosition.OnItem
                self.dropIndicatorRect = QRect(rect.left(), rect.top(), rect.width(), rect.height())
        else:
            # On empty space
            self.dropIndicatorPosition = QAbstractItemView.DropIndicatorPosition.OnViewport
            self.dropIndicatorRect = QRect()

        # Force a repaint to update the indicator
        self.viewport().update()

    def resizeEvent(self, event):
        """
        Instead of just resizing editor using itemDelegate's updateEditorGeometry method, I am resizing the editor here
        because this seems faster, although I am not able to disable the resizing behaviour of updateEditorGeometry
        method
        """
        super().resizeEvent(event)
        if self.current_editor:
            self.current_editor.setFixedWidth(self.viewport().width() - self.editor_width_reduction)

    def mousePressEvent(self, e):
        """
        This method modifies the behaviour of ListView according to which items are selected when mouse is pressed on
        them.
        Items are selected in TaskList when mouse is clicked (pressed and released) on them
        """
        if e.button() == Qt.LeftButton or self._isSelectRightClickedRow:
            return QListView.mousePressEvent(self, e)

        # to select the row on which mouse is clicked
        index = self.indexAt(e.pos())
        if index.isValid():
            self._mousePressedOnItem = True
        else:
            self._mousePressedOnItem = False

        QWidget.mousePressEvent(self, e)

    def mouseReleaseEvent(self, e):
        """
        This method modifies the behaviour of ListView according to which items are selected when mouse is pressed on
        them.
        Items are selected in TaskList when mouse is clicked (pressed and released) on them
        """
        # I don't know if I have to keep the below two lines
        QListView.mouseReleaseEvent(self, e)
        self.updateSelectedRows()

        # to select the row on which mouse is clicked
        if self._mousePressedOnItem:
            index = self.indexAt(e.pos())
            if index.isValid():
                self._setPressedRow(index.row())
                # self.updateSelectedRows()

        self._mousePressedOnItem = False
        super().mouseReleaseEvent(e)

    def dropEvent(self, e):
        """
        This method is called when an item is dropped onto a TaskList. This will go through a while loop till it finds
        TaskView class's object and then set the pressed row of both todoTasksList and completedTasksList to -1. This
        is done to overcome bugs in the original code in qfluentwidgets where the pressed row was not getting reset
        when an item was dropped.
        """
        # Clear drop indicator before processing the drop
        self.dropIndicatorRect = QRect()
        self.viewport().update()

        parent_view = self.parentWidget()
        while parent_view is not None:
            if isinstance(parent_view, Ui_TaskView):  # using Ui_TaskView because view.subinterfaces.tasks_view.TaskList
                # is a child class of Ui_TaskView and it cannot be imported here due to circular import

                parent_view.todoTasksList._setPressedRow(-1)
                parent_view.completedTasksList._setPressedRow(-1)
                parent_view.todoTasksList._setHoverRow(-1)
                parent_view.completedTasksList._setHoverRow(-1)
                parent_view.todoTasksList.viewport().update()
                parent_view.completedTasksList.viewport().update()
                break
            parent_view = parent_view.parentWidget()
        super().dropEvent(e)

    def mouseMoveEvent(self, e):
        """
        This method is called when mouse is moved over the TaskList. This will set the hover row of the delegate to the
        row over which mouse is hovering. This is done because in qfluentwidgets if mouse is moved away from an already
        hovered row to empty space of TaskList such that it doesn't cross any other row, the hovered row is not reset

        Also for the same reason self.entered signal has been disconnected in __init__ method
        """

        index = self.indexAt(e.pos())
        new_hover_row = index.row() if index.isValid() else -1
        if new_hover_row != self.delegate.hoverRow:
            self._setHoverRow(new_hover_row)
        super().mouseMoveEvent(e)

    def _setHoverRow(self, row: int):
        delegate = self.itemDelegate()
        if isinstance(delegate, ListItemDelegate):
            delegate.setHoverRow(row)
            self.viewport().update()
