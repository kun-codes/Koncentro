import json
import ssl
from http.client import HTTPSConnection
from urllib.parse import urlparse

import certifi
from loguru import logger
from PySide6.QtCore import QObject, QThread, Signal
from semver import Version

from constants import UPDATE_CHECK_URL, UpdateCheckResult
from utils.getAppVersion import get_app_version


class UpdateCheckError(Exception):
    """Base exception for update check errors"""

    def __init__(self, message: str = "An error occurred during update check") -> None:
        self.message = message
        super().__init__(self.message)


class RepositoryNotFoundError(UpdateCheckError):
    """Raised when the GitHub repository or release is not found (404)"""

    def __init__(self, message: str = "GitHub repository or release not found", status_code: int = 404) -> None:
        self.status_code = status_code
        super().__init__(message)


class RateLimitExceededError(UpdateCheckError):
    """Raised when GitHub API rate limit is exceeded (403)"""

    def __init__(
        self, message: str = "GitHub API rate limit exceeded or access forbidden", status_code: int = 403
    ) -> None:
        self.status_code = status_code
        super().__init__(message)


class UpdateChecker(QObject):
    """A thread-based update checker that doesn't block the GUI."""

    updateCheckComplete = Signal(UpdateCheckResult)

    def __init__(self) -> None:
        super().__init__()
        self._thread = QThread()
        self.moveToThread(self._thread)
        self._thread.started.connect(self._check_for_updates)

    def start(self) -> None:
        """Start the update check in a separate thread."""
        self._thread.start()

    def _check_for_updates(self) -> None:
        """Internal method that performs the actual update check."""
        result = self.checkForUpdates()
        self.updateCheckComplete.emit(result)
        self._thread.quit()

    @staticmethod
    def checkForUpdates() -> UpdateCheckResult:
        """Check for updates by comparing the current app version with the remote version."""
        current_app_version = get_app_version()
        logger.debug(f"App version: {current_app_version}")

        parsed_url = urlparse(UPDATE_CHECK_URL)

        try:
            # Create SSL context with certifi - works on all platforms
            context = ssl.create_default_context(cafile=certifi.where())
            conn = HTTPSConnection(parsed_url.netloc, context=context)

            # Add User-Agent header to avoid GitHub API rate limiting issues
            headers = {"User-Agent": f"Koncentro/{current_app_version}", "Accept": "application/json"}

            try:
                conn.request("GET", parsed_url.path, headers=headers)
            except OSError as e:
                if e.errno in [101, -3, 110, 111, 113]:  # Handle specific network-related errors
                    raise ConnectionError(f"Network error occurred: {e.strerror}")
                raise e  # Re-raise other OSErrors

            response = conn.getresponse()

            if response.status == 404:
                raise RepositoryNotFoundError()
            elif response.status == 403:
                raise RateLimitExceededError()
            elif response.status != 200:
                raise Exception(f"HTTP error occurred: {response.status} {response.reason}")

            # Parse JSON response from GitHub API
            github_data = json.loads(response.read().decode("utf-8"))

            tag_name = github_data.get("tag_name", "")
            if tag_name and tag_name.startswith("v"):
                remote_app_version = tag_name[1:]  # Remove the 'v' prefix
            else:
                remote_app_version = tag_name

            logger.debug(f"Remote version from GitHub: {remote_app_version}")

            # Convert versions to semver Version instances for proper comparison
            current_ver = Version.parse(current_app_version)
            remote_ver = Version.parse(remote_app_version)

            if remote_ver > current_ver:
                logger.warning(f"New version available: {remote_app_version}")
                return UpdateCheckResult.UPDATE_AVAILABLE
            else:
                logger.debug("App is up to date")
                return UpdateCheckResult.UP_TO_DATE

        except ConnectionError as conn_err:
            logger.error(f"Failed to check for updates: {conn_err}")
            return UpdateCheckResult.NETWORK_UNREACHABLE
        except RepositoryNotFoundError as repo_err:
            logger.error(f"Repository not found: {repo_err}")
            return UpdateCheckResult.UPDATE_URL_DOES_NOT_EXIST
        except RateLimitExceededError as rate_limit_err:
            logger.error(f"Rate limit exceeded: {rate_limit_err}")
            return UpdateCheckResult.RATE_LIMITED
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return UpdateCheckResult.UNKNOWN_ERROR
        finally:
            if "conn" in locals():
                conn.close()
