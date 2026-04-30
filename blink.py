from picozero import pico_led
import time

while True:
    pico_led.blink()
    time.sleep(2)
