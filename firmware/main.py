import asyncio
import json
import sys

from machine import Pin, PWM
from picozero import Servo, pico_led

from protocol import decode_frame
from config_validation import validate

with open("rov.json") as config_file:
    CONFIG = json.load(config_file)

validate(CONFIG)

THRUSTER_NEUTRAL = float(CONFIG["thruster_neutral"])
THRUSTER_MIN_MS = float(CONFIG["thruster_pulse_ms"]["min"])
THRUSTER_MAX_MS = float(CONFIG["thruster_pulse_ms"]["max"])
SERVO_MIN_MS = float(CONFIG["servo_pulse_ms"]["min"])
SERVO_MAX_MS = float(CONFIG["servo_pulse_ms"]["max"])

ACTUATOR = CONFIG.get("actuator")
SPEED_PIN = None


class DirectionPin:
    def __init__(self, pin):
        self._pin = Pin(pin, Pin.OUT)
        self.value = 0

    @property
    def value(self):
        return self._pin.value()

    @value.setter
    def value(self, value):
        self._pin.value(1 if float(value) >= 0.5 else 0)


class SpeedPin:
    def __init__(self, pin, freq):
        self._pwm = PWM(Pin(pin))
        self._pwm.freq(freq)
        self.value = 0

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = max(0, min(1, float(value)))
        self._pwm.duty_u16(int(self._value * 65535))


MOTOR_LOOKUP = {}
SERVO_LIMITS = {}

for _name, _thruster in CONFIG["thrusters"].items():
    _pin = int(_thruster["pin"])
    MOTOR_LOOKUP[_pin] = Servo(
        _pin,
        min_pulse_width=THRUSTER_MIN_MS / 1000,
        max_pulse_width=THRUSTER_MAX_MS / 1000,
    )

for _name, _servo in (CONFIG.get("aux_servos") or {}).items():
    _pin = int(_servo["pin"])
    MOTOR_LOOKUP[_pin] = Servo(
        _pin,
        min_pulse_width=SERVO_MIN_MS / 1000,
        max_pulse_width=SERVO_MAX_MS / 1000,
    )
    SERVO_LIMITS[_pin] = (float(_servo["min"]), float(_servo["max"]))

if ACTUATOR:
    DIRECTION_PIN = int(ACTUATOR["direction_pin"])
    SPEED_PIN = int(ACTUATOR["speed_pin"])
    MOTOR_LOOKUP[DIRECTION_PIN] = DirectionPin(DIRECTION_PIN)
    MOTOR_LOOKUP[SPEED_PIN] = SpeedPin(SPEED_PIN, int(ACTUATOR["pwm_freq"]))


def safe_output_value(pin, value):
    if pin in SERVO_LIMITS:
        low, high = SERVO_LIMITS[pin]
        return max(low, min(high, value))
    return value


def apply_frame(line):
    updates = decode_frame(line)
    for pin, value in updates:
        device = MOTOR_LOOKUP.get(pin)
        if device is not None:
            device.value = safe_output_value(pin, value)


def neutralize():
    for _thruster in CONFIG["thrusters"].values():
        MOTOR_LOOKUP[int(_thruster["pin"])].value = THRUSTER_NEUTRAL
    if SPEED_PIN is not None:
        MOTOR_LOOKUP[SPEED_PIN].value = 0


async def read_stdin():
    reader = asyncio.StreamReader(sys.stdin)
    led_on = False
    while True:
        line = await reader.readline()
        if not line:
            break
        try:
            apply_frame(line.decode())
            if led_on:
                pico_led.off()
                led_on = False
            else:
                pico_led.on()
                led_on = True
        except Exception:
            pico_led.on()


try:
    asyncio.run(read_stdin())
except KeyboardInterrupt:
    pass
finally:
    neutralize()
