from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from sqlite3 import Connection as SQLiteConnection
from typing import Optional

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QPixmap
from sqlalchemy import (
    URL,
    Boolean,
    Column,
    DateTime,
    Dialect,
    Engine,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    TypeDecorator,
    create_engine,
    event,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.pool.base import _ConnectionRecord

from configPaths import db_path, settings_dir
from constants import (
    DEFAULT_AUTOSTART_BREAK,
    DEFAULT_AUTOSTART_WORK,
    DEFAULT_BREAK_DURATION,
    DEFAULT_ENABLE_WEBSITE_BLOCKER,
    DEFAULT_LONG_BREAK_DURATION,
    DEFAULT_WORK_DURATION,
    DEFAULT_WORK_INTERVALS,
    URLListType,
    WebsiteBlockType,
)

url_object = URL.create(
    "sqlite",
    database=db_path,
)
engine = create_engine(url_object)

settings_dir = Path(settings_dir)
# if the settings directory does not exist, create it
if not settings_dir.exists():
    settings_dir.mkdir(parents=True)

Base = declarative_base()


# from: https://docs.sqlalchemy.org/en/20/dialects/sqlite.html#foreign-key-support
# for supporting foreign keys in sqlite as they are disabled by default as per: https://www.sqlite.org/foreignkeys.html
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection: SQLiteConnection, connection_record: _ConnectionRecord) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class TaskType(Enum):
    TODO = "TODO"
    COMPLETED = "COMPLETED"


class PathType(TypeDecorator[Path]):
    impl = String
    cache_ok = True

    def process_bind_param(self, value: Optional[Path], dialect: Dialect) -> Optional[str]:
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value: Optional[str], dialect: Dialect) -> Optional[Path]:
        if value is None:
            return None
        return Path(value)


class IconType(TypeDecorator[QPixmap]):
    impl = LargeBinary
    cache_ok = True

    def process_bind_param(self, value: Optional[QPixmap], dialect: Dialect) -> Optional[bytes]:
        if value is None:
            return None
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        value.save(buffer, "PNG")
        return bytes(buffer.data())

    def process_result_value(self, value: Optional[bytes], dialect: Dialect) -> Optional[QPixmap]:
        if value is None:
            return None
        pixmap = QPixmap()
        pixmap.loadFromData(value)
        return pixmap


class Version(Base):
    """Stores application and database schema version"""

    __tablename__ = "version"

    id = Column(Integer, primary_key=True)
    app_version = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.now(timezone.utc))
    updated_at = Column(
        DateTime(timezone=True), default=datetime.now(timezone.utc), onupdate=datetime.now(timezone.utc)
    )


class Task(Base):
    """
    Represents a table named "tasks" in the database
    """

    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    task_name = Column(String)
    task_type = Column(SQLEnum(TaskType))
    task_position = Column(Integer)
    elapsed_time = Column(Integer, default=0)
    target_time = Column(Integer, default=0)
    is_parent_task = Column(Boolean, default=True, nullable=False)
    # needs a name because self referential foreign key constraint
    parent_task_id = Column(
        Integer, ForeignKey("tasks.id", name="fk_tasks_parent_task_id"), nullable=True, default=None
    )
    is_expanded = Column(Boolean, default=False, nullable=True)

    workspace = relationship("Workspace", back_populates="tasks")


class BlocklistApp(Base):
    __tablename__ = "blocklist_apps"

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), nullable=False)
    app_name = Column(String, nullable=False)
    app_path = Column(PathType, nullable=False)
    app_icon = Column(IconType)

    workspace = relationship("Workspace", back_populates="blocklist_apps")


class Workspace(Base):
    """
    Represents a table named "workspaces" in the database
    """

    __tablename__ = "workspaces"

    id = Column(Integer, primary_key=True)
    workspace_name = Column(String, nullable=False)
    work_duration = Column(Integer, default=DEFAULT_WORK_DURATION)
    break_duration = Column(Integer, default=DEFAULT_BREAK_DURATION)
    long_break_duration = Column(Integer, default=DEFAULT_LONG_BREAK_DURATION)
    work_intervals = Column(Integer, default=DEFAULT_WORK_INTERVALS)
    autostart_work = Column(Boolean, default=DEFAULT_AUTOSTART_WORK)
    autostart_break = Column(Boolean, default=DEFAULT_AUTOSTART_BREAK)
    enable_website_blocker = Column(Boolean, default=DEFAULT_ENABLE_WEBSITE_BLOCKER)
    website_block_type = Column(SQLEnum(WebsiteBlockType), default=WebsiteBlockType.BLOCKLIST)

    blocklist_urls = relationship("BlocklistURL", back_populates="workspace", cascade="all, delete-orphan")
    blocklist_exception_urls = relationship(
        "BlocklistExceptionURL", back_populates="workspace", cascade="all, delete-orphan"
    )
    allowlist_urls = relationship("AllowlistURL", back_populates="workspace", cascade="all, delete-orphan")
    allowlist_exception_urls = relationship(
        "AllowlistExceptionURL", back_populates="workspace", cascade="all, delete-orphan"
    )

    tasks = relationship("Task", back_populates="workspace", cascade="all, delete-orphan")

    blocklist_apps = relationship("BlocklistApp", back_populates="workspace", cascade="all, delete-orphan")


class CurrentWorkspace(Base):
    """
    Represents a table named "current_workspace" in the database
    """

    __tablename__ = "current_workspace"

    id = Column(Integer, primary_key=True)
    # TODO: use ` cascade="all, delete-orphan"` here too for more compatibility with other databases
    current_workspace_id = Column(Integer, ForeignKey("workspaces.id", ondelete="CASCADE"), unique=True, nullable=False)


class BlocklistURL(Base):
    __tablename__ = URLListType.BLOCKLIST.value
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    url = Column(String, nullable=False)

    workspace = relationship("Workspace", back_populates="blocklist_urls")


class BlocklistExceptionURL(Base):
    __tablename__ = URLListType.BLOCKLIST_EXCEPTION.value
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    url = Column(String, nullable=False)

    workspace = relationship("Workspace", back_populates="blocklist_exception_urls")


class AllowlistURL(Base):
    __tablename__ = URLListType.ALLOWLIST.value
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    url = Column(String, nullable=False)

    workspace = relationship("Workspace", back_populates="allowlist_urls")


class AllowlistExceptionURL(Base):
    __tablename__ = URLListType.ALLOWLIST_EXCEPTION.value
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    url = Column(String, nullable=False)

    workspace = relationship("Workspace", back_populates="allowlist_exception_urls")
