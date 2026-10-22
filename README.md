# Pico W Thruster Control

Control ROV thrusters, servos, and an actuator from a Jetson over USB.
Requires MicroPython on the Pico W and `uv` on the Jetson.

Edit pins and limits in [config/rov.json](config/rov.json), then run from this folder:

```bash
uv run upload --port /dev/ttyACM0
uv run diagnostics --port /dev/ttyACM0
```

Change the port if needed. Close diagnostics before uploading.
To try the menu without hardware: `uv run diagnostics --dry-run`.

The current setup uses one thruster on GPIO12. Leave out `aux_servos` and
`actuator` when unused, or set them to `null` or `{}`. Configuration errors,
including conflicting PWM pins, are checked before upload and at startup.

Movement presets are in [diagnostics/sequences.py](diagnostics/sequences.py).
Verify them on the bench. Disconnecting USB does not guarantee the motors stop.

For camera recording, see [cameras/README.md](cameras/README.md).
