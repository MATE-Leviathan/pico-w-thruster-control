import serial
import time


SERIAL_PORT = "/dev/ttyACM0"
BAUD_RATE = 115200
SERVO_PINS = {
    "1": "01",
    "01": "01",
    "20": "20",
}


def clamp_servo_value(value):
    return max(0, min(1, float(value)))


def servo_command(pin, value):
    return f"z{pin}{clamp_servo_value(value):04.2f}x\n"


def print_help():
    print("Commands:")
    print("  1 0.50        set servo GP1")
    print("  20 0.50       set servo GP20")
    print("  both 0.50     set both servos to the same value")
    print("  1 0.25 20 0.75")
    print("  q             quit")


ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
time.sleep(3)

print_help()

while True:
    line = input("> ").strip().lower()
    if line in ("q", "quit", "exit"):
        break
    if line in ("h", "help", "?"):
        print_help()
        continue

    parts = line.split()
    cmd = ""

    try:
        if len(parts) == 2 and parts[0] == "both":
            cmd += servo_command("01", parts[1])
            cmd += servo_command("20", parts[1])
        elif len(parts) % 2 == 0:
            for i in range(0, len(parts), 2):
                pin = SERVO_PINS[parts[i]]
                value = parts[i + 1]
                cmd += servo_command(pin, value)
        else:
            print("Invalid command. Type h for help.")
            continue

        print(cmd, end="")
        ser.write(cmd.encode())
    except (KeyError, ValueError):
        print("Invalid command. Type h for help.")

ser.close()
