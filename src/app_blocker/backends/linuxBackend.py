import os
import signal
import subprocess
from os.path import realpath
from pathlib import Path
from typing import Optional

import app_rummage_py
import psutil
from loguru import logger
from PySide6.QtCore import QSize
from PySide6.QtGui import QGuiApplication, QIcon, QPixmap
from xdg import xdg_data_dirs, xdg_data_home

from app_blocker.appBlockerBackend import AppBlockerBackend, AppKind, InstalledApp
from utils.checkFlatpakSandbox import is_flatpak_sandbox

# TODO: add support for appimages and check support for windows executables running using wine


class LinuxAppBlockerBackend(AppBlockerBackend):
    FLATPAK_PREFIX = "flatpak:"
    SNAP_PREFIX = "snap:"

    def list_installed_apps(self) -> list[InstalledApp]:
        apps: list[InstalledApp] = []
        apps += self._installed_natives()
        apps += self._installed_flatpaks()
        apps += self._installed_snaps()
        return apps

    def find_blocked_pids(self, targets: set[str]) -> list[tuple[str, int]]:
        native_ids, paths, flatpak_ids, snap_names = self._group_targets(targets)

        hits: list[tuple[str, int]] = []
        if native_ids:
            hits += self._running_natives(native_ids)
        if paths:
            hits += self._running_by_path(paths)
        if flatpak_ids:
            for app_id, pids in self._running_flatpaks().items():
                if app_id in flatpak_ids:
                    hits += [(f"{self.FLATPAK_PREFIX}{app_id}", pid) for pid in pids]
        if snap_names:
            for snap_name, pids in self._running_snaps().items():
                if snap_name in snap_names:
                    hits += [(f"{self.SNAP_PREFIX}{snap_name}", pid) for pid in pids]
        return hits

    def terminate_pid(self, pid: int) -> None:
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        except PermissionError:
            logger.warning(f"app blocking: no permission to signal pid {pid}")

    def _group_targets(self, targets: set[str]) -> tuple[set[str], set[str], set[str], set[str]]:
        native_ids: set[str] = set()
        paths: set[str] = set()
        flatpak_ids: set[str] = set()
        snap_names: set[str] = set()

        for target in targets:
            if target.startswith(self.FLATPAK_PREFIX):
                app_id = target[len(self.FLATPAK_PREFIX) :]
                if app_id:
                    flatpak_ids.add(app_id)
            elif target.startswith(self.SNAP_PREFIX):
                snap_name = target[len(self.SNAP_PREFIX) :]
                if snap_name:
                    snap_names.add(snap_name)
            elif os.path.isabs(target):
                paths.add(target)
            else:
                native_ids.add(target)

        return native_ids, paths, flatpak_ids, snap_names

    def _running_natives(self, native_ids: set[str]) -> list[tuple[str, int]]:
        hits: list[tuple[str, int]] = []
        for app in app_rummage_py.running():
            if app["id"] in native_ids:
                hits += [(app["id"], pid) for pid in app["pids"]]
        return hits

    def _running_by_path(self, paths: set[str]) -> list[tuple[str, int]]:
        # /pro/<pid>/exe reports the path after resolving all the symlinks but our blocklist may have the path with
        # an unresolved symlink so we need to match processes with paths with symlinks resolved and not resolved
        exe_to_target: dict[str, str] = {}
        for path in paths:
            exe_to_target[path] = path
            exe_to_target.setdefault(realpath(path), path)

        hits: list[tuple[str, int]] = []
        for proc in psutil.process_iter(["pid", "exe"]):
            exe = proc.info["exe"]
            if exe is None:
                continue
            # an upgraded package unlinks the old binary by the process still runs the old version which report their
            # /proc/<pid>/exe with a " (deleted)" suffix which needs to be removed. Without stripping it, path matching
            # would be wrong
            if exe.endswith(" (deleted)"):
                exe = exe[: -len(" (deleted)")]
            if exe in exe_to_target:
                hits.append((exe_to_target[exe], proc.info["pid"]))
        return hits

    def _flatpak_command(self, *args: str) -> list[str]:
        if is_flatpak_sandbox():
            return ["flatpak-spawn", "--host", "flatpak", *args]
        return ["flatpak", *args]

    def _running_flatpaks(self) -> dict[str, list[int]]:
        try:
            out = subprocess.run(
                self._flatpak_command("ps", "--columns=application,pid"),
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            return {}

        running: dict[str, list[int]] = {}
        for line in out.splitlines():
            parts = line.split()
            if len(parts) >= 2 and parts[-1].isdigit():
                running.setdefault(parts[0], []).append(int(parts[-1]))
        if not running:
            return {}

        # `flatpak ps`'s PID column can report pids that don't exist in the host pid namespace, so the real pids are
        # resolved from /proc/<pid>/root/.flatpak-info that is the same file flatpak tracks instances with
        # https://github.com/flatpak/flatpak/blob/73519c296405/common/flatpak-instance.c#L1202
        host_pids = self._host_pids_by_flatpak_app(set(running))
        return {app_id: host_pids.get(app_id) or reported for app_id, reported in running.items()}

    def _host_pids_by_flatpak_app(self, app_ids: set[str]) -> dict[str, list[int]]:
        found: dict[str, list[int]] = {}
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            try:
                with open(f"/proc/{entry}/root/.flatpak-info", encoding="utf-8", errors="replace") as fh:
                    info = fh.read(4096)
            except OSError:
                continue  # not a flatpak process or it belongs to another user
            app_id = self._app_id_from_flatpak_info(info)
            if app_id not in app_ids:
                continue
            # skip the sandbox supervisors: signaling bwrap tears the sandbox down uncleanly because sandboxed
            # children carry a parent-death signal; flatpak kill also targets the app pid, never bwrap
            # https://github.com/flatpak/flatpak/blob/73519c296405/app/flatpak-builtins-kill.c#L74-L77
            if self._process_comm(int(entry)) == "bwrap":
                continue
            found.setdefault(app_id, []).append(int(entry))
        return found

    def _app_id_from_flatpak_info(self, content: str) -> Optional[str]:
        in_application_section = False
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("["):
                in_application_section = line == "[Application]"
                continue
            if in_application_section and line.startswith("name="):
                return line[len("name=") :]
        return None

    def _process_comm(self, pid: int) -> str:
        try:
            with open(f"/proc/{pid}/comm", encoding="utf-8", errors="replace") as fh:
                return fh.read().strip()
        except OSError:
            return ""

    def _running_snaps(self) -> dict[str, list[int]]:
        apps: dict[str, list[int]] = {}
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            try:
                exe = os.readlink(f"/proc/{entry}/exe")
            except OSError:
                continue
            if not exe.startswith("/snap/"):
                continue
            snap_name = exe[len("/snap/") :].split("/", 1)[0]
            if snap_name in ("bin", "snapd"):
                continue
            apps.setdefault(snap_name, []).append(int(entry))
        return apps

    def _installed_natives(self) -> list[InstalledApp]:
        return [
            InstalledApp(
                app_id=desktop_id,
                app_name=name,
                target=desktop_id,
                kind=AppKind.NATIVE,
                app_icon=self._icon_for_desktop_id(desktop_id),
            )
            for desktop_id, name in app_rummage_py.installed().items()
        ]

    def _installed_flatpaks(self) -> list[InstalledApp]:
        try:
            out = subprocess.run(
                self._flatpak_command("list", "--app", "--columns=application,name"),
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            return []

        apps: list[InstalledApp] = []
        for line in out.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                parts = line.split(None, 1)
            if len(parts) < 2 or "." not in parts[0]:
                continue  # header row or malformed line
            app_id = parts[0].strip()
            apps.append(
                InstalledApp(
                    app_id=app_id,
                    app_name=parts[1].strip(),
                    target=f"{self.FLATPAK_PREFIX}{app_id}",
                    kind=AppKind.FLATPAK,
                    app_icon=self._icon_for_desktop_id(app_id),
                )
            )
        return apps

    def _installed_snaps(self) -> list[InstalledApp]:
        try:
            out = subprocess.run(
                ["snap", "list"],
                capture_output=True,
                text=True,
                check=True,
                timeout=10,
            ).stdout
        except (OSError, subprocess.SubprocessError):
            return []

        apps: list[InstalledApp] = []
        for line in out.splitlines()[1:]:  # skip the header row
            parts = line.split()
            if not parts:
                continue
            snap_name = parts[0]
            apps.append(
                InstalledApp(
                    app_id=snap_name,
                    app_name=snap_name,
                    target=f"{self.SNAP_PREFIX}{snap_name}",
                    kind=AppKind.SNAP,
                    app_icon=self._icon_for_snap(snap_name),
                )
            )
        return apps

    def _desktop_file_dirs(self) -> list[Path]:
        dirs = [xdg_data_home() / "applications"]
        dirs += [base / "applications" for base in xdg_data_dirs()]
        # not every distro exports the flatpak and snapd dirs through XDG_DATA_DIRS
        dirs.append(xdg_data_home() / "flatpak/exports/share/applications")
        dirs.append(Path("/var/lib/flatpak/exports/share/applications"))
        dirs.append(Path("/var/lib/snapd/desktop/applications"))
        return list(dict.fromkeys(dirs))  # dedupe, keeping insertion order

    def _find_desktop_file(self, desktop_id: str) -> Optional[Path]:
        for applications_dir in self._desktop_file_dirs():
            candidate = applications_dir / f"{desktop_id}.desktop"
            if candidate.is_file():
                return candidate
        return None

    def _icon_for_desktop_id(self, desktop_id: str) -> Optional[QPixmap]:
        desktop_file = self._find_desktop_file(desktop_id)
        if desktop_file is None:
            return None
        return self._resolve_icon(self._parse_icon_key(desktop_file))

    def _icon_for_snap(self, snap_name: str) -> Optional[QPixmap]:
        snapd_dir = Path("/var/lib/snapd/desktop/applications")
        if not snapd_dir.is_dir():
            return None
        # snap exported desktop files are named <snap>_<desktopfile>.desktop
        # snapd exports them as DesktopPrefix() (the snap name) + "_" + sanitized basename
        # https://github.com/canonical/snapd/blob/90c6da1b63bb/snap/info.go#L1069
        for desktop_file in sorted(snapd_dir.glob(f"{snap_name}_*.desktop")):
            icon = self._resolve_icon(self._parse_icon_key(desktop_file))
            if icon is not None:
                return icon
        return None

    def _parse_icon_key(self, desktop_file: Path) -> Optional[str]:
        try:
            with open(desktop_file, encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if line.startswith("[") or "=" not in line:
                        continue
                    key, val = line.split("=", 1)
                    if key.strip() == "Icon":
                        return val.strip()
        except OSError:
            return None
        return None

    def _resolve_icon(self, icon_value: Optional[str]) -> Optional[QPixmap]:
        if not icon_value or QGuiApplication.instance() is None:
            return None

        if icon_value.startswith("/"):
            icon = QIcon(icon_value)
        else:
            # flatpak export dirs are not part of Qt's default icon search paths
            QIcon.setThemeSearchPaths(self._icon_search_paths())
            QIcon.setThemeName("hicolor")
            icon = QIcon.fromTheme(icon_value)

        if icon.isNull():
            return None

        pixmap = icon.pixmap(QSize(48, 48))
        return None if pixmap.isNull() else pixmap

    def _icon_search_paths(self) -> list[str]:
        paths = [str(base / "icons") for base in (xdg_data_home(), *xdg_data_dirs())]
        paths += [
            "/usr/share/icons",
            str(xdg_data_home() / "flatpak/exports/share/icons"),
            "/var/lib/flatpak/exports/share/icons",
        ]
        return list(dict.fromkeys(paths))  # dedupe, keeping insertion order
