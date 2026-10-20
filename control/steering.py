"""Advisory direction only; no GPIO, UART, motors or servo output."""
from enum import Enum
import math
from typing import Optional

class Direction(str, Enum):
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    CENTER = "CENTER"
    UNKNOWN = "UNKNOWN"

def suggest_steering(deviation_px: Optional[float], deadband_px: float = 20) -> Direction:
    """Positive deviation means vehicle right of lane center: suggest LEFT."""
    if deadband_px < 0:
        raise ValueError("Deadband must be nonnegative")
    if deviation_px is None or not math.isfinite(deviation_px):
        return Direction.UNKNOWN
    if abs(deviation_px) <= deadband_px:
        return Direction.CENTER
    return Direction.LEFT if deviation_px > 0 else Direction.RIGHT
