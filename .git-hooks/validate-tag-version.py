#!/usr/bin/env python3

import os
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


def get_local_tags():
    """Get all local tags that match v*.*.* format."""
    try:
        result = subprocess.run(["git", "tag"], capture_output=True, text=True, check=False)

        if result.returncode == 0 and result.stdout.strip():
            # Filter tags to only include those matching v*.*.* format
            import re

            version_pattern = re.compile(r"^v\d+\.\d+\.\d+$")
            tags = result.stdout.strip().split("\n")

            # Return all tags that match our pattern
            return [tag for tag in tags if version_pattern.match(tag)]

        return []
    except Exception as e:
        print(f"Error getting local tags: {e}")
        return []


def get_remote_tags():
    """Get all tags on the remote."""
    try:
        # Use git ls-remote to list remote tags
        result = subprocess.run(["git", "ls-remote", "--tags", "origin"], capture_output=True, text=True, check=False)

        if result.returncode == 0 and result.stdout.strip():
            # Extract tag names from the output
            remote_tags = []
            for line in result.stdout.strip().split("\n"):
                if "refs/tags/" in line and not line.endswith("^{}"):
                    tag = line.split("refs/tags/")[1]
                    remote_tags.append(tag)
            return remote_tags
        return []
    except Exception as e:
        print(f"Error getting remote tags: {e}")
        return []


def get_unpushed_tags():
    """Get tags that exist locally but not on the remote."""
    local_tags = get_local_tags()
    remote_tags = get_remote_tags()

    return [tag for tag in local_tags if tag not in remote_tags]


def get_pending_tags():
    """Get any tags that are about to be pushed."""
    # First check standard method
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", "--cached", "refs/tags/"], capture_output=True, text=True, check=False
        )
        if result.returncode == 0 and result.stdout.strip():
            # Extract tag names from the diff output
            return [line.split("/")[-1] for line in result.stdout.strip().split("\n")]
    except Exception:
        pass

    # If that didn't work, check for environment variables set by pre-push hook
    if "GIT_PUSH_OPTION_COUNT" in os.environ:
        # This means we're in a push operation
        return get_unpushed_tags()

    return []


def main():
    # Get version from pyproject.toml
    pyproject_version = get_version_from_pyproject()

    # Check if this is being run directly from pre-push
    is_pre_push = "GIT_PUSH_OPTION_COUNT" in os.environ

    # Get tags to check
    tags_to_check = get_pending_tags()

    # If no pending tags but we're in a pre-push context, check unpushed tags
    if not tags_to_check and is_pre_push:
        tags_to_check = get_unpushed_tags()

    # If still no tags to check, use the latest tag
    if not tags_to_check:
        latest_tag = get_latest_tag()
        if latest_tag:
            tags_to_check = [latest_tag]

    # No tags to check at all, exit cleanly
    if not tags_to_check:
        print("No version tags to validate.")
        return 0

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
