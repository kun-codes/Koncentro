import os

from PySide6.QtCore import QCoreApplication, QSettings

from constants import APPLICATION_NAME, ORGANIZATION_NAME

QCoreApplication.setOrganizationName(ORGANIZATION_NAME)
QCoreApplication.setApplicationName(APPLICATION_NAME)

# will only be used to get platform specific file save location, all config values are to be saved using qconfig_custom
setting_temp = QSettings(QSettings.Format.IniFormat, QSettings.Scope.UserScope, ORGANIZATION_NAME, APPLICATION_NAME)

settings_dir = os.path.dirname(setting_temp.fileName())

# replacing the extension of the settings file from .ini to .json
root, _ = os.path.splitext(setting_temp.fileName())
settings_file_path = root + ".json"

db_path: str = os.path.join(settings_dir, f"{APPLICATION_NAME}.db")
