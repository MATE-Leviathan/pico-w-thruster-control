import argparse
import glob
import re
import shutil
import time
import subprocess
from pathlib import Path

import serial

try:
    import cv2
except ImportError:
    cv2 = None

servo_limits = {
    "20": (0.42, 0.54),
    "01": (0.45, 1.00),
}

servo_end_values = {
    "01": 0.54,
}

VIDEO_ROOT = Path("systemscheck_videos")
THRUSTER_PINS = ("26", "07", "16", "03", "15", "11")
DESCENT_THRUSTER_PINS = ("07", "11")
NEUTRAL_THRUSTER_VALUE = 0.50
DESCENT_TEST_DOWN_VALUE = 0.44
DESCENT_TEST_UP_VALUE = 0.56
DESCENT_TEST_STEP = 0.01
DESCENT_TEST_STEP_DELAY_SECONDS = 0.25
DESCENT_TEST_HOLD_SECONDS = 1.0
DESCENT_TEST_CYCLES = 2
THRUSTER_ARM_DELAY_SECONDS = 0.5


def servo_command(pin, value):
    return f"z{pin}{value:04.2f}x\n"


def thruster_command(pin, value):
    return f"z{pin}{value:05.2f}x\n"


def thruster_commands(pins, value):
    return "".join(thruster_command(pin, value) for pin in pins)


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
            current_is_explorehd = "exploreHD USB Camera" in line
            current_devices = []
            continue

        device_path = line.strip()
        if current_is_explorehd and device_path.startswith("/dev/video"):
            current_devices.append(device_path)

    finish_camera()

    if len(cameras) != 4:
        raise RuntimeError(
            f"Expected 4 exploreHD USB cameras from v4l2-ctl --list-devices, "
            f"found {len(cameras)}: {cameras}"
        )

    return sorted(cameras, key=video_device_sort_key)


def discover_camera_devices(camera_count=4):
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

    camera_devices = discover_camera_devices(camera_count=4)
    print(f"Camera capture devices: {', '.join(camera_devices) or 'none found'}")

    if len(camera_devices) < 4:
        print(f"Expected 4 camera capture devices, found {len(camera_devices)}")

    for camera_number, device_path in enumerate(camera_devices, start=1):
        video_number = Path(device_path).name.replace("video", "")
        output_path = output_dir / f"camera_{camera_number}_video{video_number}.avi"
        record_camera_clip(device_path, output_path, duration_seconds)

    print(f"Camera clips are in {output_dir.resolve()}")


def parse_args():
    parser = argparse.ArgumentParser(description="Run thruster, actuator, and servo system checks.")
    parser.add_argument("--port", default="/dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200)
    parser.add_argument(
        "--record-cameras",
        action="store_true",
        help="Record camera check clips. Existing systemscheck videos are deleted first.",
    )
    parser.add_argument("--camera-duration", type=float, default=5.0)
    parser.add_argument(
        "--test-descent",
        action="store_true",
        help="Slowly pulse the vertical thrusters up and down around neutral.",
    )
    return parser.parse_args()


def write_thrusters(ser, pins, value):
    cmd = thruster_commands(pins, value)
    print(cmd, end="")
    ser.write(cmd.encode())


def arm_thrusters_one_at_a_time(ser, pins):
    for pin in pins:
        cmd = thruster_command(pin, NEUTRAL_THRUSTER_VALUE)
        print(cmd, end="")
        ser.write(cmd.encode())
        time.sleep(THRUSTER_ARM_DELAY_SECONDS)


def ramp_thrusters(ser, pins, start_value, end_value):
    direction = 1 if end_value > start_value else -1
    value = start_value

    while value != end_value:
        value += direction * DESCENT_TEST_STEP
        if direction > 0:
            value = min(value, end_value)
        else:
            value = max(value, end_value)

        write_thrusters(ser, pins, value)
        time.sleep(DESCENT_TEST_STEP_DELAY_SECONDS)


def run_descent_test(port, baud):
    ser = serial.Serial(port, baud, timeout=1)

    try:
        time.sleep(3)
        print("Neutralizing all thrusters")
        write_thrusters(ser, THRUSTER_PINS, NEUTRAL_THRUSTER_VALUE)
        time.sleep(1.5)

        for cycle in range(1, DESCENT_TEST_CYCLES + 1):
            print(f"Descent test cycle {cycle}: slow down")
            ramp_thrusters(
                ser,
                DESCENT_THRUSTER_PINS,
                NEUTRAL_THRUSTER_VALUE,
                DESCENT_TEST_DOWN_VALUE,
            )
            time.sleep(DESCENT_TEST_HOLD_SECONDS)
            ramp_thrusters(
                ser,
                DESCENT_THRUSTER_PINS,
                DESCENT_TEST_DOWN_VALUE,
                NEUTRAL_THRUSTER_VALUE,
            )
            time.sleep(DESCENT_TEST_HOLD_SECONDS)

            print(f"Descent test cycle {cycle}: slow up")
            ramp_thrusters(
                ser,
                DESCENT_THRUSTER_PINS,
                NEUTRAL_THRUSTER_VALUE,
                DESCENT_TEST_UP_VALUE,
            )
            time.sleep(DESCENT_TEST_HOLD_SECONDS)
            ramp_thrusters(
                ser,
                DESCENT_THRUSTER_PINS,
                DESCENT_TEST_UP_VALUE,
                NEUTRAL_THRUSTER_VALUE,
            )
            time.sleep(DESCENT_TEST_HOLD_SECONDS)
    finally:
        try:
            write_thrusters(ser, THRUSTER_PINS, NEUTRAL_THRUSTER_VALUE)
        finally:
            ser.close()


def run_system_check(port, baud):
    ser = serial.Serial(port, baud, timeout=1)

    try:
        time.sleep(3)
        # 0 -> fr-1
        # 1 -> ml-5
        #,2 -> bl-4
        # 3 -> br-3
        # 4 -> nothing
        # 5 -> nothing
        # 6 -> fl-6
        # 7 -> mr-2
        # accounted for 1, 2, 3,
        # MAKE VERY SURE TO HAVE PADDING, OTHERWISE COOKED
        all_pins = THRUSTER_PINS
        arm_thrusters_one_at_a_time(ser, all_pins)
        time.sleep(1.5)

        cmd = ""
        for pin in all_pins:
            cmd += f"z{pin}00.75x\n"
            #cmd += f"z{pin}00.50x\n"
        s = time.perf_counter()

        ser.write(cmd.encode())

        time.sleep(0.2)

        cmd = ""
        for pin in all_pins:
            cmd += f"z{pin}00.50x\n"
            print(cmd)

        ser.write(cmd.encode())

        ser.write(b"z2101.00x\n")
        ser.write(b"z2801.00x\n")
        time.sleep(1)

        ser.write(b"z2800.00x\n")
        time.sleep(0.2)

        ser.write(b"z2100.00x\n")
        ser.write(b"z2801.00x\n")
        time.sleep(0.5)

        ser.write(b"z2100.50x\n")
        ser.write(b"z2800.00x\n")

        for pin, (min_value, max_value) in servo_limits.items():
            midpoint = (min_value + max_value) / 2
            end_value = servo_end_values.get(pin, midpoint)

            print(f"Testing servo {pin} safe min {min_value:0.2f}")
            ser.write(servo_command(pin, min_value).encode())
            time.sleep(1)

            print(f"Testing servo {pin} safe max {max_value:0.2f}")
            ser.write(servo_command(pin, max_value).encode())
            time.sleep(1)

            print(f"Ending servo {pin} at {end_value:0.2f}")
            ser.write(servo_command(pin, end_value).encode())
            time.sleep(0.5)
    finally:
        ser.close()


def main():
    args = parse_args()

    if args.record_cameras:
        record_camera_check_videos(args.camera_duration)

    if args.test_descent:
        run_descent_test(args.port, args.baud)
    else:
        run_system_check(args.port, args.baud)


if __name__ == "__main__":
    main()
