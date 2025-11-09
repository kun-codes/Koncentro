from collections.abc import Callable
from typing import TYPE_CHECKING, Any, List, Union

from loguru import logger
from PySide6.QtCore import QObject, QTimer

from constants import InterfaceType
from prefabs.targetClickTeachingTip import TargetClickTeachingTip
from prefabs.transientPopupTeachingTip import TransientPopupTeachingTip

if TYPE_CHECKING:
    from mainWindow import MainWindow


class TeachingTipList(list):
    def __init__(
        self, onAdded: Callable[[Union[TargetClickTeachingTip, TransientPopupTeachingTip]], None], *args: Any
    ) -> None:
        super().__init__(*args)
        self._onAdded = onAdded

    def append(self, item: Union[TargetClickTeachingTip, TransientPopupTeachingTip]) -> None:
        super().append(item)
        if self._onAdded:
            try:
                self._onAdded(item)
            except Exception:
                logger.exception("Error in teaching tip on_added handler")


class InterfaceTutorial(QObject):
    def __init__(self, main_window: "MainWindow", interface_type: InterfaceType) -> None:
        self.main_window = main_window
        self.current_step = 0
        self.interface_type = interface_type
        self.tutorial_steps: List[Callable[[], None]] = []
        self.teaching_tips = TeachingTipList(onAdded=self.connectSignalToSlotsForTeachingTip)

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

    def _last_step(self) -> None:
        """
        Override this in child classes
        """
        raise NotImplementedError

    def connectSignalToSlotsForTeachingTip(self, tip: Union[TransientPopupTeachingTip, TargetClickTeachingTip]) -> None:
        tip.view.skipButton.clicked.connect(lambda: tip.destroyed.disconnect(self.next_step))
        tip.view.skipButton.clicked.connect(tip._fadeOut)
        tip.view.skipButton.clicked.connect(self._last_step)
