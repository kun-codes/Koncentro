from typing import TypedDict

class RunningApp(TypedDict):
    id: str
    name: str
    pids: list[int]

def installed() -> dict[str, str]: ...
def running() -> list[RunningApp]: ...
