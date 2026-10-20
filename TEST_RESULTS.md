# Executed software checks

Date: 2026-10-20. Host: Windows x64; project-local virtual environment.
Python 3.12.14, OpenCV 4.14.0 (opencv-python 4.14.0.94), NumPy 2.5.4.

- Initial test discovery failed because the bundled Python runtime lacked cv2.
- Created .venv and installed requirements.txt successfully.
- .venv/Scripts/python.exe -m unittest discover -s tests -v:
  PASS, 12 tests in 0.105 seconds.
- .venv/Scripts/python.exe -m compileall -q main.py camera config control utils vision tests:
  PASS, no compilation errors.
- .venv/Scripts/python.exe main.py --help:
  PASS, documented CLI options displayed.

The tests cover synthetic lane identification, center, signed deviation and
direction, missing lanes, no stale estimates, clutter, invalid geometry,
configuration validation, deadband/nonfinite handling, and mocked camera
initialization/disconnection cleanup.

No live camera capture, GUI display, snapshot interaction, Raspberry Pi execution,
physical USB unplug, performance benchmark, ESP32 or actuator tests were run.
