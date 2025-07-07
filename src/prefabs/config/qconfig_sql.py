from copy import deepcopy
from pathlib import Path
from typing import Union
from venv import logger

from qfluentwidgets import (
    ConfigItem,
    QConfig,
    exceptionHandler,
)

from config_paths import settings_file_path
from models.db_tables import Workspace
from models.workspace_lookup import WorkspaceLookup
from prefabs.config.config_item_sql import ConfigItemSQL
from utils.db_utils import get_session


class QConfigSQL(QConfig):
    def __init__(self) -> None:
        super().__init__()
        self.file = Path(settings_file_path)
        self._cfg.file = Path(settings_file_path)

    def set(self, item: Union[ConfigItemSQL, ConfigItem], value, save=True, copy=True) -> None:
        """set the value of config item

        Parameters
        ----------
        item: ConfigItem
            config item

        value:
            the new value of config item

        save: bool
            whether to save the change to config file

        copy: bool
            whether to deep copy the new value
        """

        # deepcopy new value
        try:
            item.value = deepcopy(value) if copy else value
        except Exception:
            item.value = value

        if isinstance(item, ConfigItemSQL) and save:
            self.saveToDB(item)

        if item.restart:
            self._cfg.appRestartSig.emit()

    def saveToDB(self, item: ConfigItemSQL) -> None:
        with get_session() as session:
            db_table = item.db_table
            db_column = item.db_column

            if db_table == Workspace:
                current_workspace = WorkspaceLookup.get_current_workspace_id()  # make changes only ion the current
                # workspace
                record = session.query(db_table).filter_by(id=current_workspace).first()
                if record:
                    logger.debug(f"Setting {db_column.name} to {item.value}")
                    setattr(record, db_column.name, item.value)

    @exceptionHandler()
    def load(self, file=None, config=None) -> None:
        """load config

        Parameters
        ----------
        file: str or Path
            the path of json config file

        config: Config
            config object to be initialized
        """
        if isinstance(config, QConfigSQL):
            self._cfg = config

        if isinstance(file, (str, Path)):
            self._cfg.file = Path(file)

        self.load_from_db()

    def load_from_db(self, file=None, config=None) -> None:
        # load from database
        with get_session(is_read_only=True) as session:
            current_workspace = WorkspaceLookup.get_current_workspace_id()
            workspace_record = session.query(Workspace).filter_by(id=current_workspace).first()

            if workspace_record:
                for name in dir(self._cfg.__class__):
                    item = getattr(self._cfg.__class__, name)
                    if isinstance(item, ConfigItemSQL):
                        db_value = getattr(workspace_record, item.db_column.name, None)
                        if db_value is not None:
                            item.value = db_value


qconfig_custom = QConfigSQL()
