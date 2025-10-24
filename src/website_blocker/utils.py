# Copyright: (c) 2018, Aniket Panjwani <aniket@addictedto.tech>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

"""Utility functions to assist setting up port forwarding."""

import os
import signal
from typing import List

import psutil
from loguru import logger


def find_processes_by_name(name: str) -> List[psutil.Process]:
    "Return a list of processes matching 'name'."
    ls: List[psutil.Process] = []
    for p in psutil.process_iter(attrs=["name", "exe", "cmdline"]):
        if (
            name == p.info["name"]
            or p.info["exe"]
            and os.path.basename(p.info["exe"]) == name
            or p.info["cmdline"]
            and p.info["cmdline"][0] == name
        ):
            ls.append(p)
    return ls


def kill_process() -> None:
    logger.debug("Inside kill_process().")
    if os.name == "nt":
        processes: List[psutil.Process] = find_processes_by_name("mitmdump.exe") + find_processes_by_name(
            "mitmproxy.exe"
        )
        for p in processes:
            logger.debug(f"Trying to kill process with pid {p.pid} on Windows.")
            p.kill()  # I couldn't find any way of stopping mitmdump gracefully on Windows
    else:
        processes: List[psutil.Process] = find_processes_by_name("mitmdump") + find_processes_by_name("mitmproxy")
        # list all processes with id and name
        for p in processes:
            logger.debug(f"Found process with pid {p.pid} and name {p.info['name']}.")
        # if no process is found then
        if not processes:
            logger.debug("No mitmdump/mitmproxy process found.")
            return

        for p in processes:
            try:
                logger.debug(
                    f"Trying to send SIGINT signal to mitmdump with pid {p.pid} on Linux/MacOS inside kill_process()."
                )
                p.send_signal(signal.SIGINT)
            except psutil.AccessDenied:
                logger.error(f"Access denied to kill process with pid {p.pid} with SIGINT.")
                logger.debug(f"Trying to kill process with pid {p.pid} with SIGKILL.")
                p.kill()
            except psutil.NoSuchProcess:
                logger.debug(f"Process with pid {p.pid} does not exist anymore.")
