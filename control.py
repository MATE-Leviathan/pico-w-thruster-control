import time

import serial

ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)


def command(pin, value):
    if value < 0:
        value_str = f"{value:.1f}"
    else:
        value_str = f"{value:.2f}"
    # MAKE VERY SURE TO HAVE PADDING, OTHERWISE COOKED
    return f"z{int(pin):02d}{value_str}x\n"


time.sleep(3)
# 0 -> fr-1
# 1 -> ml-5
# ,2 -> bl-4
# 3 -> br-3
# 4 -> nothing
# 5 -> nothing
# 6 -> fl-6
# 7 -> mr-2
# accounted for 1, 2, 3,
all_pins = [26, 7, 16, 3, 15, 11]
ACTUATOR_NUM = 99
PIN_NUM = 1
cmd = ""
for pin in all_pins:
    cmd += command(pin, 0.50)
    print(cmd)

ser.write(cmd.encode())
time.sleep(1.5)

cmd = ""
for pin in all_pins:
    # cmd += command(pin, 0.75)
    cmd += command(pin, 0.50)
s = time.perf_counter()

TOTAL_RUNS = 300
for i in range(TOTAL_RUNS):
    s = time.perf_counter()
    ser.reset_output_buffer()
    ser.write(cmd.encode().ljust(64, b" "))
    ser.flush()
    e = time.perf_counter()
    print(f"Time of run {(e - s)}")
time.sleep(0.1)
cmd = ""
for pin in all_pins:
    cmd += command(pin, 0.50)
    print(cmd)

cmd += command(ACTUATOR_NUM, 0.00)
ser.write(cmd.encode())

ser.close()
