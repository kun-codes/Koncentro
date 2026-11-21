from bisect import bisect_right
from typing import List, Optional, Union

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QWidget

from models.dbTables import BlocklistApp
from models.workspaceLookup import WorkspaceLookup
from utils.db_utils import get_session


class AppItem:
    def __init__(self, app_id: int, app_name: str, app_path: str, app_icon: Optional[QPixmap] = None) -> None:
        self.app_id = app_id
        self.app_name = app_name
        self.app_path = app_path
        self.app_icon = app_icon


class AppListModel(QAbstractListModel):
    AppIDRole: Qt.ItemDataRole = Qt.ItemDataRole.UserRole + 1
    AppNameRole: Qt.ItemDataRole = Qt.ItemDataRole.UserRole + 3
    AppIconRole: Qt.ItemDataRole = Qt.ItemDataRole.UserRole + 5
    AppPathRole: Qt.ItemDataRole = Qt.ItemDataRole.UserRole + 7

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.apps: List[AppItem] = []

    def index(self, row: int, column: int = 0, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        if not self.hasIndex(row, column, parent):
            return QModelIndex()

        return self.createIndex(row, column, self.apps[row])

    def load_data(self) -> None:
        current_workspace_id = WorkspaceLookup.get_current_workspace_id()

        with get_session(is_read_only=True) as session:
            apps = (
                session.query(BlocklistApp)
                .filter(BlocklistApp.workspace_id == current_workspace_id)
                .order_by(BlocklistApp.app_name.collate("NOCASE"))
                .all()
            )

            self.apps = [
                AppItem(app_id=app.id, app_name=app.app_name, app_path=app.app_path, app_icon=app.app_icon)
                for app in apps
            ]

        self.layoutChanged.emit()

    def data(self, index: QModelIndex, role: Qt.ItemDataRole) -> Optional[Union[int, str, QPixmap]]:
        if not index.isValid():
            return None

        if role == self.AppIDRole:
            return self.apps[index.row()].app_id
        elif role == self.AppNameRole:
            return self.apps[index.row()].app_name
        elif role == self.AppPathRole:
            return self.apps[index.row()].app_path
        elif role == self.AppIconRole:
            return self.apps[index.row()].app_icon

    def rowCount(self, parent: Union[QModelIndex] = QModelIndex()) -> int:
        return len(self.apps)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1

    def parent(self, child: QModelIndex) -> QModelIndex:
        return QModelIndex()

    def _insertion_index(self, app_name: str) -> int:
        return bisect_right(self.apps, app_name.casefold(), key=lambda app: app.app_name.casefold())

    def add_app(self, app: BlocklistApp) -> None:
        with get_session() as session:
            session.add(app)
            session.commit()
            # capture values inside the session: commit() expires attributes and
            # closing the session detaches the instance, so app.id etc. cannot be
            # accessed afterwards
            new_item = AppItem(app.id, app.app_name, app.app_path, app.app_icon)

        lo = self._insertion_index(new_item.app_name)
        self.beginInsertRows(QModelIndex(), lo, lo)
        self.apps.insert(lo, new_item)
        self.endInsertRows()

    def delete_app(self, row: int) -> None:
        if not (0 <= row < len(self.apps)):
            return

        app_item = self.apps[row]
        with get_session() as session:
            app = session.get(BlocklistApp, app_item.app_id)
            if app:
                session.delete(app)

        self.beginRemoveRows(QModelIndex(), row, row)
        self.apps.pop(row)
        self.endRemoveRows()

    def edit_app(self, row: int, new_app: BlocklistApp) -> None:
        if not (0 <= row < len(self.apps)):
            return

        old_item = self.apps[row]

        with get_session() as session:
            app = session.get(BlocklistApp, old_item.app_id)
            if app is None:
                return
            app.app_name = new_app.app_name
            app.app_path = new_app.app_path
            app.app_icon = new_app.app_icon
            session.commit()

        updated_item = AppItem(old_item.app_id, new_app.app_name, new_app.app_path, new_app.app_icon)

        # if the app name is unchanged then just update in place and AppList will repaint the row
        if updated_item.app_name.casefold() == old_item.app_name.casefold():
            self.apps[row] = updated_item
            index = self.index(row, 0)
            self.dataChanged.emit(index, index, [self.AppNameRole, self.AppPathRole, self.AppIconRole])
            return

        # a name change means we have to remove the row and then add in a new one in a potentially different place
        self.beginRemoveRows(QModelIndex(), row, row)
        self.apps.pop(row)
        self.endRemoveRows()

        lo = self._insertion_index(updated_item.app_name)
        self.beginInsertRows(QModelIndex(), lo, lo)
        self.apps.insert(lo, updated_item)
        self.endInsertRows()
