import time

from diagnostics.config import actuator, thrusters

ARM_DELAY_SECONDS = 3.0

SPIN_FORWARD_VALUE = 0.75
SPIN_REVERSE_VALUE = 0.25
SPIN_DURATION_SECONDS = 0.4
SPIN_SETTLE_SECONDS = 0.5

SERVO_SETTLE_SECONDS = 1.0

ACTUATOR_POWER = 1.0
ACTUATOR_RUN_SECONDS = 0.5
ACTUATOR_SETTLE_SECONDS = 0.3


def arm_thrusters(link, config, selected):
    neutral = float(config["thruster_neutral"])

    for index, (name, pin) in enumerate(selected):
        print(f"Arming {name} (GP{pin}) at neutral")
        link.send([(pin, neutral)])

        if index < len(selected) - 1:
            time.sleep(ARM_DELAY_SECONDS)


def spin_thrusters(link, config, selected):
    neutral = float(config["thruster_neutral"])

    for name, pin in selected:
        print(f"Spin test {name} (GP{pin}): forward then reverse")
        link.send([(pin, neutral)])
        time.sleep(SPIN_SETTLE_SECONDS)
        link.send([(pin, SPIN_FORWARD_VALUE)])
        time.sleep(SPIN_DURATION_SECONDS)
        link.send([(pin, neutral)])
        time.sleep(SPIN_SETTLE_SECONDS)
        link.send([(pin, SPIN_REVERSE_VALUE)])
        time.sleep(SPIN_DURATION_SECONDS)
        link.send([(pin, neutral)])
        time.sleep(SPIN_SETTLE_SECONDS)


def test_servos(link, selected):
    for name, pin, low, high, end in selected:
        print(f"Servo test {name} (GP{pin}): {low:.2f} then {high:.2f}, end {end:.2f}")
        link.send([(pin, low)])
        time.sleep(SERVO_SETTLE_SECONDS)
        link.send([(pin, high)])
        time.sleep(SERVO_SETTLE_SECONDS)
        link.send([(pin, end)])
        time.sleep(SERVO_SETTLE_SECONDS)


def test_actuator(link, config):
    settings = actuator(config)
    if settings is None:
        raise ValueError("No actuator configured")
    direction_pin, speed_pin, _freq = settings
    print("Actuator test: forward, stop, back, stop")

    link.send([(speed_pin, 0.0)])
    link.send([(direction_pin, 1.0)])
    link.send([(speed_pin, ACTUATOR_POWER)])
    time.sleep(ACTUATOR_RUN_SECONDS)
    link.send([(speed_pin, 0.0)])
    time.sleep(ACTUATOR_SETTLE_SECONDS)

    link.send([(direction_pin, 0.0)])
    link.send([(speed_pin, ACTUATOR_POWER)])
    time.sleep(ACTUATOR_RUN_SECONDS)
    link.send([(speed_pin, 0.0)])


def neutralize(link, config):
    updates = [(pin, float(config["thruster_neutral"])) for _name, pin, _pos in thrusters(config)]
    settings = actuator(config)
    if settings is not None:
        _direction_pin, speed_pin, _freq = settings
        updates.append((speed_pin, 0.0))
    link.send(updates)
