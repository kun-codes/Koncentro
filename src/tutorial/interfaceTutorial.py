from collections.abc import Callable
from typing import List

from loguru import logger
from PySide6.QtCore import QObject, QTimer
from qfluentwidgets import FluentWindow

from constants import InterfaceType


class InterfaceTutorial(QObject):
    def __init__(self, main_window: FluentWindow, interface_type: InterfaceType) -> None:
        self.main_window = main_window
        self.current_step = 0
        self.interface_type = interface_type
        self.tutorial_steps: List[Callable[[], None]] = []
        self.teaching_tips = []

    def start(self) -> None:
        if self.current_step < len(self.tutorial_steps):
            if self.current_step == 0:
                QTimer.singleShot(1000, self.tutorial_steps[self.current_step])  # wait for 1 second before showing
                # the first step
            else:
                self.tutorial_steps[self.current_step]()

    def next_step(self) -> None:
        logger.debug(f"Next step: {self.current_step}")
        self.current_step += 1
        self.start()
