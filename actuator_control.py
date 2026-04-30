import argparse
import time

import serial


DEFAULT_PORT = "/dev/ttyACM0"
DEFAULT_BAUD = 115200
ACTUATOR_ID = 99


def command(actuator_id, value):
    return f"z{int(actuator_id):02d}{value:05.2f}x\n"


def send_actuator(ser, actuator_id, value):
    value = max(-1.0, min(1.0, float(value)))
    cmd = command(actuator_id, value)
    print(cmd.strip())
    ser.write(cmd.encode())
    ser.flush()


def move_for(ser, actuator_id, direction, duration, power, step):
    if direction == "forward":
        value = abs(power)
    elif direction == "back":
        value = -abs(power)
    else:
        raise ValueError("direction must be 'forward' or 'back'")

    send_actuator(ser, actuator_id, value)

    remaining = float(duration)
    while remaining > 0:
        sleep_time = min(step, remaining)
        time.sleep(sleep_time)
        remaining -= sleep_time

    send_actuator(ser, actuator_id, 0.0)


def interactive(ser, actuator_id, power, step):
    print("Commands: f [seconds], b [seconds], step [seconds], power [0-1], off, q")
    print(f"Default time step: {step:.2f}s, power: {power:.2f}")

    while True:
        raw = input("> ").strip().lower()
        if not raw:
            continue

        parts = raw.split()
        cmd = parts[0]

        if cmd in ("q", "quit", "exit"):
            send_actuator(ser, actuator_id, 0.0)
            return

        if cmd == "off":
            send_actuator(ser, actuator_id, 0.0)
            continue

        if cmd == "step":
            step = float(parts[1])
            print(f"Default time step: {step:.2f}s")
            continue

        if cmd == "power":
            power = max(0.0, min(1.0, float(parts[1])))
            print(f"Power: {power:.2f}")
            continue

        if cmd in ("f", "forward", "b", "back"):
            direction = "forward" if cmd in ("f", "forward") else "back"
            duration = float(parts[1]) if len(parts) > 1 else step
            move_for(ser, actuator_id, direction, duration, power, step)
            continue

        print("Unknown command")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Timed forward/back control for the linear actuator."
    )
    parser.add_argument("--port", default=DEFAULT_PORT)
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    parser.add_argument("--id", type=int, default=ACTUATOR_ID)
    parser.add_argument("--power", type=float, default=1.0)
    parser.add_argument("--step", type=float, default=0.25)
    parser.add_argument(
        "direction",
        nargs="?",
        choices=("forward", "back"),
        help="Run one timed movement instead of opening the interactive prompt.",
    )
    parser.add_argument(
        "duration",
        nargs="?",
        type=float,
        help="Seconds to run when direction is provided.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    power = max(0.0, min(1.0, args.power))
    step = max(0.01, args.step)

    with serial.Serial(args.port, args.baud, timeout=1) as ser:
        time.sleep(2)

        try:
            if args.direction:
                if args.duration is None:
                    raise SystemExit("duration is required when direction is provided")
                move_for(ser, args.id, args.direction, args.duration, power, step)
            else:
                interactive(ser, args.id, power, step)
        except KeyboardInterrupt:
            print()
            send_actuator(ser, args.id, 0.0)


if __name__ == "__main__":
    main()
