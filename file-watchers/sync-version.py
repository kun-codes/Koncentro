#!/usr/bin/env python3

"""
This script updates the version in `get_app_version.py` based on the version specified in `pyproject.toml`.
This script is automatically ran by PyCharm when the `pyproject.toml` file is modified.
"""

import re
from pathlib import Path
import tomllib

PYPROJECT_PATH = Path(__file__).parent.parent / "pyproject.toml"
GET_APP_VERSION_PATH = Path(__file__).parent.parent / "src" / "utils" / "get_app_version.py"

def get_version_from_pyproject():
    with PYPROJECT_PATH.open("rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]

def update_get_app_version(version):
    with GET_APP_VERSION_PATH.open("r") as f:
        content = f.read()
    new_content = re.sub(
        r'return\s*["\'].*?["\']',
        f'return "{version}"',
        content
    )
    with GET_APP_VERSION_PATH.open("w") as f:
        f.write(new_content)

if __name__ == "__main__":
    version = get_version_from_pyproject()
    update_get_app_version(version)
    print(f"Updated get_app_version.py to version {version}")
