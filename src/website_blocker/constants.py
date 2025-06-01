# Don't add any 3rd party imports here, as this file is used by mitmdump directly through filter.py

import os
import sys
from pathlib import Path

APPLICATION_NAME = "Koncentro"

MITMDUMP_SHUTDOWN_URL = f"http://shutdown.{APPLICATION_NAME.lower()}.internal/"
BLOCK_HTML_MESSAGE = f"<h1>Website blocked by {APPLICATION_NAME}!</h1>"

MITMDUMP_COMMAND_LINUX = (
    '"{}" --set allow_remote=true -p {} --showhost -s "{}" --set "addresses_str={}" --set "block_type={}"'.format(
        "{}",
        "{}",
        os.path.join(getattr(sys, "_MEIPASS", Path(__file__).parent), "filter.py"),
        "{}",
        "{}",
    )
)  # using _MEIPASS to make it compatible with pyinstaller
# the os.path.join returns the location of filter.py

MITMDUMP_COMMAND_WINDOWS = (
    r'"{}" --set allow_remote=true -p {} --showhost -s "{}" --set "addresses_str={}" --set "block_type={}"'.format(
        "{}",
        "{}",
        os.path.join(getattr(sys, "_MEIPASS", Path(__file__).parent), "filter.py"),
        "{}",
        "{}",
    )
)  # using _MEIPASS to make it compatible with pyinstaller
# the os.path.join returns the location of filter.py

