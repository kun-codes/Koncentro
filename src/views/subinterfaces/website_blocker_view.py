from loguru import logger
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from qfluentwidgets import (
    InfoBar,
    InfoBarPosition,
    ToolTipFilter,
    ToolTipPosition,
)

from constants import URLListType, WebsiteFilterType
from models.website_list_manager_model import WebsiteListManager
from models.workspace_list_model import WorkspaceListModel
from models.workspace_lookup import WorkspaceLookup
from ui_py.ui_website_blocker_view import Ui_WebsiteBlockView


class WebsiteBlockerView(Ui_WebsiteBlockView, QWidget):
    """
    For website blocker view of the app
    """

    def __init__(self, workspace_list_model: WorkspaceListModel):
        super().__init__()
        self.setupUi(self)

        self.blockListText = ""
        self.allowListText = ""

        self.is_editing = False

        self.model = WebsiteListManager()
        self.workspace_list_model = workspace_list_model

        self.initWidget()
        self.connectSignalsToSlots()

        # self.model.invalidURLSignal.connect(self.onInvalidURLSignal)

        self.saveButton.setDisabled(True)

    def initWidget(self):
        self.blockListTextEdit.setHidden(True)
        self.allowListTextEdit.setHidden(True)

        self.initTextEdits()
        self.initWebsiteFilterComboBox()

        self.saveButton.setToolTip("Save")
        self.saveButton.installEventFilter(
            ToolTipFilter(self.saveButton, showDelay=300, position=ToolTipPosition.BOTTOM)
        )
        self.cancelButton.setToolTip("Cancel Changes")
        self.cancelButton.installEventFilter(
            ToolTipFilter(self.cancelButton, showDelay=300, position=ToolTipPosition.BOTTOM)
        )
        self.blockTypeComboBox.setToolTip("Select Filter Type")
        self.blockTypeComboBox.installEventFilter(
            ToolTipFilter(self.blockTypeComboBox, showDelay=300, position=ToolTipPosition.BOTTOM)
        )

    def connectSignalsToSlots(self):
        self.blockTypeComboBox.currentIndexChanged.connect(self.onFilterTypeChanged)
        self.saveButton.clicked.connect(self.onSaveButtonClicked)
        self.cancelButton.clicked.connect(self.onCancelButtonClicked)
        self.workspace_list_model.current_workspace_deleted.connect(self.onCurrentWorkspaceDeleted)
        self.workspace_list_model.current_workspace_changed.connect(self.onCurrentWorkspaceChanged)

        self.blockListTextEdit.textChanged.connect(self.onTextChanged)
        self.allowListTextEdit.textChanged.connect(self.onTextChanged)

        self.blockListTextEdit.textChanged.connect(self.checkURLs)
        self.allowListTextEdit.textChanged.connect(self.checkURLs)

    def onTextChanged(self):
        self.is_editing = True

        self.saveButton.setDisabled(False)
        self.blockTypeComboBox.setDisabled(True)
        # todo: show the user a tip that they can enable the combo box again by clicking on save or cancel buttons

    def checkURLs(self):
        urls = self.getListOfURLs()

        is_all_urls_valid, invalid_url_line_numbers = self.model.validate_urls(urls)

        # todo: underline invalid urls
        current_website_filter_type = self.model.get_website_filter_type()

        if is_all_urls_valid:
            if current_website_filter_type == WebsiteFilterType.BLOCKLIST:
                self.blockListTextEdit.underline_lines([])
            elif current_website_filter_type == WebsiteFilterType.ALLOWLIST:
                self.allowListTextEdit.underline_lines([])

            return True, urls
        else:
            if current_website_filter_type == WebsiteFilterType.BLOCKLIST:
                self.blockListTextEdit.underline_lines(invalid_url_line_numbers)
            elif current_website_filter_type == WebsiteFilterType.ALLOWLIST:
                self.allowListTextEdit.underline_lines(invalid_url_line_numbers)
            return False, invalid_url_line_numbers

    def getListOfURLs(self):
        current_website_filter_type = self.model.get_website_filter_type()

        if current_website_filter_type == WebsiteFilterType.BLOCKLIST:
            urls = []
            block_count = self.blockListTextEdit.blockCount()
            for i in range(block_count):
                block = self.blockListTextEdit.document().findBlockByNumber(i)
                urls.append(block.text())
            # problems in showing the line numbers of invalid urls
            # using list comprehension instead of set comprehension to maintain the order of urls
        elif current_website_filter_type == WebsiteFilterType.ALLOWLIST:
            urls = []
            block_count = self.allowListTextEdit.blockCount()
            for i in range(block_count):
                block = self.allowListTextEdit.document().findBlockByNumber(i)
                urls.append(block.text())

        return urls

    def onSaveButtonClicked(self):
        is_all_urls_valid, result = self.checkURLs()

        if is_all_urls_valid:
            urls = result
        else:
            self.spawnInvalidURLInfoBar(result)
            return

        current_website_filter_type = self.model.get_website_filter_type()

        # urls are now valid
        urls = set(urls)  # converting to set as self.model.update_target_list_urls() expects a set
        urls = {url.strip() for url in urls if url.strip()}  # removing empty strings and strings with only whitespaces

        if current_website_filter_type == WebsiteFilterType.BLOCKLIST:
            self.model.update_target_list_urls(URLListType.BLOCKLIST, urls)
            self.initTextEdits(WebsiteFilterType.BLOCKLIST)
        elif current_website_filter_type == WebsiteFilterType.ALLOWLIST:
            self.model.update_target_list_urls(URLListType.ALLOWLIST, urls)
            self.initTextEdits(WebsiteFilterType.ALLOWLIST)

        self.is_editing = False

        self.saveButton.setDisabled(True)
        self.blockTypeComboBox.setDisabled(False)

        InfoBar.success(
            "URLs saved",
            f"URLs for {"blocklist" if current_website_filter_type == WebsiteFilterType.BLOCKLIST \
                else "allowlist"} has been saved successfully.",
            orient=Qt.Orientation.Vertical,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=4000,
            parent=self,
        )

    def spawnInvalidURLInfoBar(self, line_numbers: list[int]):
        InfoBar.error(
            "Invalid URLs",
            f"URLs at line numbers {', '.join(map(str, line_numbers[:10]))}"
            f"{'...' if len(line_numbers) > 10 else ''} are invalid.",  # only show first 10 invalid url,
            # if there are more than 10 that then show ... after the first 10 invalid url line numbers
            orient=Qt.Orientation.Vertical,
            isClosable=True,
            position=InfoBarPosition.TOP_RIGHT,
            duration=4000,
            parent=self,
        )

    def onCancelButtonClicked(self):
        self.blockListTextEdit.setPlainText(self.blockListText)
        self.allowListTextEdit.setPlainText(self.allowListText)

        self.is_editing = False

        self.saveButton.setDisabled(True)
        self.blockTypeComboBox.setDisabled(False)

    def load_data(self):
        # todo: check for invalid urls
        pass

    def onFilterTypeChanged(self):
        logger.debug("Inside onFilterTypeChanged")
        if self.blockTypeComboBox.currentIndex() == WebsiteFilterType.BLOCKLIST.value:
            self.allowListTextEdit.setHidden(True)
            self.blockListTextEdit.setHidden(False)

            self.model.set_website_filter_type(WebsiteFilterType.BLOCKLIST)

        elif self.blockTypeComboBox.currentIndex() == WebsiteFilterType.ALLOWLIST.value:
            self.allowListTextEdit.setHidden(False)
            self.blockListTextEdit.setHidden(True)

            self.model.set_website_filter_type(WebsiteFilterType.ALLOWLIST)

    def initWebsiteFilterComboBox(self):
        self.blockTypeComboBox.addItem("Blocklist")
        self.blockTypeComboBox.addItem("Allowlist")

        self.blockTypeComboBox.setCurrentIndex(self.model.get_website_filter_type().value)
        self.onFilterTypeChanged()  # calling manually since signals aren't connected to slots yet

    def initTextEdits(self, filter_type: WebsiteFilterType = None):
        if filter_type is None:
            self.blockListTextEdit.setPlainText("\n".join(sorted(self.model.blocklist_urls)))
            self.allowListTextEdit.setPlainText("\n".join(sorted(self.model.allowlist_urls)))

            self.blockListText = self.blockListTextEdit.toPlainText()
            self.allowListText = self.allowListTextEdit.toPlainText()
        elif filter_type == WebsiteFilterType.BLOCKLIST:
            self.blockListTextEdit.setPlainText("\n".join(sorted(self.model.blocklist_urls)))
            self.blockListText = self.blockListTextEdit.toPlainText()
        elif filter_type == WebsiteFilterType.ALLOWLIST:
            self.allowListTextEdit.setPlainText("\n".join(sorted(self.model.allowlist_urls)))
            self.allowListText = self.allowListTextEdit.toPlainText()

    def onCurrentWorkspaceDeleted(self):
        # set every ui component to its default
        self.blockTypeComboBox.setCurrentIndex(0)
        # todo: set blockTypeComboBox index to new current workspace's website_filter_type
        self.blockTypeComboBox.currentIndexChanged.emit(0)
        self.blockListTextEdit.clear()
        # todo: set blockListTextEdit to new current workspace's blocklist
        self.allowListTextEdit.clear()
        # todo: set allowListTextEdit to new current workspace's allowlist

    def onCurrentWorkspaceChanged(self):
        self.model.load_website_filter_type()
        self.model.load_data()

        current_workspace = WorkspaceLookup.get_current_workspace()
        self.blockTypeComboBox.setCurrentIndex(current_workspace.website_filter_type.value)

        self.initTextEdits()

        self.is_editing = False

        self.saveButton.setDisabled(True)
        self.blockTypeComboBox.setDisabled(False)
