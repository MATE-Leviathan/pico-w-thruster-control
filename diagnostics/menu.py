import argparse
import sys

import questionary
import serial

from diagnostics import config as rov_config
from diagnostics import sequences
from diagnostics.serial_client import DEFAULT_BAUD, Link

DEFAULT_PORT = "/dev/ttyACM0"

MAIN_MENU = [
    "Arm / sound test",
    "Spin test",
    "Servo test",
    "Actuator test",
    "Neutralize thrusters / stop actuator",
    "Exit",
]


def menu_choices(config):
    choices = list(MAIN_MENU)
    if not rov_config.aux_servos(config):
        choices.remove("Servo test")
    if rov_config.actuator(config) is None:
        choices.remove("Actuator test")
        choices[choices.index("Neutralize thrusters / stop actuator")] = "Neutralize thrusters"
    return choices


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Pico W output diagnostic menu.")
    parser.add_argument("--port", default=DEFAULT_PORT)
    parser.add_argument("--baud", type=int, default=DEFAULT_BAUD)
    parser.add_argument("--dry-run", action="store_true", help="Print commands without connecting to hardware.")
    return parser.parse_args(argv)


def choose_thrusters(config):
    thrusters = [(name, pin) for name, pin, _ in rov_config.thrusters(config)]
    options = ["All thrusters, one at a time", "Select one thruster", "Back"]
    choice = questionary.select("Thruster target:", choices=options).ask()
    if choice is None or choice == "Back":
        return None

    if choice == "All thrusters, one at a time":
        return thrusters

    pick = questionary.select(
        "Thruster:", choices=[f"{name} (GP{pin})" for name, pin in thrusters] + ["Back"]
    ).ask()

    for name, pin in thrusters:
        if pick == f"{name} (GP{pin})":
            return [(name, pin)]

    return None


def choose_servos(config):
    servos = rov_config.aux_servos(config)
    options = ["All auxiliary servos, one at a time", "Select one servo", "Back"]
    choice = questionary.select("Servo target:", choices=options).ask()

    if choice is None or choice == "Back":
        return None
    if choice == "All auxiliary servos, one at a time":
        return servos

    pick = questionary.select(
        "Servo:", choices=[f"{name} (GP{pin})" for name, pin, *_ in servos] + ["Back"]
    ).ask()

    for servo in servos:
        if pick == f"{servo[0]} (GP{servo[1]})":
            return [servo]

    return None


def confirm(message):
    return bool(questionary.confirm(message, default=False).ask())


def _run(link, config, action):
    try:
        action()
    except KeyboardInterrupt:
        print("\nInterrupted; neutralizing outputs")
    except Exception as error:
        print(f"Test failed: {error}")
    finally:
        try:
            sequences.neutralize(link, config)
        except Exception as error:
            print(f"Cleanup failed: {error}")


def menu_loop(link, config):
    while True:
        choice = questionary.select("Diagnostic menu:", choices=menu_choices(config)).ask()

        if choice is None or choice == "Exit":
            return

        if choice == "Arm / sound test":
            selected = choose_thrusters(config)
            if selected and confirm(f"Arm {len(selected)} thruster(s) at neutral?"):
                _run(link, config, lambda: sequences.arm_thrusters(link, config, selected))

        elif choice == "Spin test":
            selected = choose_thrusters(config)
            if selected and confirm(f"Spin test {len(selected)} thruster(s)? This moves hardware."):
                _run(link, config, lambda: sequences.spin_thrusters(link, config, selected))

        elif choice == "Servo test":
            selected = choose_servos(config)
            if selected and confirm(f"Move {len(selected)} servo(s) within their limits?"):
                _run(link, config, lambda: sequences.test_servos(link, selected))

        elif choice == "Actuator test":
            if confirm("Run the actuator forward/back test?"):
                _run(link, config, lambda: sequences.test_actuator(link, config))

        elif choice in ("Neutralize thrusters", "Neutralize thrusters / stop actuator"):
            _run(link, config, lambda: sequences.neutralize(link, config))


def main(argv=None):
    args = parse_args(argv)
    try:
        config = rov_config.load_config()
        rov_config.validate(config)
    except ValueError as error:
        print(f"Invalid configuration: {error}", file=sys.stderr)
        return 1
    if args.dry_run:
        print("Dry run: commands are printed only; no hardware is connected.")

    try:
        with Link(args.port, args.baud, dry_run=args.dry_run) as link:
            menu_loop(link, config)

    except serial.SerialException as error:
        print(f"Could not open {args.port}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
