#!/usr/bin/env python3

import re
import subprocess
import sys
import tomllib
from pathlib import Path


def get_version_from_pyproject():
    """Extract version from pyproject.toml."""
    pyproject_path = Path("pyproject.toml")
    with pyproject_path.open("rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]


def get_latest_tag():
    """Get the most recent Git tag that matches v*.*.* format."""
    try:
        # First get all tags sorted by creation date (newest first)
        result = subprocess.run(["git", "tag", "--sort=-creatordate"], capture_output=True, text=True, check=False)

        if result.returncode == 0 and result.stdout.strip():
            # Filter tags to only include those matching v*.*.* format
            import re

            version_pattern = re.compile(r"^v\d+\.\d+\.\d+$")
            tags = result.stdout.strip().split("\n")

            # Find the newest tag that matches our pattern
            for tag in tags:
                if version_pattern.match(tag):
                    return tag

        return None
    except Exception as e:
        print(f"Error getting latest tag: {e}")
        return None


def get_pending_tags():
    """Get any tags that are about to be pushed."""
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached", "refs/tags/"], capture_output=True, text=True, check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            # Extract tag names from the diff output
            return [line.split("/")[-1] for line in result.stdout.strip().split("\n")]
        return []
    except Exception:
        return []


def main():
    # Get version from pyproject.toml
    pyproject_version = get_version_from_pyproject()

    # Get pending tags or the latest tag
    tags_to_check = get_pending_tags()
    if not tags_to_check:
        latest_tag = get_latest_tag()
        if latest_tag:
            tags_to_check = [latest_tag]

    # Check each tag against the version pattern
    for tag in tags_to_check:
        if re.match(r"^v\d+\.\d+\.\d+$", tag):
            # Extract version without the 'v' prefix
            tag_version = tag[1:]

            # Compare versions
            if tag_version != pyproject_version:
                print(
                    f"Error: Tag version ({tag_version}) does not match the version in "
                    f"pyproject.toml ({pyproject_version})"
                )
                print("Please update pyproject.toml or use the correct tag version.")
                return 1
            else:
                print(f"Version check passed: Tag version {tag} matches pyproject.toml version ({pyproject_version})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
