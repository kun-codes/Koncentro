from models.dbTables import CurrentWorkspace, Task, TaskType, Version, Workspace
from utils.db_utils import get_session
from utils.getAppVersion import get_app_version


def checkValidDB() -> None:
    with get_session() as session:
        # Initialize version info if not exists
        # todo: make a upgrade db function too for future app versions
        if not session.query(Version).first():
            version = Version(app_version=get_app_version())
            session.add(version)
            session.commit()

        workspace = session.query(Workspace).first()
        # create a default workspace if none exists
        if not workspace:
            workspace = Workspace(workspace_name="Default Workspace")
            session.add(workspace)
            session.commit()

            # add some tasks too
            sample_tasks = [
                Task(
                    workspace_id=workspace.id,
                    task_name="🛍️ Create shopping list for the week",
                    task_type=TaskType.TODO,
                    task_position=0,
                    is_expanded=True,
                ),
                Task(
                    workspace_id=workspace.id,
                    task_name="☎️ Call family this weekend",
                    task_type=TaskType.TODO,
                    task_position=1,
                    is_expanded=True,
                ),
                Task(
                    workspace_id=workspace.id,
                    task_name="🏞️ Go for a nature walk",
                    task_type=TaskType.TODO,
                    task_position=2,
                    is_expanded=True,
                ),
                Task(
                    workspace_id=workspace.id,
                    task_name="🍽️ Prepare dinner for tonight",
                    task_type=TaskType.COMPLETED,
                    task_position=0,
                    is_expanded=False,
                ),
                Task(
                    workspace_id=workspace.id,
                    task_name="💌 Send thank you notes",
                    task_type=TaskType.COMPLETED,
                    task_position=1,
                    is_expanded=False,
                ),
                Task(
                    workspace_id=workspace.id,
                    task_name="📚 Finish reading current book",
                    task_type=TaskType.COMPLETED,
                    task_position=2,
                    is_expanded=False,
                ),
            ]
            session.add_all(sample_tasks)
            session.commit()

            # Add subtasks
            task_subtasks_mapping = {
                "🛍️ Create shopping list for the week": [
                    "Plan meals for the week",
                    "Check pantry for existing items",
                ],
                "☎️ Call family this weekend": [
                    "Call mom and dad on Saturday",
                    "Video chat with siblings",
                ],
                "🏞️ Go for a nature walk": [
                    "Choose a scenic walking trail",
                    "Pack water and snacks",
                ],
                "🍽️ Prepare dinner for tonight": [
                    "Select recipe and ingredients",
                    "Prep vegetables and seasonings",
                ],
                "💌 Send thank you notes": [
                    "Write personalized messages",
                    "Address and stamp envelopes",
                ],
                "📚 Finish reading current book": [
                    "Read remaining chapters",
                    "Take notes on key concepts",
                ],
            }

            # Create subtasks for each sample task
            for task in sample_tasks:
                if task.task_name in task_subtasks_mapping:
                    subtasks_list = task_subtasks_mapping[task.task_name]

                    for i, subtask_name in enumerate(subtasks_list):
                        subtask = Task(
                            workspace_id=workspace.id,
                            task_name=subtask_name,
                            task_type=task.task_type,
                            task_position=i,
                            is_parent_task=False,
                            parent_task_id=task.id,
                            is_expanded=False,
                        )
                        session.add(subtask)

            session.commit()

        # if application was closed while no workspace was selected, select the first workspace in the database
        # if database had no workspace to begin with then set default workspace as current database
        current_workspace = session.query(CurrentWorkspace).first()
        if not current_workspace:
            current_workspace = CurrentWorkspace(current_workspace_id=workspace.id)
            session.add(current_workspace)
            session.commit()
