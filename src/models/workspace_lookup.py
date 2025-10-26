from typing import Optional

from models.db_tables import CurrentWorkspace, Workspace
from utils.db_utils import get_session


class WorkspaceLookup:
    @staticmethod
    def get_current_workspace_id() -> Optional[int]:
        with get_session(is_read_only=True) as session:
            current_workspace = session.query(CurrentWorkspace).first()
        return current_workspace.current_workspace_id if current_workspace else None

    @staticmethod
    def get_current_workspace() -> Optional[Workspace]:
        current_workspace_id = WorkspaceLookup.get_current_workspace_id()
        with get_session(is_read_only=True) as session:
            workspace = session.get(Workspace, current_workspace_id)
        return workspace
