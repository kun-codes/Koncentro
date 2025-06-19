import platform
import os.path
import signal
import sys
from pathlib import Path

# Apply tooltip patch to fix window flags issue
try:
    from utils.patch_tooltip import apply_patches
    apply_patches()
except Exception as e:
    print(f"Warning: Could not apply tooltip patch: {e}")

from alembic import command
from alembic.config import Config
from loguru import logger
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication, QMessageBox

import resources.fonts_rc
from constants import APPLICATION_NAME, APPLICATION_UID, ORGANIZATION_NAME
from main_window import MainWindow
from prefabs.qtSingleApplication import QtSingleApplication
from utils.check_init_service import check_init_service
from utils.check_valid_db import checkValidDB
from utils.is_nuitka import is_nuitka
from utils.update_app_version_in_db import updateAppVersionInDB


def handle_signal(signal, frame):
    if mainWindow:
        mainWindow.close()

    app_instance = QApplication.instance()
    app_instance.quit()

# https://alembic.sqlalchemy.org/en/latest/cookbook.html#building-an-up-to-date-database-from-scratch
def run_alembic_upgrade():
    if is_nuitka():
        # from: https://nuitka.net/user-documentation/common-issue-solutions.html#onefile-finding-files
        alembic_ini_path = os.path.join(os.path.dirname(sys.argv[0]), "alembic.ini")
    else:
        alembic_ini_path = Path(__file__).parent.parent / "alembic.ini"
    alembic_cfg = Config(alembic_ini_path)
    # alembic_cfg.set_main_option("script_location", str(Path(__file__).parent.parent / "migrations"))
    command.upgrade(alembic_cfg, "head")

def substitute_fonts():
    # Windows already has Segoe UI, so no need to substitute fonts
    if not os.name == "nt":
        fonts = [
            ":/fontsPrefix/fonts/selawk.ttf",
            ":/fontsPrefix/fonts/selawkb.ttf",
            ":/fontsPrefix/fonts/selawkl.ttf",
            ":/fontsPrefix/fonts/selawksb.ttf",
            ":/fontsPrefix/fonts/selawksl.ttf",
        ]

        for font in fonts:
            id = QFontDatabase.addApplicationFont(font)
            if id < 0:
                logger.error(f"Failed to load font: {font}")

        QFont.insertSubstitutions(
            "Segoe UI", ["Selawik", "Selawik Light", "Selawik Semibold", "Selawik Semilight"])

def check_desktop_environment():
    desktop_env = os.environ.get("XDG_CURRENT_DESKTOP", "").lower()
    if any(env in desktop_env for env in ["gnome", "kde", "cinnamon"]):
        logger.info("Detected GNOME,KDE or Cinnamon desktop environment, proceeding with application launch.")
        return True
    else:
        _app = QApplication(sys.argv)  # temporary application for the message box
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Unsupported Desktop Environment")
        msg.setInformativeText("This application is not supported on your current desktop environment. Please use GNOME or KDE.")
        msg.setWindowTitle("Unsupported Desktop Environment")
        msg.exec()
        sys.exit(1)  # Exit the application after showing the message


if __name__ == "__main__":
    if platform.system().lower() == "linux":
        check_desktop_environment()
        check_init_service()

    run_alembic_upgrade()  # create db if it doesn't exist and run migrations
    checkValidDB()  # Check if the database is valid, if it doesn't have required sample data, add it
    updateAppVersionInDB()

    appUID = APPLICATION_UID
    app = QtSingleApplication(appUID, sys.argv)

    if app.isRunning():
        logger.info("Application is already running, activating window of the existing instance.")
        logger.info("Exiting current instance....")
        sys.exit(0)

    substitute_fonts()

    # Set application information for notifications
    app.setApplicationName(APPLICATION_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationDisplayName(APPLICATION_NAME)

    mainWindow = MainWindow()
    mainWindow.show()

    app.setActivationWindow(mainWindow)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    sys.exit(app.exec())
