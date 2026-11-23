from pathlib import Path
from sys import platform
from typing import Optional

from PySide6.QtCore import QModelIndex, QSize, Qt
from PySide6.QtGui import QKeyEvent, QKeySequence, QShortcut, QShowEvent
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
from models.appPickerListModel import AppFilterProxyModel, AppPickerListModel, AppPickerModelItem
from prefabs.appPickerItemDelegate import AppPickerItemDelegate
from utils.checkFlatpakSandbox import is_flatpak_sandbox


class BlockAppDialog(MessageBoxBase):
    """
    For the app picker dialog in the app blocker view
    """

    def __init__(
        self, blocked_targets: set[str], installed_apps: list[InstalledApp], parent: Optional[QWidget] = None
    ) -> None:
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
        self.browseShortcut = QShortcut(QKeySequence(QKeySequence.StandardKey.Open), self)
        self.browseShortcut.activated.connect(self.browseButton.click)
        self.browseButton.setToolTip(
            f"Block an app by its path ({self.browseShortcut.key().toString(QKeySequence.SequenceFormat.NativeText)})"
        )
        self.browseButton.installEventFilter(ToolTipFilter(self.browseButton, 300, ToolTipPosition.BOTTOM))

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.searchEdit)
        self.viewLayout.addWidget(self.hintLabel)
        self.viewLayout.addWidget(self.appListView)
        self.viewLayout.addWidget(self.browseButton)

        self.yesButton.setText("Block")
        self.cancelButton.setText("Cancel")

        self.yesButton.setToolTip(
            f"Add apps ({QKeySequence(Qt.Key.Key_Enter).toString(QKeySequence.SequenceFormat.NativeText)})"
        )
        self.yesButton.installEventFilter(ToolTipFilter(self.yesButton, 300, ToolTipPosition.TOP))
        self.cancelButton.setToolTip(
            f"Close dialog ({QKeySequence(Qt.Key.Key_Escape).toString(QKeySequence.SequenceFormat.NativeText)})"
        )
        self.cancelButton.installEventFilter(ToolTipFilter(self.cancelButton, 300, ToolTipPosition.TOP))

        # 715 is the app window's minimum width (mainWindow.initWindow)
        dialog_width = min(max(420, int(parent.width() * 0.5)), 715) if parent else 420
        self.widget.setMinimumWidth(dialog_width)
        self.widget.setMinimumHeight(480)

        self.appListModel.populate(installed_apps, blocked_targets)

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
        # the is_dir check is skipped under flatpak as the sandbox sees only the runtime's /usr/bin, the actual
        # dialog is opened host-side by xdg-desktop-portal, where /usr/bin refers to the host's directory
        # in the edge case when Koncentro is in a flatpak and the host linux distro doesnt have /usr/bin
        # most likely the file picker will fallback to the home directory
        start_dir = str(Path.home())
        if platform == "linux" and (is_flatpak_sandbox() or Path("/usr/bin").is_dir()):
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

    def showEvent(self, event: QShowEvent) -> None:
        super().showEvent(event)
        self.searchEdit.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in [Qt.Key.Key_Return, Qt.Key.Key_Enter] and self.yesButton.isEnabled():
            self.yesButton.click()
        elif event.key() == Qt.Key.Key_Escape:
            self.cancelButton.click()
        else:
            super().keyPressEvent(event)
