# Pico W Thruster Control

Control ROV thrusters, servos, and an actuator from a Jetson over USB.
Requires MicroPython on the Pico W and `uv` on the Jetson.

## Setup

1. Install Python 3.10 or newer and `uv` on the Jetson.
2. With the Pico W disconnected, hold BOOTSEL while plugging it into USB.
   Copy the Pico W `.uf2` from [assets/firmware](assets/firmware) onto the
   `RPI-RP2` drive. The Pico will restart with MicroPython installed.
3. Edit pins and limits in [config/rov.json](config/rov.json) to match your wiring.
   Pin numbers are GPIO numbers, so `12` means GP12.

## Run

Run these commands from this folder. Dependencies install automatically:

```bash
uv run upload --port /dev/ttyACM0
uv run diagnostics --port /dev/ttyACM0
```

Change the port if needed. Close diagnostics before uploading.
To try the menu without hardware: `uv run diagnostics --dry-run`.

Use **Arm / sound test** to send neutral to the selected thrusters, then
**Spin test** for a short forward/reverse test. Servo and actuator tests appear
only when those outputs are configured. Use **Neutralize thrusters** (or
**Neutralize thrusters / stop actuator**) to stop those outputs.

After changing the configuration, upload again so the Pico uses the same settings
as the diagnostic menu.

The current setup uses one thruster on GPIO12. Leave out `aux_servos` and
`actuator` when unused, or set them to `null` or `{}`. Configuration errors,
including conflicting PWM pins, are checked before upload and at startup.

Movement presets are in [diagnostics/sequences.py](diagnostics/sequences.py).
Verify them on the bench. Disconnecting USB does not guarantee the motors stop.

For camera recording, see [cameras/README.md](cameras/README.md).
