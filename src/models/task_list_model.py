from loguru import logger
from PySide6.QtCore import QAbstractListModel, QByteArray, QDataStream, QIODevice, QMimeData, QModelIndex, Qt, Signal
from PySide6.QtGui import QColor
from qfluentwidgets import FluentIcon
from sqlalchemy import update

from models.config import AppSettings
from models.db_tables import Task, TaskType
from models.workspace_lookup import WorkspaceLookup
from utils.db_utils import get_session


class TaskListModel(QAbstractListModel):
    IDRole = Qt.UserRole + 1
    IconRole = Qt.UserRole + 3
    ElapsedTimeRole = Qt.UserRole + 5
    TargetTimeRole = Qt.UserRole + 7

    taskDeletedSignal = Signal(int)  # task_id
    taskMovedSignal = Signal(int, TaskType)  # task_id and TaskType
    currentTaskChangedSignal = Signal(int)  # task_id

    def __init__(self, task_type: TaskType, parent=None) -> None:
        super().__init__(parent)
        self.task_type = task_type
        self.current_task_id = None
        self.tasks = []
        self._dragInProgress = False  # Track if we're in a drag operation
        self.load_data()

    def setCurrentTaskID(self, id) -> None:
        self.current_task_id = id
        self.currentTaskChangedSignal.emit(id)

    def currentTaskID(self):
        return self.current_task_id

    def load_data(self) -> None:
        current_workspace_id = WorkspaceLookup.get_current_workspace_id()
        self.tasks = []
        with get_session(is_read_only=True) as session:
            self.tasks = [
                {
                    "id": task.id,
                    "task_name": task.task_name,
                    "task_position": task.task_position,
                    "elapsed_time": task.elapsed_time,  # in ms
                    "target_time": task.target_time,  # in ms
                    "icon": FluentIcon.PLAY if self.task_type == TaskType.TODO else FluentIcon.MENU,
                }
                for task in session.query(Task)
                .filter(Task.task_type == self.task_type)
                .filter(Task.workspace_id == current_workspace_id)
                .order_by(Task.task_position)
                .all()
            ]
        self.layoutChanged.emit()

    def index(self, row, column=0, parent=QModelIndex()):
        return self.createIndex(row, column)

    def data(self, index, role=...):
        if role == Qt.DisplayRole:
            return self.tasks[index.row()]["task_name"]
        elif role == self.ElapsedTimeRole:
            task = self.tasks[index.row()]
            return task["elapsed_time"]
        elif role == self.TargetTimeRole:
            task = self.tasks[index.row()]
            return task["target_time"]
        elif role == self.IDRole:
            task = self.tasks[index.row()]
            return task["id"]
        elif role == self.IconRole:
            task = self.tasks[index.row()]
            return task["icon"]
        elif role == Qt.ItemDataRole.BackgroundRole:
            if self.current_task_id == self.tasks[index.row()]["id"]:
                theme_color: QColor = AppSettings.get(AppSettings, AppSettings.themeColor)
                return theme_color  # use theme color to color current task
            else:
                return None  # use default color according to dark/light theme

        return None

    def setData(self, index, value, role=..., update_db=True) -> bool:
        if role == Qt.DisplayRole:
            row = index.row()
            task_name = value.strip()
            if task_name:
                self.tasks[row]["task_name"] = task_name
                self.update_db()
                self.dataChanged.emit(index, index)
                return True
        elif role == self.ElapsedTimeRole:
            row = index.row()
            elapsed_time = value
            self.tasks[row]["elapsed_time"] = elapsed_time
            if update_db:
                self.update_db()
            self.dataChanged.emit(index, index)
            return True
        elif role == self.TargetTimeRole:
            row = index.row()
            target_time = value
            self.tasks[row]["target_time"] = target_time
            self.update_db()
            self.dataChanged.emit(index, index)
            return True
        elif role == self.IconRole:
            row = index.row()
            icon = value
            self.tasks[row]["icon"] = icon
            self.dataChanged.emit(index, index)
            return True
        return False

    def revert(self):
        self.load_data()
        return super().revert()

    def columnCount(self, parent) -> int:
        return 1

    def rowCount(self, parent=...):
        return len(self.tasks)

    def supportedDropActions(self):
        return Qt.DropAction.MoveAction

    def mimeData(self, indexes):
        # Set drag in progress flag
        self._dragInProgress = True

        # First update the elapsed time for the task before drag starts
        if self.task_type == TaskType.TODO and self.current_task_id is not None:
            # Update the database with the current elapsed time to avoid losing time during drag
            current_task_index = None
            for i, task in enumerate(self.tasks):
                if task["id"] == self.current_task_id:
                    current_task_index = self.index(i)
                    break

            if current_task_index is not None:
                self.setData(current_task_index, task["elapsed_time"], self.ElapsedTimeRole, update_db=True)

        mime_data = QMimeData()
        encoded_data = QByteArray()
        stream = QDataStream(encoded_data, QIODevice.WriteOnly)

        # Store rows being dragged
        rows_being_dragged = []
        for index in indexes:
            if index.isValid():
                row = index.row()
                rows_being_dragged.append(row)
                task_id = self.tasks[row]["id"]
                stream.writeInt32(row)
                stream.writeInt32(task_id)
                stream.writeQString(self.tasks[row]["task_name"])
                stream.writeInt64(self.tasks[row]["elapsed_time"])
                stream.writeInt64(self.tasks[row]["target_time"])

        # Store the indices being dragged in the mime data for later use
        task_ids_bytes = QByteArray()
        id_stream = QDataStream(task_ids_bytes, QIODevice.WriteOnly)
        for row in rows_being_dragged:
            id_stream.writeInt32(self.tasks[row]["id"])
        mime_data.setData("application/x-task-ids", task_ids_bytes)

        # Don't update task positions or database here - we'll do that in dropMimeData
        # This prevents prematurely marking tasks with position -1 when they might be
        # dropped back in the same position

        logger.debug(f"Dragging from task type: {self.task_type}")
        logger.debug(f"Rows being dragged: {rows_being_dragged}")

        mime_data.setData("application/x-qabstractitemmodeldatalist", encoded_data)
        return mime_data

    def dropMimeData(self, data, action, row, column, parent) -> bool:
        # Clear drag in progress flag since we're handling the drop
        self._dragInProgress = False

        if not data.hasFormat("application/x-qabstractitemmodeldatalist"):
            return False

        # Use the parent index row when dropping directly onto an item
        # This handles the case of dropping directly on another task
        if parent.isValid():
            # When dropping onto an item, we want to place the dragged item after it
            drop_position = parent.row() + 1
        else:
            # If row is -1, it means drop at the end or in an empty space
            if row == -1:
                drop_position = self.rowCount()
            else:
                drop_position = row

        encoded_data = data.data("application/x-qabstractitemmodeldatalist")
        stream = QDataStream(encoded_data, QIODevice.ReadOnly)

        # Create a list to store tasks being dropped
        drop_tasks = []
        task_ids = []

        # Read all task data from the stream
        while not stream.atEnd():
            _source_row = stream.readInt32()
            task_id = stream.readInt32()
            task_ids.append(task_id)
            task_name = stream.readQString()
            elapsed_time = stream.readInt64()
            target_time = stream.readInt64()

            # For the current task, check if we need to update the elapsed time from in-memory cache
            if self.task_type == TaskType.TODO and self.current_task_id == task_id:
                # Get the latest in-memory elapsed time value
                for existing_task in self.tasks:
                    if existing_task["id"] == task_id:
                        # Use the most up-to-date value
                        elapsed_time = existing_task["elapsed_time"]
                        logger.debug(f"Updated elapsed time for current task during drop: {elapsed_time}")
                        break

            drop_tasks.append(
                {
                    "id": task_id,
                    "task_name": task_name,
                    "task_position": None,  # Will be set later
                    "elapsed_time": elapsed_time,
                    "target_time": target_time,
                    "icon": FluentIcon.PLAY if self.task_type == TaskType.TODO else FluentIcon.MENU,
                }
            )

        # Find which tasks in our current model need to be removed (moved)
        task_id_to_original_row = {}
        for i, task in enumerate(self.tasks):
            if task["id"] in task_ids:
                task_id_to_original_row[task["id"]] = i

        # Adjust the drop position if we're moving tasks from above the drop position
        # This accounts for the "gap" created by removing items
        offset = 0
        for task_id, original_row in task_id_to_original_row.items():
            if original_row < drop_position:
                offset += 1

        drop_position -= offset
        logger.debug(f"Adjusted drop position after offset: {drop_position}")

        # Check if this is a drop in the exact same position
        if len(task_id_to_original_row) == 1 and len(drop_tasks) == 1:
            original_pos = task_id_to_original_row[drop_tasks[0]["id"]]
            # Check if we're dropping at the same position
            if original_pos == drop_position:
                logger.debug(f"Task dropped at same position: {original_pos} -> {drop_position}")
                return False  # No change needed, cancel the operation

        # Create a new list for tasks in their new order
        new_tasks = []

        # Create a copy of the tasks excluding the ones being moved
        filtered_tasks = [task for task in self.tasks if task["id"] not in task_ids]

        # Insert all tasks before the drop position
        for i in range(drop_position):
            if i >= len(filtered_tasks):
                break
            new_tasks.append(filtered_tasks[i])

        # Insert the dropped tasks at the drop position
        for task in drop_tasks:
            new_tasks.append(task)

        # Insert all remaining tasks after the drop position
        for i in range(drop_position, len(filtered_tasks)):
            new_tasks.append(filtered_tasks[i])

        # Set task positions
        for i, task in enumerate(new_tasks):
            task["task_position"] = i

        # Emit signals for moved tasks
        for task in drop_tasks:
            self.taskMovedSignal.emit(task["id"], self.task_type)

        # Replace the tasks list with our new ordered list
        self.beginResetModel()
        self.tasks = new_tasks
        self.endResetModel()

        # Update database
        self.update_db()

        # emit layoutChanged to notify the view of the changes
        self.layoutChanged.emit()

        logger.debug(f"Task type: {self.task_type}")
        logger.debug(f"Tasks after drop: {[t['id'] for t in self.tasks]}")

        return True

    def update_db(self) -> None:
        """
        updating db, using bulk insert
        https://docs.sqlalchemy.org/en/20/orm/queryguide/dml.html#orm-queryguide-bulk-update
        """
        current_workspace_id = WorkspaceLookup.get_current_workspace_id()
        with get_session() as session:
            session.execute(
                update(Task),
                [
                    {
                        "id": task["id"],
                        "workspace_id": current_workspace_id,
                        "task_name": task["task_name"],
                        "task_type": self.task_type,
                        "task_position": task["task_position"],
                        "elapsed_time": task["elapsed_time"],
                        "target_time": task["target_time"],
                    }
                    for task in self.tasks
                ],
            )

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled | Qt.ItemIsDropEnabled

        return (
            Qt.ItemFlag.ItemIsEnabled
            | Qt.ItemFlag.ItemIsSelectable
            | Qt.ItemFlag.ItemIsDragEnabled
            | Qt.ItemFlag.ItemIsDropEnabled
            | Qt.ItemFlag.ItemIsEditable
        )

    def mimeTypes(self):
        return ["application/x-qabstractitemmodeldatalist"]

    # TODO: Implement insertRows method
    # def insertRows(self, row, count, parent=None):
    #     self.beginInsertRows(parent, row, row + count - 1)
    #     encoded_data = self.mimeData([self.index(row)]).data("application/x-qabstractitemmodeldatalist")
    #     stream = QDataStream(encoded_data, QIODevice.ReadOnly)
    #     _row = stream.readInt32()
    #     task_id = stream.readInt32()
    #     task_name = stream.readQString()
    #     return True

    def insertRow(self, row, parent=QModelIndex(), task_name=None, task_type=TaskType.TODO) -> bool:
        """
        Used to insert a new task in the list
        """
        self.beginInsertRows(parent, row, row)

        with get_session() as session:
            task = Task(
                workspace_id=WorkspaceLookup.get_current_workspace_id(),
                task_name=task_name,
                task_type=task_type,
                task_position=row,
            )
            session.add(task)
            session.commit()
            new_id = task.id

        task_list_new_member = {
            "id": new_id,
            "task_name": task_name,
            "task_position": row,
            "elapsed_time": 0,
            "target_time": 0,
            "icon": FluentIcon.PLAY if self.task_type == TaskType.TODO else FluentIcon.MENU,
        }

        logger.debug(f"Task list new member: {task_list_new_member}")

        self.tasks.insert(row, task_list_new_member)
        self.endInsertRows()
        self.layoutChanged.emit()
        return True

    def removeRows(self, row, count, parent=...) -> bool:
        """
        remove rows but not delete from db
        This method can be called by Qt during drag operations.
        We should be careful not to permanently remove data during active drags.
        """
        # If we're in a drag operation, don't actually remove the data
        # Let the visual removal happen but keep the data intact until drop completes
        if self._dragInProgress:
            logger.debug(f"Ignoring removeRows during drag operation for rows {row} to {row + count - 1}")
            return True

        self.beginRemoveRows(parent, row, row + count - 1)
        for i in range(count):
            logger.debug(f"tasks: {self.tasks}")
            logger.debug(f"Removing task at row: {row}")
            del self.tasks[row]
            logger.debug(f"tasks: {self.tasks}")
        self.endRemoveRows()

        # Update task positions
        for i, task in enumerate(self.tasks):
            task["task_position"] = i

        self.layoutChanged.emit()
        return True

    def cancelDrag(self) -> None:
        """
        Cancel an ongoing drag operation and ensure data consistency
        """
        if self._dragInProgress:
            logger.debug(f"Cancelling drag operation for task type: {self.task_type}")
            self._dragInProgress = False
            # Force refresh to ensure view reflects actual data
            self.layoutChanged.emit()

    def isDragInProgress(self):
        """
        Check if a drag operation is currently in progress
        """
        return self._dragInProgress

    def deleteTask(self, row, parent=QModelIndex()) -> bool:
        """
        will remove rows as well as delete from database
        """
        logger.debug(f"Deleting task at row: {row}")
        task_id = self.tasks[row]["id"]
        # get index of row
        with get_session() as session:
            task = session.query(Task).get(task_id)
            session.delete(task)

        logger.debug(f"tasks: {self.tasks}")
        self.removeRows(row, 1, parent)

        for i, task in enumerate(self.tasks):
            task["task_position"] = i

        self.update_db()
        self.taskDeletedSignal.emit(task_id)
        self.layoutChanged.emit()
        return True

    def setIconForTask(self, row, icon) -> None:
        self.tasks[row]["icon"] = icon
        self.dataChanged.emit(self.index(row, 0), self.index(row, 0), [self.IconRole])

    def getTaskNameById(self, task_id):
        for task in self.tasks:
            if task["id"] == task_id:
                return task["task_name"]
        return None

    def currentTaskIndex(self):
        for task in self.tasks:
            if task["id"] == self.current_task_id:
                return self.index(task["task_position"], 0)
