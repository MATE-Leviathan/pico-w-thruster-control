import serial
import time

ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)

time.sleep(1)

ser.write(b"START\n")

time.sleep(5)

for i in range(10):
    ser.write(b"LED_OFF\n")
    time.sleep(0.5)
    ser.write(b"LED_ON\n")
    time.sleep(0.5)

ser.close()
