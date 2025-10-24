from loguru import logger
from PySide6.QtCore import QObject, QTimer, Signal

from config_values import ConfigValues
from constants import TimerState


class PomodoroTimer(QObject):  # Inherit from QObject to support signals
    """
    Core functionality of the Pomodoro Timer
    """

    # emitted every time the timer state changes, regardless of whether it is due to skipping the duration or not
    # first argument for current timer state, bool is for saying is for saying if timer state has
    # changed due to skipping the duration or not, true if duration is skipped, false otherwise
    timerStateChangedSignal: Signal = Signal(TimerState, bool)
    sessionStoppedSignal: Signal = Signal()
    # only emitted when the timer state changes and corresponding autostart setting is set to false
    waitForUserInputSignal: Signal = Signal()
    sessionPausedSignal: Signal = Signal()
    # emitted when the session is resumed after being paused or after manually starting the session when
    # corresponding autostart setting is set to false
    sessionStartedSignal: Signal = Signal()
    durationSkippedSignal: Signal = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.previous_timer_state: TimerState = TimerState.NOTHING
        self.timer_state: TimerState = TimerState.NOTHING
        self.pomodoro_timer: QTimer = QTimer()
        self.session_progress: float = 0  # would be incremented by 0.5 after every work ended signal is emitted
        # would also be incremented by 0.5 after every break ended signal is emitted
        # starts out at 0 which means that the timer state is NOTHING
        # whole number means that break is going on
        # would be reset to zero after every long break
        self.sessions_completed: int = 0  # would be incremented by 1 after every long break is ended

        self.remaining_time: int = 0  # will change according to BREAK_DURATION, WORK_DURATION, LONG_BREAK_DURATION
        self.timer_resolution: int = 1000  # in milliseconds

        # self.pomodoro_timer.timeout.connect(self.sessionEnded)
        self.pomodoro_timer.timeout.connect(self.decreaseRemainingTime)

    def getTimerState(self) -> TimerState:
        return self.timer_state

    def updateSessionProgress(self, is_skipped: bool = False) -> None:
        """
        Increments the session tracking variable session_progress by 0.5 or resets to 0 depending on the timer state
        """
        logger.debug(f"Session Progress (before): {self.session_progress}")
        logger.debug(f"Timer State (before): {self.timer_state}")

        self.previous_timer_state = self.timer_state

        if self.timer_state == TimerState.WORK:
            if self.session_progress < ConfigValues.WORK_INTERVALS - 0.5:
                self.session_progress += 0.5
                self.timer_state = TimerState.BREAK
            elif self.session_progress == ConfigValues.WORK_INTERVALS - 0.5:
                self.session_progress += 0.5
                self.timer_state = TimerState.LONG_BREAK
        elif self.timer_state == TimerState.BREAK:
            self.session_progress += 0.5
            self.timer_state = TimerState.WORK
        elif self.timer_state == TimerState.NOTHING:
            self.session_progress += 0.5
            self.timer_state = TimerState.WORK
        elif self.timer_state == TimerState.LONG_BREAK:
            self.session_progress += 0.5  # Back to work after long_break
            self.timer_state = TimerState.WORK

        if self.session_progress > ConfigValues.WORK_INTERVALS:
            self.session_progress = (
                self.session_progress % ConfigValues.WORK_INTERVALS
            )  # for example in case work intervals is
            # 2 and during long break it was 2 and then after it, it becomes 2.5 which is not a valid state, so we get
            # the remainder which is 0.5

        if self.previous_timer_state != self.timer_state:
            self.timerStateChangedSignal.emit(self.timer_state, is_skipped)

        logger.debug(f"Session Progress (after): {self.session_progress}")
        logger.debug(f"Timer State (after): {self.timer_state}")

    def setDuration(self) -> None:
        """
        Starts the timer for the work session, break session or long break session
        """
        if self.remaining_time > 0 and not self.pomodoro_timer.isActive():  # if timer is paused
            logger.info("Resuming timer")
            self.pomodoro_timer.start(self.timer_resolution)
        else:  # if timer is not paused then set timer duration and start timer
            if self.getTimerState() == TimerState.NOTHING:
                logger.info("In Nothing State")
            elif self.getTimerState() == TimerState.WORK:
                logger.debug(f"Work duration: {ConfigValues.WORK_DURATION}")
                self.setTimerDuration(ConfigValues.WORK_DURATION * 60 * 1000)
                logger.info("Starting work session")
            elif self.getTimerState() == TimerState.BREAK:
                logger.debug(f"Break duration: {ConfigValues.BREAK_DURATION}")
                self.setTimerDuration(ConfigValues.BREAK_DURATION * 60 * 1000)
                logger.info("Starting break session")
            elif self.getTimerState() == TimerState.LONG_BREAK:
                logger.debug(f"Long break duration: {ConfigValues.LONG_BREAK_DURATION}")
                self.setTimerDuration(ConfigValues.LONG_BREAK_DURATION * 60 * 1000)
                logger.info("Starting long break session")

    def startDuration(self) -> None:
        self.pomodoro_timer.start(self.timer_resolution)
        self.sessionStartedSignal.emit()

    def pauseDuration(self) -> None:
        self.previous_timer_state = self.timer_state
        logger.info("Timer is paused now")
        self.pomodoro_timer.stop()
        self.sessionPausedSignal.emit()

    def durationEnded(self, isSkipped: bool = False) -> None:
        """
        Handles the end of the work session, break session or long break session
        """
        # increment sessions_completed if long break has ended
        if self.timer_state == TimerState.LONG_BREAK:
            self.sessions_completed += 1
            logger.info(f"Sessions completed: {self.sessions_completed}")

        self.pomodoro_timer.stop()
        if self.timer_state == TimerState.WORK:
            self.updateSessionProgress(isSkipped)
            self.setDuration()
            if isSkipped:  # if session is skipped then value of autostart_break is not checked as it doesn't matter
                # and start the next duration automatically
                self.startDuration()
                return
            elif ConfigValues.AUTOSTART_BREAK:
                logger.info("Auto-starting break session")
                self.startDuration()
            else:
                logger.info("Waiting for user input after ending work session")
                self.waitForUserInputSignal.emit()  # resets the pause resume button to its checked state
                # if self.previous_timer_state != self.timer_state:
                #     self.timerStateChangedSignal.emit(self.timer_state)
        elif self.timer_state in [TimerState.BREAK, TimerState.LONG_BREAK]:
            self.updateSessionProgress(isSkipped)
            self.setDuration()
            if isSkipped:
                self.startDuration()
                return
            if ConfigValues.AUTOSTART_WORK:
                logger.info("Auto-starting work session")
                self.startDuration()
            else:
                logger.info("Waiting for user input after ending break session")
                self.waitForUserInputSignal.emit()
                # if self.previous_timer_state != self.timer_state:
                #     self.timerStateChangedSignal.emit(self.timer_state)

    def skipDuration(self) -> None:
        # self.previous_timer_state = self.timer_state  # should I remove it???
        if self.remaining_time == 0 and not self.pomodoro_timer.isActive():
            # TODO: Implement skipping duration when timer is not doing anything
            raise NotImplementedError("Skipping duration when timer is not doing anything isn't implemented currently")
            logger.info("Skipping duration when timer is doing nothing")
        else:
            logger.info("Skipping duration when timer is doing something")
            self.remaining_time = 0
            self.durationEnded(isSkipped=True)

        self.durationSkippedSignal.emit()

    def setTimerDuration(self, duration: int) -> None:
        """
        for setting the duration of the timer
        """
        self.remaining_time = duration

    def decreaseRemainingTime(self) -> None:
        """
        For decreasing the remaining time by timer_resolution
        """

        self.remaining_time -= self.timer_resolution

        if self.remaining_time < 0:
            self.durationEnded()
            return

        self.pomodoro_timer.start(self.timer_resolution)

    def getRemainingTime(self) -> int:
        """
        Returns the remaining time in milliseconds for the duration
        """
        return self.remaining_time

    def pomodoroSessionEnded(self) -> None:
        logger.info("Pomodoro Session Ended")
        self.stopSession()

    def stopSession(self) -> None:
        logger.info("Stopping Pomodoro Session")
        self.previous_timer_state = self.timer_state
        self.sessions_completed = 0
        self.pomodoro_timer.stop()
        self.remaining_time = 0
        self.session_progress = 0
        self.timer_state = TimerState.NOTHING
        if self.previous_timer_state != self.timer_state:
            self.timerStateChangedSignal.emit(self.timer_state, False)
        self.sessionStoppedSignal.emit()
        logger.debug(f"Session Progress: {self.session_progress}")

    def getSessionProgress(self) -> float:
        return self.session_progress

    def getSessionsCompleted(self) -> int:
        return self.sessions_completed

    # def skipDuration(self):
    #     logger.info("Skipping duration")
    #     self.timer_duration = 0
    #     self.session_progress += 0.5
    #     self.durationEnded()
