from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QAbstractItemView, QListView, QProxyStyle, QWidget
from qfluentwidgets import ListItemDelegate, ListView, isDarkTheme

from prefabs.taskListItemDelegate import TaskListItemDelegate
from ui_py.ui_tasks_list_view import Ui_TaskView


# from: https://www.qtcentre.org/threads/35443-Customize-drop-indicator-in-QTreeView?p=167572#post167572
class TaskListStyle(QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget=None):
        if element == QProxyStyle.PE_IndicatorItemViewItemDrop:
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing, True)
            pen = QPen(QColor(255, 255, 255), 1) if isDarkTheme() else QPen(QColor(0, 0, 0), 1)
            painter.setPen(pen)
            if option.rect.height() == 0:
                # Draw a line drop indicator
                painter.drawLine(option.rect.left(), option.rect.top(), option.rect.right(), option.rect.top())
            else:
                # Draw a rounded rectangle if rect has height
                painter.drawRoundedRect(option.rect, 5, 5)  # same radius as indicator in list_view.qss at
                # https://github.com/zhiyiYo/PyQt-Fluent-Widgets/blob/2b3e9636556dd8ca8e9e9b5ccccbf5b56afa07e9/qfluentwidgets/_rc/qss/dark/list_view.qss#L26
            painter.restore()
        else:
            super().drawPrimitive(element, option, painter, widget)


class TaskList(ListView):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAutoScroll(True)
        self.setStyle(TaskListStyle())

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.current_editor = None

        self._mousePressedOnItem = False

        self.entered.disconnect()  # see mouseMoveEvent method's docstring

        self.setItemDelegate(TaskListItemDelegate(self))

        self.editor_width_reduction = 5  # the same number in TaskListItemDelegate's updateEditorGeometry method

        # Track drag operations to handle failed drops
        self._dragInProgress = False
        self._draggedIndexes = []

    def paintEvent(self, event) -> None:
        # Delete all buttons when there are no items in the model
        if self.model() and self.model().rowCount() == 0:
            delegate = self.itemDelegate()
            if hasattr(delegate, "deleteAllButtons"):
                delegate.deleteAllButtons()

        super().paintEvent(event)

    def startDrag(self, supportedActions) -> None:
        """
        Override startDrag to track drag operations and handle failed drops properly
        """
        # Store the indexes being dragged
        self._draggedIndexes = self.selectedIndexes()
        self._dragInProgress = True

        # Call the parent implementation to start the drag
        super().startDrag(supportedActions)

        # After drag completes, check if it was successful
        # If we reach here and _dragInProgress is still True, it means the drag failed
        if self._dragInProgress:
            self._handleFailedDrag()

        # Reset drag state
        self._dragInProgress = False
        self._draggedIndexes = []

    def _handleFailedDrag(self) -> None:
        """
        Handle the case where a drag operation failed (e.g., dropped on invalid target)
        This ensures the task doesn't disappear from the original list
        """
        # Cancel the drag operation in the model
        if self.model() and hasattr(self.model(), "cancelDrag"):
            self.model().cancelDrag()

    def dragEnterEvent(self, event) -> None:
        """
        Override dragEnterEvent to handle drag operations properly
        """
        super().dragEnterEvent(event)
        # Accept the drag if it contains our mime type
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
        else:
            event.ignore()

    def resizeEvent(self, event) -> None:
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

    def mouseReleaseEvent(self, e) -> None:
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

    def dropEvent(self, e) -> None:
        """
        This method is called when an item is dropped onto a TaskList. This will go through a while loop till it finds
        TaskView class's object and then set the pressed row of both todoTasksList and completedTasksList to -1. This
        is done to overcome bugs in the original code in qfluentwidgets where the pressed row was not getting reset
        when an item was dropped.
        """
        # Mark drag as successful if this is our own drag operation
        if self._dragInProgress:
            self._dragInProgress = False

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

                # Also mark drag as successful for both task lists to handle cross-list drops
                parent_view.todoTasksList._dragInProgress = False
                parent_view.completedTasksList._dragInProgress = False

                # Cancel any pending drag operations in the models
                if hasattr(parent_view.todoTasksList.model(), "cancelDrag"):
                    parent_view.todoTasksList.model().cancelDrag()
                if hasattr(parent_view.completedTasksList.model(), "cancelDrag"):
                    parent_view.completedTasksList.model().cancelDrag()
                break
            parent_view = parent_view.parentWidget()
        super().dropEvent(e)

    def mouseMoveEvent(self, e) -> None:
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

    def _setHoverRow(self, row: int) -> None:
        delegate = self.itemDelegate()
        if isinstance(delegate, ListItemDelegate):
            delegate.setHoverRow(row)
            self.viewport().update()
