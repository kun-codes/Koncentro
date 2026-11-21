from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QWidget
from qfluentwidgets import FluentIcon, InfoBar, InfoBarPosition

from models.appListModel import AppListModel
from models.dbTables import BlocklistApp
from models.workspaceLookup import WorkspaceLookup
from prefabs.appListItemDelegate import AppListItemDelegate
from ui_py.ui_app_blocker_view import Ui_AppBlockView
from views.dialogs.blockAppDialog import BlockAppDialog


class AppBlockerView(Ui_AppBlockView, QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)

        self.initWidget()
        self.connectSignalsToSlots()

    def initWidget(self) -> None:
        self.addAppsButton.setIcon(FluentIcon.VPN)

        self.appListModel = AppListModel(self)
        self.appListModel.load_data()

        self.blockedAppsListView.setModel(self.appListModel)
        self.blockedAppsListView.setItemDelegate(AppListItemDelegate(self.blockedAppsListView))
        self.blockedAppsListView.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.blockedAppsListView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def onCurrentWorkspaceChanged(self) -> None:
        self.appListModel.load_data()

    def connectSignalsToSlots(self) -> None:
        self.addAppsButton.clicked.connect(self.addApps)

    def addApps(self) -> None:
        current_workspace_id = WorkspaceLookup.get_current_workspace_id()
        if not current_workspace_id:
            logger.debug("No current workspace selected, not opening the app picker")
            return

        blocked_targets = {app.app_path for app in self.appListModel.apps}
        dialog = BlockAppDialog(blocked_targets, self.window())

        if not dialog.exec():
            return

        for installed_app in dialog.selected_apps():
            blocklist_app = BlocklistApp(
                workspace_id=current_workspace_id,
                app_name=installed_app.app_name,
                app_path=installed_app.target,
                app_icon=installed_app.app_icon,
            )
            self.appListModel.add_app(blocklist_app)

        added_count = len(dialog.selected_apps())
        if added_count:
            InfoBar.success(
                "App added" if added_count == 1 else "Apps added",
                f"{'App' if added_count == 1 else f'{added_count} apps'}"
                f" {'was' if added_count == 1 else 'were'} added to the blocklist.",
                orient=Qt.Orientation.Vertical,
                isClosable=True,
                position=InfoBarPosition.TOP_RIGHT,
                duration=4000,
                parent=self,
            )
