import os
import platform
import subprocess

from loguru import logger
from PySide6.QtCore import Qt, QThread, QTimer, QUrl, Signal
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QSizePolicy
from qfluentwidgets import BodyLabel, FluentIcon, InfoBar, MessageBoxBase, PushButton, SubtitleLabel

from config_values import ConfigValues
from constants import (
    APPLICATION_NAME,
    CHECK_CERTIFICATE_WINDOWS_COMMAND,
    InstallMitmproxyCertificateResult,
)
from utils.find_mitmdump_executable import get_mitmdump_path
from views.dialogs.postSetupVerificationDialog import PostSetupVerificationDialog
from website_blocker.website_blocker_manager import WebsiteBlockerManager


class CertificateInstallWindowsWorker(QThread):
    finished = Signal(InstallMitmproxyCertificateResult)

    def __init__(self, powershell_command):
        super().__init__()
        self.powershell_command = powershell_command

    def run(self):
        try:
            # First check if the certificate already exists
            check_result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", CHECK_CERTIFICATE_WINDOWS_COMMAND],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if check_result.returncode != 0:
                self.finished.emit(InstallMitmproxyCertificateResult.ERROR)
                return

            # If certificate already exists
            if check_result.stdout.strip():
                self.finished.emit(InstallMitmproxyCertificateResult.ALREADY_INSTALLED)
                return

            # Certificate doesn't exist, proceed with installation
            install_result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", self.powershell_command],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if install_result.returncode == 0:
                self.finished.emit(InstallMitmproxyCertificateResult.SUCCESS)
            else:
                self.finished.emit(InstallMitmproxyCertificateResult.FAILURE)

        except subprocess.TimeoutExpired:
            self.finished.emit(InstallMitmproxyCertificateResult.TIMEOUT)
        except Exception as e:
            logger.error(f"Error during certificate installation: {str(e)}")
            self.finished.emit(InstallMitmproxyCertificateResult.ERROR)


class SetupAppDialog(MessageBoxBase):
    def __init__(self, parent=None, is_setup_first_time: bool = True) -> None:
        super().__init__(parent=parent)

        self.is_setup_first_time = is_setup_first_time

        titleText = f"Setup {APPLICATION_NAME}"
        titleText += " for the first time" if self.is_setup_first_time else ""
        self.titleLabel = SubtitleLabel(titleText, parent=self)

        if platform.system().lower() == "windows":
            bodyText = "Click the below button to install the mitmproxy certificate to Windows."
        else:
            bodyText = "Click the below button to visit the webpage to set up system-wide website blocking. "

        self.bodyLabel = BodyLabel(
            bodyText,
            parent=self,
        )

        self.bodyLabel2 = BodyLabel(
            "You would need to install mitmproxy's certificate to your system to enable website blocking",
            parent=self,
        )

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.bodyLabel)
        self.viewLayout.addWidget(self.bodyLabel2)

        self.yesButton.setText("Open Setup")
        self.yesButton.setIcon(FluentIcon.LINK)
        self.cancelButton.setText("Setup Completed")

        self.backButton = PushButton("Cancel Setup", self.buttonGroup)

        # to make all buttons have the same size
        self.buttonLayout.insertWidget(0, self.backButton, 1, Qt.AlignmentFlag.AlignVCenter)
        for button in [self.yesButton, self.cancelButton, self.backButton]:
            button.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            button.setMinimumWidth(150)

        self.initWidget()
        self.initTemporaryWebsiteBlockerManager()

        self.certificateTimer = None
        if platform.system().lower() == "windows":
            self.initCertificateWatcher()

        self.certificate_worker = None

    def initCertificateWatcher(self) -> None:
        """
        only for Windows for now
        """
        InfoBar.info(
            title="Waiting for Certificate Generation",
            content="It would only take a few seconds.",
            orient=Qt.Orientation.Vertical,
            isClosable=False,
            duration=3000,
            parent=self,
        )
        self.yesButton.setEnabled(False)
        self.cancelButton.setEnabled(False)

        self.certificateTimer = QTimer()
        self.certificateTimer.timeout.connect(self.isCertificateExists)
        self.certificateTimer.start(300)

    def isCertificateExists(self) -> bool:
        """
        only for Windows for now
        """
        if platform.system().lower() == "windows":
            username = os.getlogin()
            certPath = os.path.join("C:\\Users", username, ".mitmproxy", "mitmproxy-ca-cert.cer")

            if os.path.exists(certPath):
                InfoBar.success(
                    title="Certificate Generated",
                    content="Mitmproxy certificate has been successfully generated.",
                    orient=Qt.Orientation.Vertical,
                    isClosable=True,
                    duration=3000,
                    parent=self,
                )
                logger.debug("Mitmproxy certificate found, enabling buttons.")
                self.yesButton.setEnabled(True)
                self.cancelButton.setEnabled(True)
                self.yesButton.setText("Open Setup")
                if self.certificateTimer is not None:
                    self.certificateTimer.stop()
                return True
            else:
                logger.debug("Waiting for mitmproxy certificate to be generated...")
                return False

    def initWidget(self) -> None:
        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.bodyLabel.setWordWrap(True)
        self.bodyLabel.setAlignment(Qt.AlignmentFlag.AlignJustify)

        self.bodyLabel2.setWordWrap(True)
        self.bodyLabel2.setAlignment(Qt.AlignmentFlag.AlignJustify)

        # self.widget.setFixedSize(300, 500)

        self.__connectSignalsToSlots()

    def __connectSignalsToSlots(self) -> None:
        # disconnecting from the default slots as done in the parent class, so that self.accept() and self.reject()
        # are not called
        self.yesButton.clicked.disconnect()
        self.cancelButton.clicked.disconnect()
        self.yesButton.clicked.connect(self.onWebsiteBlockSetupButtonClicked)
        self.cancelButton.clicked.connect(self.onCloseButtonClicked)
        self.backButton.clicked.connect(self.onBackButtonClicked)

    def onWebsiteBlockSetupButtonClicked(self) -> None:
        if platform.system().lower() == "windows":
            if self.certificate_worker and self.certificate_worker.isRunning():
                return

            # clean up any existing worker
            if self.certificate_worker:
                self.certificate_worker.finished.disconnect()
                self.certificate_worker.deleteLater()
                self.certificate_worker = None

            username = os.getlogin()
            certPath = os.path.join("C:\\Users", username, ".mitmproxy", "mitmproxy-ca-cert.cer")

            powershell_command = (
                f'Import-Certificate -FilePath "{certPath}" -CertStoreLocation Cert:\\CurrentUser\\Root'
            )

            self.certificate_worker = CertificateInstallWindowsWorker(powershell_command)
            self.certificate_worker.finished.connect(self.onCertificateInstallFinished)
            self.certificate_worker.start()
        else:
            url = QUrl("http://mitm.it/")
            QDesktopServices.openUrl(url)

    def onCloseButtonClicked(self) -> None:
        confirmation_dialog = PostSetupVerificationDialog(self, self.is_setup_first_time)

        if confirmation_dialog.exec():
            self.temporary_website_blocker_manager.stop_blocking(delete_proxy=True)  # stopping website blocking here
            # because this function will only be triggered after confirmation_dialog is accepted
            self.accept()

    def onBackButtonClicked(self) -> None:
        self.temporary_website_blocker_manager.stop_blocking(delete_proxy=True)
        self.reject()

    def initTemporaryWebsiteBlockerManager(self) -> None:
        self.temporary_website_blocker_manager = WebsiteBlockerManager()
        self.temporary_website_blocker_manager.start_blocking(
            listening_port=ConfigValues.PROXY_PORT,
            joined_addresses="example.com",
            block_type="blocklist",
            mitmdump_bin_path=get_mitmdump_path(),
        )

    def onCertificateInstallFinished(self, result: InstallMitmproxyCertificateResult):
        if result == InstallMitmproxyCertificateResult.SUCCESS:
            InfoBar.success(
                title=result.value,
                content="",
                orient=Qt.Orientation.Vertical,
                isClosable=True,
                duration=3000,
                parent=self.parent(),
            )
        elif result == InstallMitmproxyCertificateResult.ALREADY_INSTALLED:
            InfoBar.info(
                title=result.value,
                content="",
                orient=Qt.Orientation.Vertical,
                isClosable=True,
                duration=3000,
                parent=self.parent(),
            )
        else:
            InfoBar.error(
                title=result.value,
                content="",
                orient=Qt.Orientation.Vertical,
                isClosable=True,
                duration=5000,
                parent=self.parent(),
            )

        # Clean up worker
        if self.certificate_worker:
            self.certificate_worker.deleteLater()
            self.certificate_worker = None
