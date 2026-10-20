"""Validated, immutable runtime configuration. ROI coordinates are normalized."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Settings:
    camera_index: int = 0
    width: int = 640
    height: int = 480
    blur_kernel: int = 5
    canny_low: int = 50
    canny_high: int = 150
    roi: tuple = ((0.05, 0.98), (0.40, 0.58), (0.60, 0.58), (0.95, 0.98))
    hough_threshold: int = 25
    min_line_length: int = 35
    max_line_gap: int = 30
    min_abs_slope: float = 0.4
    max_abs_slope: float = 8.0
    min_lane_width_fraction: float = 0.20
    max_lane_width_fraction: float = 0.95
    steering_deadband_px: float = 20.0

    def __post_init__(self):
        if self.camera_index < 0 or self.width < 32 or self.height < 32:
            raise ValueError("Camera index must be nonnegative; dimensions must be >= 32")
        if self.blur_kernel < 1 or self.blur_kernel % 2 != 1:
            raise ValueError("Blur kernel must be a positive odd integer")
        if not 0 <= self.canny_low < self.canny_high <= 255:
            raise ValueError("Require 0 <= Canny low < high <= 255")
        if len(self.roi) < 3 or any(not 0 <= v <= 1 for p in self.roi for v in p):
            raise ValueError("ROI needs at least three normalized vertices")
        if not 0 < self.min_abs_slope < self.max_abs_slope:
            raise ValueError("Invalid slope range")
        if not 0 < self.min_lane_width_fraction < self.max_lane_width_fraction <= 1:
            raise ValueError("Invalid lane width fractions")
        if min(self.hough_threshold, self.min_line_length) <= 0 or self.max_line_gap < 0:
            raise ValueError("Invalid Hough parameters")
        if self.steering_deadband_px < 0:
            raise ValueError("Deadband must be nonnegative")
