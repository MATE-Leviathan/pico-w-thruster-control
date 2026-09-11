import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FIRMWARE_DIR = REPO_ROOT / "firmware"
CONFIG_PATH = REPO_ROOT / "config" / "rov.json"

def load_config(path=CONFIG_PATH):
    with open(path) as config_file:
        return json.load(config_file)


def validate(config):
    outputs = list(config["thrusters"].values()) + list(config["aux_servos"].values())

    servo_pins = [int(entry["pin"]) for entry in outputs]
    direction_pin, speed_pin, frequency = actuator(config)

    pins = servo_pins + [direction_pin, speed_pin]
    if any(pin < 0 or pin > 31 for pin in pins):
        raise ValueError("GPIO pin outside 0..31")

    if len(pins) != len(set(pins)):
        raise ValueError("GPIO pins must be unique")

    for key in ("thruster_pulse_ms", "servo_pulse_ms"):
        limits = config[key]
        if not float(limits["min"]) < float(limits["max"]):
            raise ValueError(key + " minimum must be below maximum")


def thrusters(config):
    return [
        (name, int(entry["pin"]), entry.get("position"))
        for name, entry in config["thrusters"].items()
    ]


def aux_servos(config):
    return [
        (name, int(entry["pin"]), float(entry["min"]), float(entry["max"]), float(entry["end"]))
        for name, entry in config["aux_servos"].items()
    ]


def actuator(config):
    entry = config["actuator"]
    return int(entry["direction_pin"]), int(entry["speed_pin"]), int(entry["pwm_freq"])
