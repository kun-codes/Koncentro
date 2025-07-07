import os
import platform
import shutil
import sys
from pathlib import Path

from loguru import logger

from utils.is_nuitka import is_nuitka


def get_mitmdump_path():
    if is_nuitka():
        # from: https://nuitka.net/user-documentation/common-issue-solutions.html#onefile-finding-files
        mitmdump_path = os.path.join(os.path.dirname(sys.argv[0]), "mitmdump")

        mitmdump_path = Path(mitmdump_path)

        if platform.system() == "Windows":
            mitmdump_path = mitmdump_path.with_suffix(".exe")

        if mitmdump_path.exists():
            logger.debug(f"mitmdump path: {mitmdump_path}")
            return str(mitmdump_path)

    # get the path to the project root
    path = Path(__file__).parent.parent.parent
    # Find the path to the mitmdump executable
    mitmdump_path = shutil.which("mitmdump", path=path)

    if platform.system() == "Windows" and mitmdump_path is None:
        mitmdump_path = shutil.which("mitmdump.exe", path=path)

    if mitmdump_path is None:
        logger.error("mitmdump executable not found in PATH")
    else:
        logger.debug(f"mitmdump path: {mitmdump_path}")

    return mitmdump_path
