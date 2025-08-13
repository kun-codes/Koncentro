from models.config import app_settings, workspace_specific_settings


class ConfigValues:
    BREAK_DURATION = workspace_specific_settings.get(workspace_specific_settings.break_duration)
    WORK_DURATION = workspace_specific_settings.get(workspace_specific_settings.work_duration)
    LONG_BREAK_DURATION = workspace_specific_settings.get(workspace_specific_settings.long_break_duration)
    WORK_INTERVALS = workspace_specific_settings.get(workspace_specific_settings.work_intervals)
    AUTOSTART_WORK = workspace_specific_settings.get(workspace_specific_settings.autostart_work)
    AUTOSTART_BREAK = workspace_specific_settings.get(workspace_specific_settings.autostart_break)
    ENABLE_WEBSITE_BLOCKER = workspace_specific_settings.get(workspace_specific_settings.enable_website_blocker)
    PROXY_PORT = app_settings.get(app_settings.proxy_port)
    CHECK_FOR_UPDATES_ON_START = app_settings.get(app_settings.check_for_updates_on_start)
    HAS_COMPLETED_TASK_VIEW_TUTORIAL = app_settings.get(app_settings.has_completed_task_view_tutorial)
    HAS_COMPLETED_POMODORO_VIEW_TUTORIAL = app_settings.get(app_settings.has_completed_pomodoro_view_tutorial)
    HAS_COMPLETED_WEBSITE_BLOCKER_VIEW_TUTORIAL = app_settings.get(
        app_settings.has_completed_website_blocker_view_tutorial
    )
    HAS_COMPLETED_WORKSPACE_MANAGER_DIALOG_TUTORIAL = app_settings.get(
        app_settings.has_completed_workspace_manager_dialog_tutorial
    )
    SHOULD_MINIMIZE_TO_TRAY = app_settings.get(app_settings.should_minimize_to_tray)
