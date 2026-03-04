import serial
import time

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

time.sleep(3)
# 0 -> fr-1
# 1 -> ml-5
#,2 -> bl-4
# 3 -> br-3
# 4 -> nothing
# 5 -> nothing
# 6 -> fl-6
# 7 -> mr-2
# accounted for 1, 2, 3,
# MAKE VERY SURE TO HAVE PADDING, OTHERWISE COOKED
all_pins = ["00", "01", "02", "03", "06", "07"]
PIN_NUM = "01"
cmd = ""
for pin in all_pins:
    cmd += f"z{pin}00.50x\n"
    print(cmd)

ser.write(cmd.encode())
time.sleep(1.5)

cmd = ""
for pin in all_pins:
    #cmd += f"z{pin}00.75x\n"
    cmd += f"z{pin}00.50x\n"
s = time.perf_counter()

TOTAL_RUNS = 300
for i in range(TOTAL_RUNS):
    s = time.perf_counter()
    ser.reset_output_buffer()
    ser.write(cmd.encode().ljust(64, b' '))
    ser.flush()
    e = time.perf_counter()
    print(f"Time of run {(e-s)}")
time.sleep(0.1)
cmd = ""
for pin in all_pins:
    cmd += f"z{pin}00.50x\n"
    print(cmd)

ser.write(cmd.encode())

ser.close()
