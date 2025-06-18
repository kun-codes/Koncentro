import sys

import psutil
from PySide6.QtWidgets import QApplication, QMessageBox
from loguru import logger


def check_init_service():
    try:
        init_process = psutil.Process(1)
        if "systemd" in init_process.name().lower():
            logger.info("Detected systemd init service, proceeding with application launch.")
            return True
        else:
            _app = QApplication(sys.argv)
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Unsupported Init Service")
            msg.setInformativeText("This application is only supported on systems using systemd.")
            msg.setWindowTitle("Unsupported Init Service")
            msg.exec()
            sys.exit(1)
    except Exception as e:
        logger.error(f"Error checking init service: {e}")
        # If we can't determine the init system, assume it's not systemd
        _app = QApplication(sys.argv)
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Unsupported Init Service")
        msg.setInformativeText("Could not determine init service."
                               " This application is only supported on systems using systemd.")
        msg.setWindowTitle("Unsupported Init Service")
        msg.exec()
        sys.exit(1)
