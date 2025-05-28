import os
import sys
import tomllib
from pathlib import Path

from utils.is_nuitka import is_nuitka


def get_app_version():
    """Get version from pyproject.toml"""
    if is_nuitka():
        # from: https://nuitka.net/user-documentation/common-issue-solutions.html#onefile-finding-files
        pyproject_path = os.path.join(os.path.dirname(sys.argv[0]), "pyproject.toml")
    else:
        pyproject_path = Path(__file__).parent.parent.parent / "pyproject.toml"
    with open(pyproject_path, "rb") as f:
        pyproject = tomllib.load(f)
    return pyproject["project"]["version"]
