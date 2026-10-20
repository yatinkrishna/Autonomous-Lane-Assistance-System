"""USB webcam lane assistance Phase 1 entry point."""
import argparse
from dataclasses import replace
from datetime import datetime
import logging
from pathlib import Path
import time
import cv2
from camera.webcam import CameraError, Webcam
from config.settings import Settings
from control.steering import suggest_steering
from utils.visualization import render
from vision.lane_detection import detect_lanes
from vision.preprocessing import preprocess

def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--camera", type=int, default=0)
    parser.add_argument("--width", type=int, default=640)
    parser.add_argument("--height", type=int, default=480)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--headless", action="store_true", help="No GUI; stop with Ctrl+C")
    parser.add_argument("--save-dir", type=Path, default=Path("captures"))
    parser.add_argument("--canny-low", type=int, default=50)
    parser.add_argument("--canny-high", type=int, default=150)
    return parser.parse_args()

def save_capture(folder, raw, overlay):
    folder.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    for name, image in (("raw",raw), ("overlay",overlay)):
        path = folder / f"{stamp}_{name}.png"
        if not cv2.imwrite(str(path), image):
            raise OSError(f"Could not save {path}")
    logging.info("Saved capture pair to %s", folder)

def main() -> int:
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    try:
        settings = replace(Settings(), camera_index=args.camera, width=args.width,
                           height=args.height, canny_low=args.canny_low, canny_high=args.canny_high)
        with Webcam(settings) as camera:
            previous = time.perf_counter()
            fps = 0.0
            frame_number = 0
            while True:
                frame = camera.read()
                processed = preprocess(frame, settings)
                lane = detect_lanes(processed.roi, settings)
                direction = suggest_steering(lane.deviation_px, settings.steering_deadband_px)
                now = time.perf_counter()
                instant = 1/max(now-previous, 1e-9)
                fps = instant if fps == 0 else 0.9*fps+0.1*instant
                previous = now
                frame_number += 1
                overlay = render(frame, lane, direction, fps)
                if args.headless:
                    if frame_number % 60 == 0:
                        logging.info("FPS %.1f | %s | deviation %s", fps, direction.value, lane.deviation_px)
                    continue
                cv2.imshow("Original webcam", frame)
                cv2.imshow("Lane assistance", overlay)
                if args.debug:
                    cv2.imshow("Grayscale", processed.gray)
                    cv2.imshow("Edges", processed.edges)
                    cv2.imshow("ROI", processed.roi)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), ord("Q")):
                    break
                if key in (ord("s"), ord("S")):
                    try:
                        save_capture(args.save_dir, frame, overlay)
                    except (OSError, cv2.error) as error:
                        logging.error("Capture save failed: %s", error)
                if cv2.getWindowProperty("Lane assistance", cv2.WND_PROP_VISIBLE) < 1:
                    break
        return 0
    except KeyboardInterrupt:
        logging.info("Stopped by user")
        return 0
    except (CameraError, cv2.error, OSError, ValueError) as error:
        logging.error("%s", error)
        return 1
    finally:
        if not args.headless:
            try:
                cv2.destroyAllWindows()
            except cv2.error:
                pass

if __name__ == "__main__":
    raise SystemExit(main())
