from typing import List, Optional, Union

from loguru import logger
from PySide6.QtCore import (
    QAbstractItemModel,
    QByteArray,
    QDataStream,
    QIODevice,
    QMimeData,
    QModelIndex,
    Qt,
    Signal,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QWidget
from qfluentwidgets import FluentIcon
from sqlalchemy import update

from constants import InvalidTaskDrop
from models.config import AppSettings
from models.db_tables import Task, TaskType
from models.workspace_lookup import WorkspaceLookup
from utils.db_utils import get_session


class TaskNode:
    """
    Node class representing a task in a tree structure.
    A task can have subtasks, but subtasks cannot have their own subtasks.
    """

    def __init__(
        self,
        task_id: int,
        task_name: str = "",
        task_position: int = 0,
        elapsed_time: int = 0,
        target_time: int = 0,
        icon: FluentIcon = None,
        parent: Optional["TaskNode"] = None,
        is_expanded: bool = False,
    ) -> None:
        self.task_id: int = task_id
        self.task_name: str = task_name
        self.task_position: int = task_position
        self.elapsed_time: int = elapsed_time
        self.target_time: int = target_time
        self.icon = icon
        self.is_expanded: bool = is_expanded

        self.parent_node: Optional["TaskNode"] = parent
        self.children: List["TaskNode"] = []

        if parent is not None:
            parent.add_child(self)

    def add_child(self, child: "TaskNode") -> None:
        if child not in self.children:
            self.children.append(child)
            child.parent_node = self

    def remove_child(self, child: "TaskNode") -> None:
        if child in self.children:
            self.children.remove(child)
            child.parent_node = None

    def child_count(self) -> int:
        return len(self.children)

    def child_at(self, index: int) -> Optional["TaskNode"]:
        if 0 <= index < len(self.children):
            return self.children[index]
        return None

    def row(self) -> int:
        if self.parent_node is not None:
            return self.parent_node.children.index(self)
        return 0

    def is_root(self) -> bool:
        return self.parent_node is None

    def is_leaf(self) -> bool:
        return len(self.children) == 0

    def can_have_children(self) -> bool:
        return self.is_root()

    def set_expanded(self, expanded: bool) -> None:
        self.is_expanded = expanded


class TaskListModel(QAbstractItemModel):
    IDRole: Qt.ItemDataRole = Qt.ItemDataRole.UserRole + 1
    IconRole: Qt.ItemDataRole = Qt.ItemDataRole.UserRole + 3
    ElapsedTimeRole: Qt.ItemDataRole = Qt.ItemDataRole.UserRole + 5
    TargetTimeRole: Qt.ItemDataRole = Qt.ItemDataRole.UserRole + 7
    IsExpandedRole: Qt.ItemDataRole = Qt.ItemDataRole.UserRole + 9

    taskDeletedSignal: Signal = Signal(int)  # task_id
    taskAddedSignal: Signal = Signal(int)  # task_id
    taskMovedSignal: Signal = Signal(int, TaskType)  # task_id and TaskType
    currentTaskChangedSignal: Signal = Signal(int)  # task_id
    invalidTaskDropSignal: Signal = Signal(InvalidTaskDrop)

    def __init__(self, task_type: TaskType, parent: Optional[QWidget] = None) -> None:  # noqa: F821
        super().__init__(parent)
        self.task_type: TaskType = task_type
        self.current_task_id: Optional[int] = None
        self.root_nodes: List[TaskNode] = []  # List of root task nodes
        self._dragInProgress: bool = False  # Track if we're in a drag operation
        self.load_data()

    def setCurrentTaskID(self, id: int) -> None:
        self.current_task_id = id
        self.currentTaskChangedSignal.emit(id)

    def currentTaskID(self) -> Optional[int]:
        return self.current_task_id

    def load_data(self) -> None:
        current_workspace_id = WorkspaceLookup.get_current_workspace_id()
        self.root_nodes = []

        with get_session(is_read_only=True) as session:
            tasks = (
                session.query(Task)
                .filter(Task.task_type == self.task_type)
                .filter(Task.workspace_id == current_workspace_id)
                .filter(Task.is_parent_task)
                .order_by(Task.task_position)
                .all()
            )

            # Create root nodes (main tasks)
            for task in tasks:
                node = TaskNode(
                    task_id=task.id,
                    task_name=task.task_name,
                    task_position=task.task_position,
                    elapsed_time=task.elapsed_time,
                    target_time=task.target_time,
                    icon=FluentIcon.PLAY if self.task_type == TaskType.TODO else FluentIcon.MENU,
                    is_expanded=task.is_expanded,
                )
                self.root_nodes.append(node)

            subtasks = (
                session.query(Task)
                .filter(Task.task_type == self.task_type)
                .filter(Task.workspace_id == current_workspace_id)
                .filter(~Task.is_parent_task)
                .order_by(Task.task_position)
                .all()
            )

            # create leaf nodes (subtasks)
            for subtask in subtasks:
                node = TaskNode(
                    task_id=subtask.id,
                    task_name=subtask.task_name,
                    task_position=subtask.task_position,
                    elapsed_time=subtask.elapsed_time,
                    target_time=subtask.target_time,
                    icon=FluentIcon.PLAY if self.task_type == TaskType.TODO else FluentIcon.MENU,
                    is_expanded=False,
                )
                parent_node = next((n for n in self.root_nodes if n.task_id == subtask.parent_task_id), None)
                if parent_node:
                    parent_node.add_child(node)

        self.layoutChanged.emit()

    def get_node(self, index: QModelIndex) -> Optional[TaskNode]:
        """Get the node associated with a given index"""
        if not index.isValid():
            return None

        return index.internalPointer()

    def index(self, row: int, column: int = 0, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        if not parent.isValid():
            # Top-level item (root task)
            if 0 <= row < len(self.root_nodes):
                return self.createIndex(row, column, self.root_nodes[row])
        else:
            # Child item (subtask)
            parent_node = self.get_node(parent)
            if parent_node and 0 <= row < parent_node.child_count():
                return self.createIndex(row, column, parent_node.child_at(row))

        return QModelIndex()

    def parent(self, child: QModelIndex) -> QModelIndex:
        if not child.isValid():
            return QModelIndex()

        child_node = self.get_node(child)
        if child_node is None or child_node.is_root():
            return QModelIndex()

        parent_node = child_node.parent_node
        if parent_node is None:
            return QModelIndex()

        # Find the row of the parent node
        parent_row = self.root_nodes.index(parent_node)
        return self.createIndex(parent_row, 0, parent_node)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        if not parent.isValid():
            # Root level
            return len(self.root_nodes)

        parent_node = self.get_node(parent)
        if parent_node:
            return parent_node.child_count()

        return 0

    def data(
        self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole
    ) -> Optional[Union[str, int, QColor, FluentIcon, bool]]:
        if not index.isValid():
            return None

        node = self.get_node(index)
        if node is None:
            return None

        if role == Qt.ItemDataRole.DisplayRole:
            return node.task_name
        elif role == self.ElapsedTimeRole:
            return node.elapsed_time
        elif role == self.TargetTimeRole:
            return node.target_time
        elif role == self.IDRole:
            return node.task_id
        elif role == self.IconRole:
            return node.icon
        elif role == Qt.ItemDataRole.BackgroundRole:
            if self.current_task_id == node.task_id:
                theme_color: QColor = AppSettings.get(AppSettings, AppSettings.themeColor)
                return theme_color
            else:
                return None
        elif role == self.IsExpandedRole:
            return node.is_expanded

        return None

    def setData(
        self,
        index: QModelIndex,
        value: Union[str, int, FluentIcon, bool],
        role: int = Qt.ItemDataRole.DisplayRole,
        update_db: bool = True,
    ) -> bool:
        if not index.isValid():
            return False

        node = self.get_node(index)
        if node is None:
            return False

        if role == Qt.ItemDataRole.DisplayRole:
            task_name = value.strip()
            if task_name:
                node.task_name = task_name
                if update_db:
                    self.update_db()
                self.dataChanged.emit(index, index, [Qt.ItemDataRole.DisplayRole])
                return True
        elif role == self.ElapsedTimeRole:
            node.elapsed_time = value
            if update_db:
                self.update_db()
            self.dataChanged.emit(index, index, [self.ElapsedTimeRole])
            return True
        elif role == self.TargetTimeRole:
            node.target_time = value
            if update_db:
                self.update_db()
            self.dataChanged.emit(index, index, [self.TargetTimeRole])
            return True
        elif role == self.IconRole:
            node.icon = value
            self.dataChanged.emit(index, index, [self.IconRole])
            return True
        elif role == self.IsExpandedRole:
            node.is_expanded = value
            self.dataChanged.emit(index, index, [self.IsExpandedRole])
            self.layoutChanged.emit()

        return False

    def revert(self) -> None:
        self.load_data()
        return super().revert()

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1

    def supportedDropActions(self) -> Qt.DropAction:
        return Qt.DropAction.MoveAction

    def mimeData(self, indexes: List[QModelIndex]) -> QMimeData:
        # Set drag in progress flag
        self._dragInProgress = True

        # First update the elapsed time for the task before drag starts
        if self.task_type == TaskType.TODO and self.current_task_id is not None:
            # Update the database with the current elapsed time to avoid losing time during drag
            current_node = self.getTaskNodeById(self.current_task_id)
            if current_node is not None:
                current_index = self.getIndexByNode(current_node)
                if current_index.isValid():
                    self.setData(current_index, current_node.elapsed_time, self.ElapsedTimeRole, update_db=True)

        mime_data = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.WriteOnly)

        # Store nodes being dragged
        nodes_being_dragged = []
        for index in indexes:
            if index.isValid():
                node = self.get_node(index)
                if node:
                    nodes_being_dragged.append(node)
                    logger.warning(f"preparing to drag node: {node}")
                    row = node.row() if not node.is_root() else self.root_nodes.index(node)
                    stream.writeInt32(row)
                    stream.writeInt32(node.task_id)
                    stream.writeQString(node.task_name)
                    stream.writeInt64(node.elapsed_time)
                    stream.writeInt64(node.target_time)
                    stream.writeBool(node.is_root())
                    # parent of task before dragging
                    parent_task_id = node.parent_node.task_id if node.parent_node else -1
                    stream.writeInt32(parent_task_id)
                    stream.writeBool(node.is_expanded)

        logger.debug(f"Dragging from task type: {self.task_type}")
        logger.debug(f"Nodes being dragged: {[node.task_id for node in nodes_being_dragged]}")

        mime_data.setData("application/x-qabstractitemmodeldatalist", encoded_data)
        return mime_data

    def dropMimeData(self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex) -> bool:
        # Clear drag in progress flag since we're handling the drop
        self._dragInProgress = False
        logger.debug(f"row: {row}, column: {column}, parent: {parent}, action: {action}")

        if not data.hasFormat("application/x-qabstractitemmodeldatalist"):
            return False

        encoded_data = data.data("application/x-qabstractitemmodeldatalist")
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.ReadOnly)

        # Read all task data from the stream
        # Only one task can be dragged at once
        while not stream.atEnd():
            # have to read all this because QDataStream is sequential access only
            _ = stream.readInt32()
            _ = stream.readInt32()
            _ = stream.readQString()
            _ = stream.readInt64()
            _ = stream.readInt64()
            is_root = stream.readBool()
            _ = stream.readInt32()  # parent task id of the task before it was dragged
            _ = stream.readBool()

            if is_root:
                return self._handleDroppedRootNode(data, action, row, column, parent)
            else:
                return self._handleDroppedChildNode(data, action, row, column, parent)

    def _handleDroppedRootNode(
        self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex
    ) -> bool:
        """
        logic followed:
        if parent task
            if dropped within same list
                valid drop; place it at new location
            elif dropped to other list
                valid drop; place at new location and change task list type of the parent task and all its children
            elif dropped at the place of a subtask
                invalid drop, return to previous location
        """
        encoded_data = data.data("application/x-qabstractitemmodeldatalist")
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.ReadOnly)

        drop_nodes = []
        task_ids = []

        # Use the parent index row when dropping directly onto an item
        if parent.isValid():
            self.invalidTaskDropSignal.emit(InvalidTaskDrop.DROPPED_PARENT_TASK_AT_CHILD_LEVEL)
            logger.debug("Can't drop parent task within another parent task")
            return False
        else:
            if row == -1:
                drop_position = len(self.root_nodes)
            else:
                drop_position = row

        # Only one task can be dragged at once
        while not stream.atEnd():
            _source_row = stream.readInt32()
            task_id = stream.readInt32()
            task_ids.append(task_id)
            task_name = stream.readQString()
            elapsed_time = stream.readInt64()
            target_time = stream.readInt64()
            _is_root = stream.readBool()
            _original_parent_task_id = stream.readInt32()  # parent task id of the task before it was dragged
            # will have -1 since this is a root node
            is_expanded = stream.readBool()

            # For the current task, check if we need to update the elapsed time from in-memory cache
            if self.task_type == TaskType.TODO and self.current_task_id == task_id:
                existing_node = self.getTaskNodeById(task_id)
                if existing_node:
                    elapsed_time = existing_node.elapsed_time
                    logger.debug(f"Updated elapsed time for current task during drop: {elapsed_time}")

            node = TaskNode(
                task_id=task_id,
                task_name=task_name,
                task_position=0,  # Will be set later
                elapsed_time=elapsed_time,
                target_time=target_time,
                icon=FluentIcon.PLAY if self.task_type == TaskType.TODO else FluentIcon.MENU,
                is_expanded=is_expanded,
            )

            # have to read child tasks from database instead from in memory data structure as the task ids of
            # child tasks aren't being passed via mime data. Can't read from in memory data structure because
            # during cross-list drag and drop, the source list's data structure is not accessible.
            current_workspace_id = WorkspaceLookup.get_current_workspace_id()
            with get_session(is_read_only=True) as session:
                subtasks = (
                    session.query(Task)
                    .filter(Task.parent_task_id == task_id)
                    .filter(Task.workspace_id == current_workspace_id)
                    .filter(~Task.is_parent_task)
                    .order_by(Task.task_position)
                    .all()
                )

                # create child nodes
                for subtask in subtasks:
                    _child_node = TaskNode(
                        task_id=subtask.id,
                        task_name=subtask.task_name,
                        task_position=subtask.task_position,
                        elapsed_time=subtask.elapsed_time,
                        target_time=subtask.target_time,
                        icon=FluentIcon.PLAY if self.task_type == TaskType.TODO else FluentIcon.MENU,
                        parent=node,  # Set the new parent node
                        is_expanded=subtask.is_expanded,
                    )

            drop_nodes.append(node)

        # Find which nodes in our current model need to be removed (moved)
        nodes_to_remove = []
        for node in self.root_nodes:
            if node.task_id in task_ids:
                nodes_to_remove.append(node)

        node.task_position = drop_position
        logger.debug(f"Adjusted drop position after offset: {drop_position}")

        # Check if this is a drop in the exact same position
        if len(nodes_to_remove) == 1 and len(drop_nodes) == 1:
            original_pos = self.root_nodes.index(nodes_to_remove[0])
            if original_pos == drop_position:
                logger.debug(f"Node dropped at same position: {original_pos} -> {drop_position}")
                return False

        # inserting dropped task at new position
        self.beginInsertRows(QModelIndex(), drop_position, drop_position + len(drop_nodes) - 1)
        self.root_nodes = self.root_nodes[:drop_position] + drop_nodes + self.root_nodes[drop_position:]
        self.endInsertRows()

        # required when tasks are transferred from one task list to another
        # this same step happens in removeRows method but that method is not called
        # for the model into which the task was dropped, so it has to be performed here
        for i, node in enumerate(self.root_nodes):
            node.task_position = i

        # emit signals for moved nodes
        for node in drop_nodes:
            self.taskMovedSignal.emit(node.task_id, self.task_type)
            for subtask in node.children:
                self.taskMovedSignal.emit(subtask.task_id, self.task_type)

        self.update_db()

        # emit layoutChanged to notify the view of the changes
        self.layoutChanged.emit()

        logger.debug(f"Task type: {self.task_type}")
        logger.debug(f"Root nodes after drop: {[node.task_id for node in self.root_nodes]}")

        return True

    def _handleDroppedChildNode(
        self, data: QMimeData, action: Qt.DropAction, row: int, column: int, parent: QModelIndex
    ) -> bool:
        """
        if subtask
            if dropped within its own parent
                valid drop; place it at new location
            elif dropped at subtasks of another parent task
                invalid drop; return to previous location
            elif dropped at top level
                invalid drop; return to previous location

        """
        encoded_data = data.data("application/x-qabstractitemmodeldatalist")
        stream = QDataStream(encoded_data, QIODevice.OpenModeFlag.ReadOnly)

        drop_nodes = []
        task_ids = []
        if not parent.isValid():
            self.invalidTaskDropSignal.emit(InvalidTaskDrop.DROPPED_CHILD_TASK_AT_ROOT_LEVEL)
            logger.debug("Can't drop subtask at root level")
            return False

        droppedOnParentNode = self.get_node(parent)
        if not droppedOnParentNode:
            self.invalidTaskDropSignal.emit(InvalidTaskDrop.DROPPED_CHILD_TASK_AT_ROOT_LEVEL)
            logger.debug("Invalid parent node")
            return False

        existing_child = None
        while not stream.atEnd():
            _source_row = stream.readInt32()
            task_id = stream.readInt32()
            task_ids.append(task_id)
            _task_name = stream.readQString()
            _elapsed_time = stream.readInt64()
            _target_time = stream.readInt64()
            _is_root = stream.readBool()  # would be False as child node
            _original_parent_task_id = stream.readInt32()  # parent task id of the task before it was dragged
            _is_expanded = stream.readBool()

            droppedOnParentTaskId = droppedOnParentNode.task_id

            if droppedOnParentTaskId != _original_parent_task_id:
                self.invalidTaskDropSignal.emit(InvalidTaskDrop.DROPPED_CHILD_TASK_IN_ANOTHER_PARENT_TASK)
                logger.debug("Can't drop subtask within another parent task")
                return False
            else:  # dropped within its own parent, which is valid
                logger.debug(f"Reordering subtask {task_id} within parent {droppedOnParentTaskId}")

                # find existing child one and reorder it
                for child in droppedOnParentNode.children:
                    if child.task_id == task_id:
                        existing_child = child
                        break

                if not existing_child:
                    logger.debug(f"Could not find existing child with task_id {task_id}")
                    return False

                drop_nodes.append(existing_child)

        # Determine the drop position within the parent's children
        if row == -1:
            drop_position = len(droppedOnParentNode.children)
        else:
            drop_position = row

        existing_child.task_position = drop_position

        # Check if dropping at the same position
        if len(drop_nodes) == 1:
            original_pos = droppedOnParentNode.children.index(drop_nodes[0])
            if original_pos == drop_position:
                logger.debug(f"Child dropped at same position: {original_pos}")
                return False

        # insert child task at new position
        self.beginInsertRows(parent, drop_position, drop_position + len(drop_nodes) - 1)
        droppedOnParentNode.children = (
            droppedOnParentNode.children[:drop_position] + drop_nodes + droppedOnParentNode.children[drop_position:]
        )
        self.endInsertRows()

        self.update_db()

        logger.debug(f"Subtasks reordered within parent {droppedOnParentTaskId}")
        return True

    def update_db(self) -> None:
        """
        Update database using bulk update
        """
        current_workspace_id = WorkspaceLookup.get_current_workspace_id()

        # Collect all nodes for database update
        all_nodes = []
        for root_node in self.root_nodes:
            all_nodes.append(root_node)
            all_nodes.extend(root_node.children)

        with get_session() as session:
            session.execute(
                update(Task),
                [
                    {
                        "id": node.task_id,
                        "workspace_id": current_workspace_id,
                        "task_name": node.task_name,
                        "task_type": self.task_type,
                        "task_position": node.task_position,
                        "elapsed_time": node.elapsed_time,
                        "target_time": node.target_time,
                        "is_parent_task": node.is_root(),
                        "parent_task_id": node.parent_node.task_id if node.parent_node else None,
                        "is_expanded": node.is_expanded,
                    }
                    for node in all_nodes
                    if node.task_id is not None
                ],
            )

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsDropEnabled

        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsDragEnabled
            | Qt.ItemFlag.ItemIsDropEnabled
            | Qt.ItemFlag.ItemIsEditable
        )

    def mimeTypes(self) -> List[str]:
        return ["application/x-qabstractitemmodeldatalist"]

    def insertRow(self, row: int, parent: QModelIndex, task_name: str, task_type: TaskType = TaskType.TODO) -> bool:
        """
        Used to insert a new task in the list
        """
        self.beginInsertRows(parent, row, row)

        with get_session() as session:
            if parent.isValid():  # add subtask
                task = Task(
                    workspace_id=WorkspaceLookup.get_current_workspace_id(),
                    task_name=task_name,
                    task_type=task_type,
                    task_position=row,
                    is_parent_task=False,
                    parent_task_id=self.get_node(parent).task_id,
                    is_expanded=False,
                )
            else:  # add root task
                task = Task(
                    workspace_id=WorkspaceLookup.get_current_workspace_id(),
                    task_name=task_name,
                    task_type=task_type,
                    task_position=row,
                    is_expanded=True,
                )
            session.add(task)
            session.commit()
            new_id = task.id

        if parent.isValid():  # add subtask
            parent_node = self.get_node(parent)
            newChildNode = TaskNode(
                task_id=new_id,
                task_name=task_name,
                task_position=row,
                elapsed_time=0,
                target_time=0,
                icon=FluentIcon.PLAY if self.task_type == TaskType.TODO else FluentIcon.MENU,
                parent=parent_node,
                is_expanded=False,
            )
            logger.debug(f"Creating new subtask node: {newChildNode.task_id} under parent: {parent_node.task_id}")
            # TaskNode constructor already adds child to parent
        else:  # add root task
            newRootNode = TaskNode(
                task_id=new_id,
                task_name=task_name,
                task_position=row,
                elapsed_time=0,
                target_time=0,
                icon=FluentIcon.PLAY if self.task_type == TaskType.TODO else FluentIcon.MENU,
                is_expanded=True,
            )
            logger.debug(f"Creating new task node: {newRootNode.task_id}")
            self.root_nodes.insert(row, newRootNode)

        self.taskAddedSignal.emit(new_id)

        self.endInsertRows()
        self.layoutChanged.emit()
        return True

    def removeRows(self, row: int, count: int, parent: QModelIndex = QModelIndex()) -> bool:
        """
        Remove rows and save changes to db
        This method can be called by Qt during drag operations.
        """
        # If we're in a drag operation, don't actually remove the data
        # Let the visual removal happen but keep the data intact until drop completes
        # I had to implement this because when dragging and dropping tasks onto invalid drop targets, tasks
        # disappear on wayland
        if self._dragInProgress:
            logger.debug(f"Ignoring removeRows during drag operation for rows {row} to {row + count - 1}")
            return True

        if parent.isValid():
            # Removing subtasks
            parent_node = self.get_node(parent)
            if parent_node:
                self.beginRemoveRows(parent, row, row + count - 1)
                for i in range(count):
                    if row < len(parent_node.children):
                        parent_node.children.pop(row)
                self.endRemoveRows()

            # update task positions
            for i, node in enumerate(parent_node.children):
                node.task_position = i
        else:
            # Removing root tasks
            self.beginRemoveRows(parent, row, row + count - 1)
            for i in range(count):
                logger.debug(f"root_nodes: {[node.task_id for node in self.root_nodes]}")
                logger.debug(f"Removing node at row: {row}")
                if row < len(self.root_nodes):
                    del self.root_nodes[row]
                logger.debug(f"root_nodes: {[node.task_id for node in self.root_nodes]}")
            self.endRemoveRows()

            # Update task positions
            for i, node in enumerate(self.root_nodes):
                node.task_position = i

        self.update_db()
        self.layoutChanged.emit()
        return True

    def finishDrag(self) -> None:
        """
        Cancel an ongoing drag operation and ensure data consistency
        """
        if self._dragInProgress:
            logger.debug(f"Marking drag operation for task type: {self.task_type} as finished")
            self._dragInProgress = False

    def isDragInProgress(self) -> bool:
        """
        Check if a drag operation is currently in progress
        """
        return self._dragInProgress

    def deleteTask(self, row: int, parent: QModelIndex = QModelIndex()) -> bool:
        """
        Delete tasks
        """
        logger.debug(f"Deleting parent/child task at row: {row}")

        taskIDs: Optional[List[int]] = []  # stores task IDs to be deleted, multiple IDs as when parent task is
        # deleted, all its child tasks need to be deleted as well

        # if to be deleted task is a subtask
        if parent.isValid():
            parent_node = self.get_node(parent)
            if parent_node and row < len(parent_node.children):
                child_node = parent_node.children[row]
                taskIDs.append(child_node.task_id)

                # and it is the only child of the parent task, then set the parent's time equal to this last child's
                # time'
                if len(parent_node.children) == 1:
                    childTargetTime = child_node.target_time
                    childElapsedTime = child_node.elapsed_time
                    parent_index = self.getIndexByNode(parent_node)
                    self.setData(parent_index, childTargetTime, self.TargetTimeRole)
                    self.setData(parent_index, childElapsedTime, self.ElapsedTimeRole)
                    self.update_db()
                # else set the parent's time as sum of all its children except the to be deleted child
                else:
                    elapsedTime = 0
                    targetTime = 0
                    for child in parent_node.children:
                        if child != child_node:
                            elapsedTime += child.elapsed_time
                            targetTime += child.target_time
                    parent_index = self.getIndexByNode(parent_node)
                    self.setData(parent_index, targetTime, self.TargetTimeRole)
                    self.setData(parent_index, elapsedTime, self.ElapsedTimeRole)
                    self.update_db()
        else:
            # Deleting root task
            if row < len(self.root_nodes):
                taskIDs.append(self.root_nodes[row].task_id)
                for child in self.root_nodes[row].children:
                    taskIDs.insert(0, child.task_id)  # inserting child tasks before root task to
                    # prevent foreign key constraint violation when deleting root task

        if taskIDs is None:
            return False

        # delete from database
        with get_session() as session:
            # delete all child tasks first using bulk delete
            session.query(Task).filter(Task.id.in_(taskIDs[:-1])).delete(synchronize_session=False)
            # delete the parent task at last
            last_id = taskIDs[-1]
            task = session.query(Task).get(last_id)
            if task:
                session.delete(task)

        logger.debug(f"Deleting tasks with ID: {taskIDs}")
        self.removeRows(row, 1, parent)

        for taskID in taskIDs:
            self.taskDeletedSignal.emit(taskID)
        self.layoutChanged.emit()
        return True

    def setIconForTask(self, row: int, icon: FluentIcon) -> None:
        if row < len(self.root_nodes):
            self.root_nodes[row].icon = icon
            index = self.index(row, 0)
            self.dataChanged.emit(index, index, [self.IconRole])

    def getTaskNameById(self, task_id: int) -> Optional[str]:
        node = self.getTaskNodeById(task_id)
        return node.task_name if node else None

    def currentTaskIndex(self) -> Optional[QModelIndex]:
        node = self.getTaskNodeById(self.current_task_id)
        if node:
            return self.getIndexByNode(node)
        return None

    def getTaskNodeById(self, task_id: Optional[int]) -> Optional[TaskNode]:
        """Find a node by its task_id"""
        if task_id is None:
            return None

        for node in self.root_nodes:
            if node.task_id == task_id:
                return node
            # searching in children of root node
            for child in node.children:
                if child.task_id == task_id:
                    return child
        return None

    def getIndexByNode(self, node: TaskNode) -> QModelIndex:
        """Get the QModelIndex for a given node"""
        if node.is_root():
            row = self.root_nodes.index(node)
            return self.index(row, 0)
        else:
            parent_index = self.getIndexByNode(node.parent_node)
            row = node.row()
            return self.index(row, 0, parent_index)

    def getIndexByTaskId(self, task_id: int) -> QModelIndex:
        """Get the QModelIndex for a given task_id"""
        node = self.getTaskNodeById(task_id)
        if node:
            return self.getIndexByNode(node)
        return QModelIndex()
