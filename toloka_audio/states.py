from enum import Enum


class PlayerState(str, Enum):
    """Supported Toloka audio player states detected from UI templates."""

    LOADING = "LOADING"
    PLAY = "PLAY"
    PAUSE = "PAUSE"
    UNKNOWN = "UNKNOWN"


class AutomationMode(str, Enum):
    RUNNING = "RUNNING"
    WAIT_USER_CONFIRMATION = "WAIT_USER_CONFIRMATION"
