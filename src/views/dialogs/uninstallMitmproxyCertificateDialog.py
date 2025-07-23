import subprocess

from loguru import logger
from PySide6.QtCore import Qt, QThread, Signal
from qfluentwidgets import BodyLabel, InfoBar, MessageBoxBase, SubtitleLabel

from constants import (
    CHECK_CERTIFICATE_WINDOWS_COMMAND,
    UNINSTALL_CERTIFICATE_WINDOWS_COMMAND,
    UninstallMitmproxyCertificateResult,
)


class CertificateUninstallWindowsWorker(QThread):
    finished = Signal(UninstallMitmproxyCertificateResult)

    def run(self):
        try:
            # First check if the certificate exists
            check_result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", CHECK_CERTIFICATE_WINDOWS_COMMAND],
                capture_output=True,
                text=True,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if check_result.returncode != 0:
                self.finished.emit(UninstallMitmproxyCertificateResult.ERROR)
                return

            if not check_result.stdout.strip():
                self.finished.emit(UninstallMitmproxyCertificateResult.NOT_INSTALLED)
                return

            # Certificate exists, proceed with uninstall
            uninstall_result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", UNINSTALL_CERTIFICATE_WINDOWS_COMMAND],
                capture_output=True,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )

            if uninstall_result.returncode == 0:
                self.finished.emit(UninstallMitmproxyCertificateResult.SUCCESS)
            else:
                self.finished.emit(UninstallMitmproxyCertificateResult.FAILURE)

        except subprocess.TimeoutExpired:
            self.finished.emit(UninstallMitmproxyCertificateResult.TIMEOUT)
        except Exception as e:
            logger.error(f"Error during certificate uninstall: {str(e)}")
            self.finished.emit(UninstallMitmproxyCertificateResult.ERROR)


class UninstallMitmproxyCertificateDialog(MessageBoxBase):
    def __init__(self, parent=None) -> None:
        super().__init__(parent=parent)
        self.titleLabel = SubtitleLabel("Uninstall Mitmproxy Certificate", parent=self)
        self.bodyLabel = BodyLabel(parent=self)
        self.bodyLabel.setText(
            "Click the button below to uninstall the mitmproxy certificate from your system. "
            "This is recommended if you are facing problems with website blocking"
        )
        self.bodyLabel2 = BodyLabel(parent=self)
        self.bodyLabel2.setText("If you want to reinstall the certificate later, you can do so from the Settings page.")

        for label in [self.bodyLabel, self.bodyLabel2]:
            label.setWordWrap(True)

        self.yesButton.setText("Uninstall Certificate")
        self.cancelButton.setText("Cancel")

        self.viewLayout.addWidget(self.titleLabel)
        self.viewLayout.addWidget(self.bodyLabel)
        self.viewLayout.addWidget(self.bodyLabel2)

        self.accepted.connect(self.uninstallMitmproxyCertificate)
        self.accepted.connect(lambda: logger.debug("accepted uninstall certificate dialog"))
        self.rejected.connect(self.reject)

        self.worker = None

    def uninstallMitmproxyCertificate(self) -> None:
        # Prevent multiple executions
        if self.worker and self.worker.isRunning():
            return

        # Disable the button to prevent multiple clicks
        self.yesButton.setEnabled(False)

        # Clean up any existing worker
        if self.worker:
            self.worker.finished.disconnect()
            self.worker.deleteLater()
            self.worker = None

        # Create and start worker thread
        self.worker = CertificateUninstallWindowsWorker()
        self.worker.finished.connect(self.onUninstallFinished)
        self.worker.finished.connect(lambda: logger.debug("uninstall certificate worker finished"))
        self.worker.start()

    def onUninstallFinished(self, result: UninstallMitmproxyCertificateResult):
        # Disconnect the signal immediately to prevent multiple calls
        if self.worker:
            self.worker.finished.disconnect()

        self.yesButton.setEnabled(True)

        if result == UninstallMitmproxyCertificateResult.SUCCESS:
            InfoBar.success(
                title=result.value,
                content="",
                orient=Qt.Orientation.Vertical,
                isClosable=True,
                duration=3000,
                parent=self.parent(),
            )
        elif result == UninstallMitmproxyCertificateResult.NOT_INSTALLED:
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
        if self.worker:
            self.worker.deleteLater()
            self.worker = None
