"""Render detections over a copy; raw capture remains unchanged."""
import cv2
import numpy as np
from vision.lane_detection import LaneEstimate
from control.steering import Direction

def render(frame: np.ndarray, lane: LaneEstimate, direction: Direction, fps: float) -> np.ndarray:
    overlay = frame.copy()
    for boundary, color in ((lane.left, (0,255,0)), (lane.right, (255,100,0))):
        if boundary:
            cv2.line(overlay, tuple(map(round, boundary.bottom)),
                     tuple(map(round, boundary.top)), color, 4)
    y = round(lane.sample_y)
    cv2.line(overlay, (round(lane.vehicle_center), y-35),
             (round(lane.vehicle_center), y), (0,255,255), 2)
    if lane.lane_center is not None:
        cv2.circle(overlay, (round(lane.lane_center), y), 7, (255,0,255), -1)
    deviation = "UNKNOWN" if lane.deviation_px is None else f"{lane.deviation_px:+.1f} px"
    lines = [f"Steering: {direction.value}  Deviation: {deviation}",
             f"FPS: {fps:.1f}  Status: {lane.reason}",
             "Left: green | Right: blue | Lane: magenta | Vehicle: yellow",
             "Q: quit | S: save raw + overlay"]
    cv2.rectangle(overlay, (0,0), (overlay.shape[1]-1, 104), (0,0,0), -1)
    for index, text in enumerate(lines):
        cv2.putText(overlay, text, (8,22+index*24), cv2.FONT_HERSHEY_SIMPLEX,
                    0.48, (255,255,255), 1, cv2.LINE_AA)
    return overlay
