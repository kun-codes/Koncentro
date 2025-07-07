from loguru import logger
from PySide6.QtCore import QAbstractListModel, QItemSelectionModel, QModelIndex, Qt, Signal

from models.db_tables import CurrentWorkspace, Workspace
from utils.db_utils import get_session


class WorkspaceListModel(QAbstractListModel):
    current_workspace_changed = Signal()
    current_workspace_deleted = Signal()

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.workspaces = []
        self.load_data()
        self.layoutChanged.connect(self.logList)
        self.selection_model: QItemSelectionModel = None

    def setSelectionModel(self, selection_model: QItemSelectionModel) -> None:
        self.selection_model = selection_model

    def load_data(self) -> None:
        with get_session(is_read_only=True) as session:
            self.workspaces = [
                {"id": workspace.id, "workspace_name": workspace.workspace_name}
                for workspace in session.query(Workspace).all()
            ]
        self.layoutChanged.emit()

    def data(self, index, role):
        if role == Qt.ItemDataRole.DisplayRole:
            return self.workspaces[index.row()]["workspace_name"]
        if role == Qt.ItemDataRole.DisplayRole:
            return self.workspaces[index.row()]["id"]

    def setData(self, index, value, role=Qt.EditRole) -> bool:
        """Update workspace name"""
        if role == Qt.EditRole:
            workspace_name = value.strip()
            if workspace_name:
                with get_session() as session:
                    workspace = session.get(Workspace, self.workspaces[index.row()]["id"])
                    workspace.workspace_name = workspace_name
                    session.commit()

                self.workspaces[index.row()]["workspace_name"] = workspace_name
                self.dataChanged.emit(index, index, [Qt.DisplayRole])
                return True
        return False

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return super().flags(index) | Qt.ItemIsEditable

    def rowCount(self, index=QModelIndex()):
        return len(self.workspaces)

    def add_workspace(self, workspace) -> None:
        with get_session() as session:
            session.add(workspace)
            session.commit()
            self.workspaces.append({"id": workspace.id, "workspace_name": workspace.workspace_name})
        self.layoutChanged.emit()

    # TODO: Implement update_workspace method

    def delete_workspace(self, index) -> None:
        if 0 <= index < len(self.workspaces):
            workspace_id = self.workspaces[index]["id"]  # workspace about to be deleted
            selected_workspace_id = self.get_current_workspace_id()
            with get_session() as session:
                workspace = session.get(Workspace, workspace_id)
                if workspace:
                    session.delete(workspace)
                    if workspace_id == selected_workspace_id:
                        self.current_workspace_deleted.emit()
            self.workspaces.pop(index)
            self.layoutChanged.emit()

    def set_current_workspace_preference(self) -> None:
        if self.selection_model:
            selected_index = self.selection_model.currentIndex()
            if selected_index.isValid():
                selected_workspace = self.workspaces[selected_index.row()]

                with get_session() as session:
                    previous_selected_workspace = session.query(CurrentWorkspace).first()
                    previous_selected_workspace_id = (
                        previous_selected_workspace.current_workspace_id if previous_selected_workspace else None
                    )
                    # make sure that only one record exists in current_workspace table
                    session.query(CurrentWorkspace).delete()
                    current_workspace = CurrentWorkspace(current_workspace_id=selected_workspace["id"])
                    session.add(current_workspace)

                self.load_data()

                current_workspace_id = session.query(CurrentWorkspace).first().current_workspace_id

                if previous_selected_workspace_id != current_workspace_id:
                    self.current_workspace_changed.emit()

    def get_current_workspace_id(self):
        with get_session(is_read_only=True) as session:
            current_workspace = session.query(CurrentWorkspace).first()
        return current_workspace.current_workspace_id if current_workspace else None

    def get_workspace_name_by_id(self, workspace_id):
        for workspace in self.workspaces:
            if workspace["id"] == workspace_id:
                return workspace["workspace_name"]
        return None

    def logList(self) -> None:
        logger.debug(f"Workspaces list in memory: {self.workspaces}")
