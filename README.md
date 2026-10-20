# Raspberry Pi 5 Lane Assistance — Phase 1

USB camera processing and advisory steering for a model car. This phase has no
motor, servo, GPIO or ESP32 communication code. Obstacle avoidance is future work.

## Raspberry Pi OS installation

Use Raspberry Pi OS with Python 3.9 or newer (a current 64-bit desktop image is
recommended for the GUI). Connect a USB webcam and run these commands from this
project directory:

```bash
sudo apt update
sudo apt install python3-opencv python3-numpy python3-venv
python3 -m venv --system-site-packages .venv
source .venv/bin/activate
python3 -c "import cv2, numpy; print(cv2.__version__, numpy.__version__)"
python3 main.py
```

The virtual environment exposes the apt-installed OpenCV and NumPy packages.
Do not run pip with sudo or use --break-system-packages. Do not install
requirements.txt in this Pi environment: pip does not recognize apt's cv2
distribution as opencv-python and may install a second copy. The requirements
file is for a separate desktop environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

On Windows activate with `.venv\Scripts\Activate.ps1` and use `python` in
place of `python3`. Choose the virtual environment interpreter in VS Code.
Virtual environments are machine-specific; recreate one on the Pi rather than
copying the Windows environment.

Installation guidance follows the
[Raspberry Pi OS documentation](https://www.raspberrypi.com/documentation/computers/os.html)
and the Raspberry Pi project's
[system-site-packages guidance](https://github.com/raspberrypi/pylibcamera/blob/main/README.md).

## Execution and controls

```bash
python3 main.py
python3 main.py --camera 1 --width 640 --height 480 --debug
python3 main.py --canny-low 40 --canny-high 130 --save-dir captures
python3 main.py --headless
python3 main.py --help
```

Two windows display the unmodified webcam feed and annotated detections.
Q quits, S saves timestamped raw and annotated PNGs. Closing the annotated
window also exits. Ctrl+C stops either mode. Debug mode adds grayscale, Canny
edges and masked ROI views. Headless mode has no windows or keyboard capture
saving; it logs measurements every 60 frames. Use a graphical desktop session
for GUI operation; an SSH-only session normally requires --headless.

A capture initialization/read failure logs an error, releases resources, and
exits with status 1. There is no automatic reconnect or retained steering
estimate. Reconnect the webcam and restart. GUI failure is also reported;
use a GUI-enabled OpenCV installation and desktop session. A failed snapshot
is logged without stopping capture.

## Modules

- main.py: command-line configuration, capture loop, timing, saving and cleanup.
- config/settings.py: immutable defaults and configuration validation.
- camera/webcam.py: OpenCV VideoCapture ownership, negotiated size logging,
  initialization and read failure handling.
- vision/preprocessing.py: grayscale, Gaussian blur, Canny and polygon ROI.
- vision/lane_detection.py: probabilistic Hough segments, slope/side filtering,
  length-weighted boundary fits and plausibility checks.
- control/steering.py: LEFT, RIGHT, CENTER or UNKNOWN suggestions only.
- utils/visualization.py: lane overlay, centers, deviation, status and FPS.
- tests/: synthetic image tests and mock-based camera lifecycle tests.

## Geometry and tuning

Edit Settings in config/settings.py for the ROI polygon, blur kernel, Canny
thresholds, Hough vote threshold, minimum segment length, maximum gap,
accepted slopes, lane width fractions and steering deadband. CLI camera,
resolution and Canny options override defaults. Pixel thresholds should be
retuned if resolution changes.

ROI vertices are fractions of image width and height. Fits and masks use
actual captured dimensions because cameras may negotiate a different size.
The lane center is measured at the bottom ROI row, not at the vanishing point.
Vehicle center assumes the optical center is aligned with the chassis center.

Deviation = vehicle center x - lane center x, in pixels. Positive means the
vehicle is right of lane center and suggests LEFT; negative suggests RIGHT.
Within the inclusive default +/-20 pixel deadband the suggestion is CENTER.
This is not a steering angle or a metric distance.

Left segments have negative image-space slope and lie left of the image
center; right segments have positive slope and lie right of center. Fits
must be ordered, inside the frame, converge upward, and have a plausible
bottom width before a center is reported. Missing or rejected pairs yield
UNKNOWN with no center/deviation; individual observed boundaries may still
be drawn. Every frame is independent: no stale center is reused.

This simple straight-lane heuristic can misidentify shadows, road edges,
intersections and clutter. It assumes both markings are visible and a level,
forward-facing camera. It does not support sharp curves, infer a missing
boundary, estimate confidence, or establish that driving is safe. FPS is a
smoothed processing-loop rate including capture and previous display delay.

## Software tests

From the project directory, with dependencies available:

```bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q main.py camera config control utils vision tests
```

Tests use generated white lane markings on a black image, exercising the
actual preprocessing and Hough pipeline. They cover lane sides, center,
signed deviation, directions, missing boundaries, no stale estimate,
horizontal clutter, geometry rejection and configuration validation.
Camera tests use mocks and do not verify physical hardware.

See TEST_RESULTS.md for checks actually executed during implementation.

## Physical Raspberry Pi checks still required

1. Confirm apt installation, webcam permissions and device index on the Pi.
   If another application owns the camera, close it first.
2. Confirm negotiated capture resolution, GUI rendering, Q/Ctrl+C cleanup,
   snapshot output, and USB unplug behavior.
3. Mount and align the camera; tune ROI, lane widths and thresholds using
   the real track, lighting, markings and chassis.
4. Measure sustained FPS, latency and thermal behavior on the Pi 5.
5. Check left/right sign against the physical camera orientation; mirrored
   feeds or an off-center mount invalidate the default assumptions.

No physical Raspberry Pi, webcam, ESP32, sensor, motor or servo validation
is implied by software test results.

## Future extension boundaries

Camera acquisition, image processing, lane estimates and advisory control
are separate modules. Later phases can consume LaneEstimate in an explicit
controller and add UART transport, ultrasonic sensor records, sensor fusion,
PID control, lane-changing state machines and an independent emergency stop.
They are intentionally absent from Phase 1.
