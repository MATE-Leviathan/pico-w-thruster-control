import json
from pathlib import Path

import jsonschema

from firmware.config_validation import validate as validate_outputs

REPO_ROOT = Path(__file__).resolve().parent.parent
FIRMWARE_DIR = REPO_ROOT / "firmware"
CONFIG_PATH = REPO_ROOT / "config" / "rov.json"
SCHEMA_PATH = REPO_ROOT / "config" / "rov.schema.json"


def load_config(path=CONFIG_PATH):
    with open(path) as config_file:
        return json.load(config_file)


def validate(config):
    with open(SCHEMA_PATH) as schema_file:
        schema = json.load(schema_file)
    try:
        jsonschema.validate(config, schema)
    except jsonschema.ValidationError as error:
        path = ".".join(str(part) for part in error.absolute_path) or "config"
        raise ValueError(f"{path}: {error.message}") from None
    validate_outputs(config)


def thrusters(config):
    return [
        (name, int(entry["pin"]), entry.get("position"))
        for name, entry in config["thrusters"].items()
    ]


def aux_servos(config):
    return [
        (name, int(entry["pin"]), float(entry["min"]), float(entry["max"]), float(entry["end"]))
        for name, entry in (config.get("aux_servos") or {}).items()
    ]


def actuator(config):
    entry = config.get("actuator")
    if not entry:
        return None
    return int(entry["direction_pin"]), int(entry["speed_pin"]), int(entry["pwm_freq"])
