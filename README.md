# Pico W Thruster Control

MicroPython control code for using a Raspberry Pi Pico W as a USB serial
controller for thrusters, servo-style outputs, and a single PWM+direction
actuator.

The main firmware is `main.py`. It reads compact ASCII command frames from USB
stdin, looks up each addressed output, and writes the requested value to the
matching motor object.

## Files

| File | Purpose |
| --- | --- |
| `main.py` | Firmware entry point. Builds the motor lookup table and reads serial commands. |
| `direction_motor.py` | Driver for the PWM+direction actuator output. |
| `picozero.py` | Vendored `picozero` dependency used for `Servo` and the onboard LED. |
| `control.py` | Host-side timing/control script that writes commands to `/dev/ttyACM0`. |
| `test_main.py` | Small local parser check for the fixed-width command format. |
| `servo.py` | Single-servo movement test. |
| `thruster.py` | Single-thruster/servo output test. |

## Current Pin Map

`main.py` defines six servo-style PWM outputs and one separate actuator output.

| Command id | GPIO | Driver | Value range |
| --- | --- | --- | --- |
| `26` | GP26 | `picozero.Servo` | `00.00` to `01.00` |
| `07` | GP7 | `picozero.Servo` | `00.00` to `01.00` |
| `16` | GP16 | `picozero.Servo` | `00.00` to `01.00` |
| `03` | GP3 | `picozero.Servo` | `00.00` to `01.00` |
| `15` | GP15 | `picozero.Servo` | `00.00` to `01.00` |
| `11` | GP11 | `picozero.Servo` | `00.00` to `01.00` |
| `99` | GP28 PWM, GP21 direction | `DirectionMotor` | `-1.00` to `01.00` |

The servo outputs use this pulse range:

```python
Servo(pin, min_pulse_width=0.0011, max_pulse_width=0.0019)
```

For those outputs, `00.50` is the neutral/midpoint value used by `control.py`.
For the actuator, `00.00` turns PWM off.

## Command Protocol

The firmware expects newline-terminated ASCII frames:

```text
zPPVVVVVPPVVVVVx
```

Each frame:

- starts with `z`
- contains one or more fixed-width output updates
- ends with `x`

Each output update is exactly seven characters:

| Field | Width | Meaning | Example |
| --- | --- | --- | --- |
| `PP` | 2 chars | GPIO pin id or actuator id, zero-padded | `07`, `26`, `99` |
| `VVVVV` | 5 chars | Value parsed as a float | `00.50`, `01.00`, `-0.50` |

Examples:

```text
z2600.50x
z2600.500700.501600.50x
z99-0.50x
```

The fixed widths matter. `z0300.50x` is valid; `z030.50x` is not for this
protocol, because the value is only four characters. Positive values should
normally be formatted with two digits before the decimal point and two decimal
places. Negative values should still be five characters, for example `-0.50`.

Pin ids must also be padded to two characters. For example, GPIO 3 is addressed
as `03`, so its neutral command is:

```text
z0300.50x
```

If a frame does not start with `z` and end with `x`, `main.py` ignores it. If a
GPIO pin id is not present in `MOTOR_LOOKUP`, that specific update is ignored.
The onboard LED toggles after each parsed update, which is useful as a quick
traffic indicator.

## Main Firmware Flow

`main.py` does four things:

1. Creates `MOTOR_LOOKUP`.
2. Adds the actuator as id `99`.
3. Adds each configured servo pin using the GPIO pin as the command id.
4. Starts an async stdin loop that parses command frames forever.

The important constants are:

```python
SERVO_PINS = [26, 7, 16, 3, 15, 11]
EXTRA_SERVO_PINS = []

ACTUATOR_IDX = 99
ACTUATOR_PWM_PIN = 28
ACTUATOR_DIR_PIN = 21
ACTUATOR_PWM_FREQ = 20000
```

`EXTRA_SERVO_PINS` is currently empty. If pins are added there, they use a wider
servo pulse range of `0.0007` to `0.0022` seconds.

## DirectionMotor

`direction_motor.py` wraps a motor driver that has:

- one PWM pin for speed
- one digital direction pin
- an optional `forward_dir` setting

Values are clamped to `-1.0` through `1.0`.

```python
motor.value = 1.0   # full forward
motor.value = -1.0  # full reverse
motor.value = 0.0   # off
```

When the value is positive, the direction pin is set to `forward_dir`. When the
value is negative, the direction pin is inverted. PWM duty is based on the
absolute value.

## Host Control Script

`control.py` opens `/dev/ttyACM0` at `115200` baud and sends command frames to
the Pico.

The helpers format one complete frame per GPIO pin:

```python
def command(pin, value):
    return f"z{int(pin):02d}{value:05.2f}x\n"


def commands(pins, value):
    return "".join(command(pin, value) for pin in pins)
```

The script currently:

1. Sends `00.50` to every servo output.
2. Builds another all-neutral command payload.
3. Writes that payload repeatedly for timing measurements.
4. Sends final neutral servo values.

The repeated write sends the encoded command bytes directly:

```python
ser.write(cmd.encode())
```

Keep the fixed-width command format intact if changing this script.

## Quick Command Reference

Neutralize all six servo outputs:

```text
z2600.50x
z0700.50x
z1600.50x
z0300.50x
z1500.50x
z1100.50x
```

Turn actuator `99` off:

```text
z9900.00x
```

Set actuator `99` to reverse half power:

```text
z99-0.50x
```

Set GP26 to its midpoint:

```text
z2600.50x
```

Set GP3 to its midpoint. The GPIO pin id is padded as `03`:

```text
z0300.50x
```

## Editing Notes

- Keep GPIO pin ids two digits wide. The parser slices exactly two characters
  for the id, so pin `3` must be sent as `03`.
- Keep values five characters wide. The parser slices exactly five characters
  for the value, so neutral is `00.50`.
- Servo ids are GPIO pin numbers.
- Actuator id `99` is not a GPIO pin number; its real pins are GP28 and GP21.
- Start hardware tests from neutral values before sending larger changes.
