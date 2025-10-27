from typing import Optional

from models.dbTables import Task
from utils.db_utils import get_session


class TaskLookup:
    @staticmethod
    def get_elapsed_time(task_id: int) -> Optional[int]:
        with get_session(is_read_only=True) as session:
            task = session.get(Task, task_id)
        return task.elapsed_time if task else None

    @staticmethod
    def get_target_time(task_id: int) -> Optional[int]:
        with get_session(is_read_only=True) as session:
            task = session.get(Task, task_id)
        return task.target_time if task else None
