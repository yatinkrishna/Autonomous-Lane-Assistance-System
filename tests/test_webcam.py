"""Mocked camera error and resource lifecycle checks; no hardware used."""
import unittest
from unittest.mock import Mock, patch
from camera.webcam import CameraError, Webcam
from config.settings import Settings

class WebcamTests(unittest.TestCase):
    @patch("camera.webcam.cv2.VideoCapture")
    def test_initialization_failure_releases(self, factory):
        capture = factory.return_value
        capture.isOpened.return_value = False
        with self.assertRaises(CameraError):
            with Webcam(Settings()):
                pass
        capture.release.assert_called_once()

    @patch("camera.webcam.cv2.VideoCapture")
    def test_disconnect_releases(self, factory):
        capture = factory.return_value
        capture.isOpened.return_value = True
        capture.read.return_value = (False, None)
        with self.assertRaises(CameraError):
            with Webcam(Settings()) as camera:
                camera.read()
        capture.release.assert_called_once()

    def test_unopened_read(self):
        with self.assertRaises(CameraError):
            Webcam(Settings()).read()
