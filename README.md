# Pico W Thruster Control

Control ROV thrusters, servos, and an actuator from a Jetson over USB.
The Pico W needs MicroPython installed.

Run from the repository root:

```bash
uv sync
uv run upload --port /dev/ttyACM0
uv run diagnostics --port /dev/ttyACM0
```

To try the menu without hardware: `uv run diagnostics --dry-run`.

Edit pins and limits in `config/rov.json`, then upload again.
Change `/dev/ttyACM0` if your Pico uses another port. Close the menu before uploading.

Movement presets are in `diagnostics/sequences.py`; verify them on the bench.
Disconnecting USB does not guarantee the motors stop.

For camera recording, see [cameras/README.md](cameras/README.md).
