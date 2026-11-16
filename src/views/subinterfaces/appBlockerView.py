from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QWidget
from qfluentwidgets import FluentIcon

from models.appListModel import AppListModel
from prefabs.appListItemDelegate import AppListItemDelegate
from ui_py.ui_app_blocker_view import Ui_AppBlockView


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
        pass
