from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QAbstractItemView, QWidget
from qfluentwidgets import FluentIcon, InfoBar, InfoBarPosition, ToolTipFilter, ToolTipPosition

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
        self.setupShortcuts()

    def initWidget(self) -> None:
        self.addAppsButton.setIcon(FluentIcon.VPN)

        self.deleteAppButton.setIcon(FluentIcon.DELETE)
        self.deleteAppButton.setEnabled(False)

        self.appListModel = AppListModel(self)
        self.appListModel.load_data()

        self.blockedAppsListView.setModel(self.appListModel)
        self.blockedAppsListView.setItemDelegate(AppListItemDelegate(self.blockedAppsListView))
        self.blockedAppsListView.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.blockedAppsListView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

    def onCurrentWorkspaceChanged(self) -> None:
        self.appListModel.load_data()
        self.onSelectionChanged()

    def setupShortcuts(self) -> None:
        self.addAppsShortcut = QShortcut(QKeySequence(Qt.KeyboardModifier.ControlModifier | Qt.Key.Key_N), self)
        self.addAppsShortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.addAppsShortcut.activated.connect(self.addAppsButton.click)

        self.deleteShortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        self.deleteShortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        self.deleteShortcut.activated.connect(self.deleteAppButton.click)

        self.addAppsButton.setToolTip(
            f"Add App ({self.addAppsShortcut.key().toString(QKeySequence.SequenceFormat.NativeText)})"
        )
        self.deleteAppButton.setToolTip(
            f"Delete App ({self.deleteShortcut.key().toString(QKeySequence.SequenceFormat.NativeText)})"
        )

        self.addAppsButton.installEventFilter(ToolTipFilter(self.addAppsButton, 300, ToolTipPosition.BOTTOM))
        self.deleteAppButton.installEventFilter(ToolTipFilter(self.deleteAppButton, 300, ToolTipPosition.BOTTOM))

    def connectSignalsToSlots(self) -> None:
        self.addAppsButton.clicked.connect(self.addApps)
        self.deleteAppButton.clicked.connect(self.deleteApp)
        self.blockedAppsListView.selectionModel().selectionChanged.connect(self.onSelectionChanged)

    def onSelectionChanged(self) -> None:
        self.deleteAppButton.setEnabled(self.blockedAppsListView.selectionModel().hasSelection())

    def deleteApp(self) -> None:
        index = self.blockedAppsListView.currentIndex()
        if not index.isValid():
            return
        self.appListModel.delete_app(index.row())

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
