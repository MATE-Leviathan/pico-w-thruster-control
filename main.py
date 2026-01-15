from picozero import pico_led
import time
import sys

while True:
    time.sleep(5)
    try:
        cmd = sys.stdin.readline().strip()
        if cmd == "START":
            cmd2 = sys.stdin.readline().strip()
            while True:
                if cmd2 == "LED_ON":
                    pico_led.on()
                if cmd2 == "LED_OFF":
                    pico_led.off()
    except:
        pass
