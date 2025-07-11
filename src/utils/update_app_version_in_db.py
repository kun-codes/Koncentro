from models.db_tables import Version
from utils.db_utils import get_session
from utils.get_app_version import get_app_version


def updateAppVersionInDB() -> None:
    with get_session() as session:
        current_app_version = get_app_version()
        version_record = session.query(Version).first()
        version_record.app_version = current_app_version
