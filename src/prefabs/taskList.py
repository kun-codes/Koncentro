from typing import Optional

from PySide6.QtCore import QModelIndex, Qt
from PySide6.QtGui import QColor, QDragEnterEvent, QDropEvent, QPainter, QPaintEvent, QPen, QResizeEvent
from PySide6.QtWidgets import QAbstractItemView, QProxyStyle, QStyle, QStyleOption, QWidget
from qfluentwidgets import TreeView, isDarkTheme

from models.task_list_model import TaskListModel
from prefabs.taskListItemDelegate import TaskListItemDelegate
from ui_py.ui_tasks_list_view import Ui_TaskView


# from: https://www.qtcentre.org/threads/35443-Customize-drop-indicator-in-QTreeView?p=167572#post167572
class TaskListStyle(QProxyStyle):
    def drawPrimitive(
        self,
        element: QStyle.PrimitiveElement,
        option: QStyleOption,
        painter: QPainter,
        widget: Optional[QWidget] = None,
    ) -> None:
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


class TaskList(TreeView):
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragDrop)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAutoScroll(True)
        self.setStyle(TaskListStyle())
        self.setHeaderHidden(True)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.current_editor = None

        self._mousePressedOnItem = False

        self.setItemDelegate(TaskListItemDelegate(self))

        self.editor_width_reduction = 5  # the same number in TaskListItemDelegate's updateEditorGeometry method

        # Track drag operations to handle failed drops
        self._dragInProgress = False

        self.expanded.connect(self._onItemExpanded)
        self.collapsed.connect(self._onItemCollapsed)

    def paintEvent(self, event: QPaintEvent) -> None:
        # Only call parent paintEvent - no button management needed
        super().paintEvent(event)

    def startDrag(self, supportedActions: Qt.DropAction) -> None:
        """
        Override startDrag to track drag operations and handle failed drops properly
        """
        self._dragInProgress = True

        # Call the parent implementation to start the drag
        super().startDrag(supportedActions)

        # After drag completes, check if it was successful
        # If we reach here and _dragInProgress is still True, it means the drag failed
        if self._dragInProgress:
            self._handleFailedDrag()

        # Reset drag state
        self._dragInProgress = False

    def _handleFailedDrag(self) -> None:
        """
        Handle the case where a drag operation failed (e.g., dropped on invalid target)
        This ensures the task doesn't disappear from the original list
        """
        # Cancel the drag operation in the model
        if self.model() and hasattr(self.model(), "finishDrag"):
            self.model().finishDrag()

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """
        Override dragEnterEvent to handle drag operations properly
        """
        super().dragEnterEvent(event)
        # Accept the drag if it contains our mime type
        if event.mimeData().hasFormat("application/x-qabstractitemmodeldatalist"):
            event.accept()
        else:
            event.ignore()

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Instead of just resizing editor using itemDelegate's updateEditorGeometry method, I am resizing the editor here
        because this seems faster, although I am not able to disable the resizing behaviour of updateEditorGeometry
        method
        """
        super().resizeEvent(event)
        if self.current_editor:
            self.current_editor.setFixedWidth(self.viewport().width() - self.editor_width_reduction)

    def dropEvent(self, e: QDropEvent) -> None:
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

                parent_view.todoTasksList.viewport().update()
                parent_view.completedTasksList.viewport().update()

                # Also mark drag as successful for both task lists to handle cross-list drops
                parent_view.todoTasksList._dragInProgress = False
                parent_view.completedTasksList._dragInProgress = False

                # Cancel any pending drag operations in the models
                if hasattr(parent_view.todoTasksList.model(), "finishDrag"):
                    parent_view.todoTasksList.model().finishDrag()
                if hasattr(parent_view.completedTasksList.model(), "finishDrag"):
                    parent_view.completedTasksList.model().finishDrag()
                break
            parent_view = parent_view.parentWidget()
        super().dropEvent(e)

    def setModel(self, model: TaskListModel) -> None:
        super().setModel(model)

        self._restoreExpansionStateOfAllTasks()

        model.taskMovedSignal.connect(self._restoreExpansionStateOfATask)
        model.taskAddedSignal.connect(self._restoreExpansionStateOfATask)

    def _restoreExpansionStateOfAllTasks(self) -> None:
        model: TaskListModel = self.model()
        if not model:
            return

        for row in range(model.rowCount()):
            index = model.index(row, 0)
            is_expanded = model.data(index, model.IsExpandedRole)
            if is_expanded:
                self.expand(index)
            else:
                self.collapse(index)

    def _restoreExpansionStateOfATask(self, task_id: int) -> None:
        model: TaskListModel = self.model()

        index = model.getIndexByTaskId(task_id)
        is_expanded = index.data(model.IsExpandedRole)
        if is_expanded:
            self.expand(index)
        else:
            self.collapse(index)

    def _onItemExpanded(self, index: QModelIndex) -> None:
        # Trigger a repaint to update button visibility after expansion
        self.viewport().update()

        model: TaskListModel = self.model()
        if model:
            model.setData(index, True, model.IsExpandedRole)

    def _onItemCollapsed(self, index: QModelIndex) -> None:
        # Trigger a repaint to update button visibility after collapse
        self.viewport().update()

        model: TaskListModel = self.model()
        if model:
            model.setData(index, False, model.IsExpandedRole)
