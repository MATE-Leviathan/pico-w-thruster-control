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
all_pins = ["26", "07", "16", "03", "15", "11"]
cmd = ""
for pin in all_pins:
    cmd += f"z{pin}00.50x\n"
    print(cmd)

ser.write(cmd.encode())
time.sleep(1.5)

cmd = ""
for pin in all_pins:
    cmd += f"z{pin}00.75x\n"
    #cmd += f"z{pin}00.50x\n"
s = time.perf_counter()

ser.write(cmd.encode())

time.sleep(0.2)




cmd = ""
for pin in all_pins:
    cmd += f"z{pin}00.50x\n"
    print(cmd)

ser.write(cmd.encode())

ser.write(b"z2101.00x\n")
ser.write(b"z2801.00x\n")
time.sleep(1)

ser.write(b"z2800.00x\n")
time.sleep(0.2)

ser.write(b"z2100.00x\n")
ser.write(b"z2801.00x\n")
time.sleep(0.5)

ser.write(b"z2100.50x\n")
ser.write(b"z2800.00x\n")

servo_20_value = input("Servo 20 value 0-1: ")
ser.write(f"z20{float(servo_20_value):04.2f}x\n".encode())

servo_1_value = input("Servo 1 value 0-1: ")
ser.write(f"z01{float(servo_1_value):04.2f}x\n".encode())

ser.close()
