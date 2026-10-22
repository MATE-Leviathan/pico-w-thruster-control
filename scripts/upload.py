import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from diagnostics import config as rov_config

DEFAULT_PORT = "/dev/ttyACM0"

MAPPING = (
    (rov_config.FIRMWARE_DIR / "config_validation.py", "config_validation.py"),
    (rov_config.FIRMWARE_DIR / "main.py", "main.py"),
    (rov_config.FIRMWARE_DIR / "protocol.py", "protocol.py"),
    (rov_config.FIRMWARE_DIR / "picozero.py", "picozero.py"),
    (rov_config.CONFIG_PATH, "rov.json"),
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Upload firmware to the Pico over USB.")
    parser.add_argument("--port", default=DEFAULT_PORT)
    return parser.parse_args(argv)


def mpremote_command(port, *commands):
    return [sys.executable, "-m", "mpremote", "connect", port, *commands]


def run_mpremote(port, *commands):
    command = mpremote_command(port, *commands)
    print("$ " + " ".join(command))
    return subprocess.run(command).returncode


def upload(port):
    copy_command = []
    for index, (src, dst) in enumerate(MAPPING):
        if index:
            copy_command.append("+")
        copy_command += ["cp", str(src), ":" + dst]

    if run_mpremote(port, *copy_command) != 0:
        print("Upload failed during copy; not restarting the Pico.", file=sys.stderr)
        return 1

    if run_mpremote(port, "reset") != 0:
        print("Copies succeeded but the reset failed.", file=sys.stderr)
        return 1

    print("Upload complete; Pico restarted.")
    return 0


def main(argv=None):
    args = parse_args(argv)

    try:
        config = rov_config.load_config()
        rov_config.validate(config)
    except ValueError as error:
        print(f"Invalid configuration: {error}", file=sys.stderr)
        return 1
    return upload(args.port)


if __name__ == "__main__":
    sys.exit(main())
