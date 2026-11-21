from pathlib import Path
from sys import platform
from typing import Optional

from PySide6.QtCore import QModelIndex, QSize, Qt
from PySide6.QtWidgets import QAbstractItemView, QFileDialog, QWidget
from qfluentwidgets import (
    BodyLabel,
    FluentIcon,
    ListView,
    MessageBoxBase,
    PushButton,
    SearchLineEdit,
    SubtitleLabel,
    ToolTipFilter,
    ToolTipPosition,
)

from app_blocker.appBlockerBackend import AppKind, InstalledApp
from app_blocker.backendFactory import get_app_blocker_backend
from models.appPickerListModel import AppFilterProxyModel, AppPickerListModel, AppPickerModelItem
from prefabs.appPickerItemDelegate import AppPickerItemDelegate


class BlockAppDialog(MessageBoxBase):
    """
    For the app picker dialog in the app blocker view
    """

    def __init__(self, blocked_targets: set[str], parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.blocked_targets = blocked_targets

        self.titleLabel = SubtitleLabel("Add apps to block", self)
        self.searchEdit = SearchLineEdit(self)
        self.searchEdit.setPlaceholderText("Search apps")
        self.searchEdit.setClearButtonEnabled(True)

        self.hintLabel = BodyLabel("Select apps to block during focus sessions", self)

        self.appListModel = AppPickerListModel(self)
        self.appFilterModel = AppFilterProxyModel(self)
        self.appFilterModel.setSourceModel(self.appListModel)

        self.appListView = ListView(self)
        self.appListView.setObjectName("appPickerListView")
        self.appListView.setModel(self.appFilterModel)
        self.appListView.setItemDelegate(AppPickerItemDelegate(self.appListView))
        self.appListView.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.appListView.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.appListView.setMinimumSize(QSize(0, 320))

        self.browseButton = PushButton(FluentIcon.FOLDER_ADD, "Browse…", self)
        self.browseButton.setToolTip("Block an app by its executable path, if it is not in the list")
        self.browseButton.installEventFilter(ToolTipFilter(self.browseButton, 300, ToolTipPosition.BOTTOM))

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.searchEdit)
        self.viewLayout.addWidget(self.hintLabel)
        self.viewLayout.addWidget(self.appListView)
        self.viewLayout.addWidget(self.browseButton)

        self.yesButton.setText("Block")
        self.cancelButton.setText("Cancel")

        # 715 is the app window's minimum width (mainWindow.initWindow)
        dialog_width = min(max(420, int(parent.width() * 0.5)), 715) if parent else 420
        self.widget.setMinimumWidth(dialog_width)
        self.widget.setMinimumHeight(480)

        self.appListModel.populate(get_app_blocker_backend().list_installed_apps(), blocked_targets)

        self.searchEdit.textChanged.connect(self.onSearchTextChanged)
        self.appListView.clicked.connect(self.onItemClicked)
        self.browseButton.clicked.connect(self.onBrowseClicked)

        self.onCheckedChanged()

    def onSearchTextChanged(self, text: str) -> None:
        self.appFilterModel.set_filter(text)

    def onItemClicked(self, index: QModelIndex) -> None:
        item: Optional[AppPickerModelItem] = index.data(AppPickerListModel.AppRole)
        if item is None or item.already_blocked:
            return

        self.appListModel.toggle_checked(item)
        self.onCheckedChanged()

    def onBrowseClicked(self) -> None:
        # as per https://refspecs.linuxfoundation.org/FHS_3.0/fhs/ch04s04.html most user commands should live here
        # if it doesnt exist then fall back to home directory
        start_dir = str(Path.home())
        if platform == "linux":
            if Path("/usr/bin").is_dir():
                start_dir = "/usr/bin"

        path, _ = QFileDialog.getOpenFileName(self, "Choose an application", start_dir, "All files (*)")
        if not path:
            return

        # the backend matches path targets through their symlink-resolved absolute path, so store it resolved
        absolute_path = str(Path(path).resolve())
        if any(item.app.target == absolute_path for item in self.appListModel.items):
            return

        browsed_app = InstalledApp(
            app_id=absolute_path,
            app_name=Path(absolute_path).name,
            target=absolute_path,
            kind=AppKind.PATH,
        )

        # show the new item immediately even when a search filter is active
        self.searchEdit.clear()
        self.appListModel.add_checked_app(browsed_app, absolute_path in self.blocked_targets)
        self.onCheckedChanged()

    def onCheckedChanged(self) -> None:
        count = len(self.appListModel.checked_apps())
        self.yesButton.setDisabled(count == 0)
        self.yesButton.setText("Block" if count <= 1 else f"Block ({count})")

    def selected_apps(self) -> list[InstalledApp]:
        return self.appListModel.checked_apps()
