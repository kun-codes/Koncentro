from typing import Optional, Union

from PySide6.QtCore import QAbstractListModel, QModelIndex, QPersistentModelIndex, QSortFilterProxyModel, Qt
from PySide6.QtWidgets import QWidget

from app_blocker.appBlockerBackend import InstalledApp


class AppPickerModelItem:
    def __init__(self, app: InstalledApp, already_blocked: bool) -> None:
        self.app = app
        self.already_blocked = already_blocked
        self.checked = False


class AppPickerListModel(QAbstractListModel):
    AppRole: int = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.items: list[AppPickerModelItem] = []

    def populate(self, installed_apps: list[InstalledApp], blocked_targets: set[str]) -> None:
        self.beginResetModel()
        self.items = [
            AppPickerModelItem(app, app.target in blocked_targets)
            for app in sorted(installed_apps, key=lambda app: app.app_name.casefold())
        ]
        self.endResetModel()

    def add_checked_app(self, app: InstalledApp, already_blocked: bool = False) -> AppPickerModelItem:
        item = AppPickerModelItem(app, already_blocked)
        item.checked = not already_blocked
        row = len(self.items)
        self.beginInsertRows(QModelIndex(), row, row)
        self.items.append(item)
        self.endInsertRows()
        return item

    def toggle_checked(self, item: AppPickerModelItem) -> None:
        item.checked = not item.checked
        row = self.items.index(item)
        index = self.index(row, 0)
        # dataChanged (forwarded by the filter proxy) makes the view repaint only this row
        self.dataChanged.emit(index, index)

    def checked_apps(self) -> list[InstalledApp]:
        return [item.app for item in self.items if item.checked]

    def rowCount(self, parent: Union[QModelIndex, QPersistentModelIndex] = QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self.items)

    def data(
        self, index: Union[QModelIndex, QPersistentModelIndex], role: int = Qt.ItemDataRole.DisplayRole
    ) -> Optional[AppPickerModelItem]:
        if not index.isValid():
            return None
        if role == self.AppRole:
            return self.items[index.row()]
        return None


class AppFilterProxyModel(QSortFilterProxyModel):
    """Search filter over AppPickerListModel"""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._needle = ""

    def set_filter(self, text: str) -> None:
        self._needle = text.strip().casefold()
        self.invalidateFilter()

    def filterAcceptsRow(
        self, source_row: int, source_parent: Union[QModelIndex, QPersistentModelIndex] = QModelIndex()
    ) -> bool:
        if not self._needle:
            return True
        item = self.sourceModel().items[source_row]
        return self._needle in item.app.app_name.casefold() or self._needle in item.app.app_id.casefold()
