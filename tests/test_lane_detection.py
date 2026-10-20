"""Synthetic integration and geometry tests; no camera required."""
import unittest
from unittest.mock import patch
import cv2
import numpy as np
from config.settings import Settings
from control.steering import Direction, suggest_steering
from vision.preprocessing import preprocess
from vision.lane_detection import detect_lanes

class LaneDetectionTests(unittest.TestCase):
    def setUp(self):
        self.settings = Settings()

    def image(self, offset=0, left=True, right=True):
        image = np.zeros((480,640,3), dtype=np.uint8)
        if left:
            cv2.line(image, (140+offset,479), (280+offset,278), (255,255,255), 8)
        if right:
            cv2.line(image, (500+offset,479), (360+offset,278), (255,255,255), 8)
        return image

    def detect(self, **kwargs):
        return detect_lanes(preprocess(self.image(**kwargs), self.settings).roi, self.settings)

    def test_identification(self):
        lane = self.detect()
        self.assertIsNotNone(lane.left)
        self.assertIsNotNone(lane.right)
        self.assertLess(lane.left.bottom[0], lane.vehicle_center)
        self.assertGreater(lane.right.bottom[0], lane.vehicle_center)

    def test_center(self):
        lane = self.detect()
        self.assertIsNotNone(lane.lane_center)
        self.assertAlmostEqual(lane.lane_center, 320, delta=5)
        self.assertEqual(suggest_steering(lane.deviation_px), Direction.CENTER)

    def test_deviation_and_direction(self):
        for offset, direction in ((35, Direction.RIGHT), (-35, Direction.LEFT)):
            with self.subTest(offset=offset):
                lane = self.detect(offset=offset)
                self.assertIsNotNone(lane.deviation_px)
                self.assertAlmostEqual(lane.deviation_px, -offset, delta=6)
                self.assertEqual(suggest_steering(lane.deviation_px), direction)

    def test_missing_lanes(self):
        for left, right in ((False,True), (True,False), (False,False)):
            with self.subTest(left=left, right=right):
                lane = self.detect(left=left, right=right)
                self.assertIsNone(lane.lane_center)
                self.assertIsNone(lane.deviation_px)
                self.assertEqual(suggest_steering(lane.deviation_px), Direction.UNKNOWN)

    def test_no_stale_estimate(self):
        self.assertIsNotNone(self.detect().lane_center)
        self.assertIsNone(self.detect(left=False, right=False).lane_center)

    def test_invalid_geometry(self):
        segments = np.array([[[300,470,310,300]], [[340,470,330,300]]])
        # Use plausible slopes with an implausibly narrow bottom lane.
        segments = np.array([[[300,470,400,300]], [[340,470,240,300]]])
        with patch("vision.lane_detection.cv2.HoughLinesP", return_value=segments):
            lane = detect_lanes(np.zeros((480,640), np.uint8), self.settings)
        self.assertIsNone(lane.deviation_px)

    def test_horizontal_clutter(self):
        image = np.zeros((480,640,3), np.uint8)
        cv2.line(image, (50,400), (590,400), (255,255,255), 8)
        lane = detect_lanes(preprocess(image, self.settings).roi, self.settings)
        self.assertIsNone(lane.lane_center)

    def test_deadband_and_nonfinite(self):
        self.assertEqual(suggest_steering(20), Direction.CENTER)
        self.assertEqual(suggest_steering(-20), Direction.CENTER)
        self.assertEqual(suggest_steering(float("nan")), Direction.UNKNOWN)

    def test_settings_validation(self):
        with self.assertRaises(ValueError):
            Settings(blur_kernel=4)
        with self.assertRaises(ValueError):
            Settings(canny_low=200, canny_high=100)

if __name__ == "__main__":
    unittest.main()

