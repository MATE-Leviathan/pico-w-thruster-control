import argparse
import glob
import re
import shutil
import subprocess
import time
from pathlib import Path

try:
    import cv2
except ImportError:
    cv2 = None

VIDEO_ROOT = Path("systemscheck_videos")
CAMERA_NAME = "exploreHD USB Camera"
EXPECTED_CAMERAS = 4


def video_device_sort_key(device_path):
    match = re.search(r"video(\d+)$", device_path)
    return (0, int(match.group(1))) if match else (1, device_path)


def is_capture_video_device(device_path):
    try:
        result = subprocess.run(
            ["v4l2-ctl", "--device", device_path, "--info"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return True

    output = f"{result.stdout}\n{result.stderr}"
    if result.returncode != 0:
        return False

    device_caps = output.split("Device Caps", 1)[-1]
    return "Video Capture" in device_caps


def discover_explorehd_devices_from_v4l2():
    try:
        result = subprocess.run(
            ["v4l2-ctl", "--list-devices"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None

    if result.returncode != 0:
        return None

    cameras = []
    current_is_explorehd = False
    current_devices = []

    def finish_camera():
        if current_is_explorehd and current_devices:
            cameras.append(current_devices[0])

    for line in result.stdout.splitlines():
        if not line.strip():
            finish_camera()
            current_is_explorehd = False
            current_devices = []
            continue

        if not line.startswith(("\t", " ")):
            finish_camera()
            current_is_explorehd = CAMERA_NAME in line
            current_devices = []
            continue

        device_path = line.strip()
        if current_is_explorehd and device_path.startswith("/dev/video"):
            current_devices.append(device_path)

    finish_camera()

    if len(cameras) != EXPECTED_CAMERAS:
        raise RuntimeError(
            f"Expected {EXPECTED_CAMERAS} {CAMERA_NAME}s from v4l2-ctl "
            f"--list-devices, found {len(cameras)}: {cameras}"
        )

    return sorted(cameras, key=video_device_sort_key)


def discover_camera_devices(camera_count=EXPECTED_CAMERAS):
    explorehd_devices = discover_explorehd_devices_from_v4l2()
    if explorehd_devices is not None:
        return explorehd_devices[:camera_count]

    video_devices = sorted(glob.glob("/dev/video*"), key=video_device_sort_key)
    capture_devices = [
        device_path
        for device_path in video_devices
        if is_capture_video_device(device_path)
    ]
    return capture_devices[:camera_count]


def record_camera_clip(device_path, output_path, duration_seconds=5.0):
    if cv2 is None:
        print("OpenCV is not installed; skipping camera recording")
        return False

    capture = cv2.VideoCapture(device_path, cv2.CAP_V4L2)
    if not capture.isOpened():
        print(f"Could not open {device_path}")
        return False

    try:
        end_time = time.monotonic() + duration_seconds
        writer = None
        frame_count = 0

        while time.monotonic() < end_time:
            ok, frame = capture.read()
            if not ok or frame is None:
                time.sleep(0.02)
                continue

            if writer is None:
                height, width = frame.shape[:2]
                fps = capture.get(cv2.CAP_PROP_FPS)
                if fps <= 0 or fps > 120:
                    fps = 20.0
                fourcc = cv2.VideoWriter_fourcc(*"MJPG")
                writer = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))
                if not writer.isOpened():
                    print(f"Could not create {output_path}")
                    return False

            writer.write(frame)
            frame_count += 1

        if writer is not None:
            writer.release()

        if frame_count == 0:
            print(f"No frames captured from {device_path}")
            return False

        print(f"Recorded {frame_count} frames from {device_path} to {output_path}")
        return True
    finally:
        capture.release()


def clear_camera_check_videos(output_root=VIDEO_ROOT):
    output_root.mkdir(parents=True, exist_ok=True)

    for path in output_root.iterdir():
        if path.is_dir():
            shutil.rmtree(path)
        else:
            path.unlink()


def record_camera_check_videos(duration_seconds=5.0):
    if cv2 is None:
        print("OpenCV is not installed; skipping camera recording")
        return

    clear_camera_check_videos()

    output_dir = VIDEO_ROOT / "latest"
    output_dir.mkdir(parents=True, exist_ok=True)

    camera_devices = discover_camera_devices(camera_count=EXPECTED_CAMERAS)
    print(f"Camera capture devices: {', '.join(camera_devices) or 'none found'}")

    if len(camera_devices) < EXPECTED_CAMERAS:
        print(f"Expected {EXPECTED_CAMERAS} camera capture devices, found {len(camera_devices)}")

    for camera_number, device_path in enumerate(camera_devices, start=1):
        video_number = Path(device_path).name.replace("video", "")
        output_path = output_dir / f"camera_{camera_number}_video{video_number}.avi"
        record_camera_clip(device_path, output_path, duration_seconds)

    print(f"Camera clips are in {output_dir.resolve()}")


def parse_args():
    parser = argparse.ArgumentParser(description="Record clips from the exploreHD cameras.")
    parser.add_argument(
        "--duration",
        type=float,
        default=5.0,
        help="Seconds to record from each camera.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    record_camera_check_videos(args.duration)


if __name__ == "__main__":
    main()
