import os.path
import signal
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config
from PySide6.QtWidgets import QApplication

from constants import APPLICATION_NAME, ORGANIZATION_NAME
from main_window import MainWindow
from utils.check_valid_db import checkValidDB
from utils.is_nuitka import is_nuitka


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


if __name__ == "__main__":
    run_alembic_upgrade()  # create db if it doesn't exist and run migrations
    checkValidDB()  # Check if the database is valid, if it doesn't have required sample data, add it

    app = QApplication(sys.argv)

    # Set application information for notifications
    app.setApplicationName(APPLICATION_NAME)
    app.setOrganizationName(ORGANIZATION_NAME)
    app.setApplicationDisplayName(APPLICATION_NAME)

    mainWindow = MainWindow()
    mainWindow.show()

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    sys.exit(app.exec())
