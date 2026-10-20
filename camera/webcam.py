"""USB camera ownership and fail-fast disconnect detection."""
import logging
import cv2
import numpy as np
from config.settings import Settings

class CameraError(RuntimeError):
    """Camera initialization or capture failure."""

class Webcam:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.capture = None

    def __enter__(self):
        try:
            self.capture = cv2.VideoCapture(self.settings.camera_index)
            if not self.capture.isOpened():
                raise CameraError(f"Cannot open USB camera index {self.settings.camera_index}")
            self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.settings.width)
            self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.settings.height)
            logging.info("Camera reports %dx%d", self.capture.get(cv2.CAP_PROP_FRAME_WIDTH),
                         self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            return self
        except Exception:
            self.close()
            raise

    def read(self) -> np.ndarray:
        if self.capture is None:
            raise CameraError("Camera is not open")
        ok, frame = self.capture.read()
        if not ok or frame is None or frame.size == 0:
            raise CameraError("Camera read failed: disconnected or unavailable")
        return frame

    def close(self):
        if self.capture is not None:
            self.capture.release()
            self.capture = None

    def __exit__(self, exc_type, exc, traceback):
        self.close()
