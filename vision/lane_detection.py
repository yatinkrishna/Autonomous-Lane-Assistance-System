"""Fit straight lane boundaries to filtered probabilistic Hough segments.

This heuristic assumes a forward-facing, approximately centered camera and
straight, converging markings. It is not a confidence-certified road detector.
"""
from dataclasses import dataclass
from typing import Optional
import cv2
import numpy as np
from config.settings import Settings

@dataclass(frozen=True)
class Boundary:
    bottom: tuple[float, float]
    top: tuple[float, float]

@dataclass(frozen=True)
class LaneEstimate:
    left: Optional[Boundary]
    right: Optional[Boundary]
    lane_center: Optional[float]
    vehicle_center: float
    deviation_px: Optional[float]
    sample_y: float
    reason: str

def _fit(segments, y_bottom: float, y_top: float) -> Optional[Boundary]:
    if not segments:
        return None
    # Fit x = a*y+b so near-vertical lanes do not cause unstable division.
    points, weights = [], []
    for x1, y1, x2, y2 in segments:
        length = np.hypot(x2-x1, y2-y1)
        points.extend(((x1, y1), (x2, y2)))
        weights.extend((length, length))
    points = np.asarray(points, dtype=float)
    matrix = np.column_stack((points[:, 1], np.ones(len(points))))
    weight = np.sqrt(np.asarray(weights))
    a, b = np.linalg.lstsq(matrix * weight[:, None], points[:, 0] * weight, rcond=None)[0]
    return Boundary((float(a*y_bottom+b), y_bottom), (float(a*y_top+b), y_top))

def detect_lanes(roi_edges: np.ndarray, settings: Settings) -> LaneEstimate:
    if roi_edges.ndim != 2 or roi_edges.size == 0:
        raise ValueError("Expected a nonempty single-channel edge image")
    height, width = roi_edges.shape
    vehicle = (width - 1) / 2
    bottom = max(p[1] for p in settings.roi) * (height - 1)
    top = min(p[1] for p in settings.roi) * (height - 1)
    segments = cv2.HoughLinesP(roi_edges, 1, np.pi/180, settings.hough_threshold,
                              minLineLength=settings.min_line_length,
                              maxLineGap=settings.max_line_gap)
    left_segments, right_segments = [], []
    if segments is not None:
        for x1, y1, x2, y2 in segments.reshape(-1, 4):
            dx, dy = float(x2-x1), float(y2-y1)
            if dx == 0:
                continue
            slope = dy / dx
            if not settings.min_abs_slope <= abs(slope) <= settings.max_abs_slope:
                continue
            midpoint = (x1+x2)/2
            if slope < 0 and midpoint < vehicle:
                left_segments.append((x1,y1,x2,y2))
            elif slope > 0 and midpoint > vehicle:
                right_segments.append((x1,y1,x2,y2))
    left, right = _fit(left_segments, bottom, top), _fit(right_segments, bottom, top)
    reason = "missing lane boundary"
    center = deviation = None
    if left is not None and right is not None:
        lane_width = right.bottom[0] - left.bottom[0]
        valid = (0 <= left.bottom[0] < right.bottom[0] < width
                 and 0 <= left.top[0] < right.top[0] < width
                 and settings.min_lane_width_fraction*width <= lane_width
                 <= settings.max_lane_width_fraction*width
                 and right.top[0]-left.top[0] < lane_width)
        reason = "valid" if valid else "implausible lane geometry"
        if valid:
            center = (left.bottom[0]+right.bottom[0])/2
            deviation = vehicle-center
    return LaneEstimate(left, right, center, vehicle, deviation, bottom, reason)
