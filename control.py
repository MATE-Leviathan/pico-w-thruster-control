import time

import serial

ser = serial.Serial("/dev/ttyACM0", 115200, timeout=1)

THRUSTER_PINS = (26, 7, 16, 3, 15, 11)
NEUTRAL_VALUE = 0.50
TOTAL_RUNS = 300


def command(pin, value):
    return f"z{int(pin):02d}{value:05.2f}x\n"


def commands(pins, value):
    return "".join(command(pin, value) for pin in pins)


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
# MAKE VERY SURE TO HAVE PADDING, OTHERWISE COOKED
cmd = commands(THRUSTER_PINS, NEUTRAL_VALUE)
print(cmd)
ser.write(cmd.encode())

cmd = commands(THRUSTER_PINS, 0.75)
print(cmd)
ser.write(cmd.encode())

time.sleep(0.2)

cmd = commands(THRUSTER_PINS, NEUTRAL_VALUE)
print(cmd)
ser.write(cmd.encode())
time.sleep(3.0)

cmd = commands(THRUSTER_PINS, 0.75)
print(cmd)
ser.write(cmd.encode())
time.sleep(0.2)



cmd = commands(THRUSTER_PINS, NEUTRAL_VALUE)
ser.write(cmd.encode())

ser.close()
