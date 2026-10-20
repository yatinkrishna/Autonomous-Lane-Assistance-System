"""Grayscale, blur, edge extraction and normalized polygon masking."""
from dataclasses import dataclass
import cv2
import numpy as np
from config.settings import Settings

@dataclass
class ProcessedFrame:
    gray: np.ndarray
    edges: np.ndarray
    roi: np.ndarray

def preprocess(frame: np.ndarray, settings: Settings) -> ProcessedFrame:
    if frame is None or frame.size == 0 or frame.ndim != 3 or frame.shape[2] != 3:
        raise ValueError("Expected a nonempty BGR image")
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (settings.blur_kernel, settings.blur_kernel), 0)
    edges = cv2.Canny(blurred, settings.canny_low, settings.canny_high)
    height, width = gray.shape
    polygon = np.array([[(round(x * (width - 1)), round(y * (height - 1)))
                         for x, y in settings.roi]], dtype=np.int32)
    mask = np.zeros_like(edges)
    cv2.fillPoly(mask, polygon, 255)
    return ProcessedFrame(gray, edges, cv2.bitwise_and(edges, mask))
