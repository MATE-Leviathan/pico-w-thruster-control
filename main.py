from picozero import pico_led
import sys
import asyncio
from machine import Pin, PWM
from picozero import Servo

MOTOR_LOOKUP = {}
gpio_pins = (26, 7, 16, 3, 15, 11)
extra_servo_pins = (20, 1)
servo_limits = {
    20: (0.42, 0.54),
    1: (0.45, 1.0),
}
motor_direction_pin = 21
motor_speed_pin = 28


class DirectionPin:
    def __init__(self, pin):
        self._pin = Pin(pin, Pin.OUT)
        self.value = 0

    @property
    def value(self):
        return self._pin.value()

    @value.setter
    def value(self, value):
        self._pin.value(1 if float(value) >= 0.5 else 0)


class SpeedPin:
    def __init__(self, pin):
        self._pwm = PWM(Pin(pin))
        self._pwm.freq(20000)
        self.value = 0

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = max(0, min(1, float(value)))
        self._pwm.duty_u16(int(self._value * 65535))

current_char = " "

for i in gpio_pins:
    MOTOR_LOOKUP[i] = Servo(i, min_pulse_width=0.0011, max_pulse_width=0.0019)
    #MOTOR_LOOKUP[i] = Servo(i)

for i in extra_servo_pins:
    MOTOR_LOOKUP[i] = Servo(i, min_pulse_width=0.0007, max_pulse_width=0.0022)

MOTOR_LOOKUP[motor_direction_pin] = DirectionPin(motor_direction_pin)
MOTOR_LOOKUP[motor_speed_pin] = SpeedPin(motor_speed_pin)


def safe_motor_value(motor_idx, value):
    if motor_idx in servo_limits:
        min_value, max_value = servo_limits[motor_idx]
        return max(min_value, min(max_value, value))

    return value


async def read_stdin():
    reader = asyncio.StreamReader(sys.stdin)
    LED_ON = False
    motor_idx = 0
    speed_str = ''
    speed = 0.5
    offset = 1
    while True:
        try:
            line = await reader.readline()
            if not line:  # EOF
                break
            
            # 4 characters max for the value
            # spaces just for clarity, send without
            # format z 01 0.55 02 1.00x
            # Remove trailing newline
            line = line.decode().rstrip()
            if line[0] != "z" or line[-1] != "x":
                exit()

            offset = 1
            while line[offset] != "x":
                motor_idx_str = line[offset:offset+2]

                motor_idx = int(motor_idx_str)
                #motor_idx = 0
                speed_str = line[offset+2:offset+6]
                speed = float(speed_str)
                #speed = 0.5
                offset += 6
                #print(f"Got motor idx {motor_idx_str} at {speed_str}")
                if motor_idx in MOTOR_LOOKUP:
                    MOTOR_LOOKUP[motor_idx].value = safe_motor_value(motor_idx, speed)
                #pico_led.blink(on_time=0.2, off_time=0.2)
                if (LED_ON):
                    pico_led.off()
                    LED_ON = False
                else:
                    pico_led.on()
                    LED_ON = True

            # Process the line here
            #print(f"Received: {line}")

        except Exception as e:
            #print(f"Error reading stdin: {e}")
            pico_led.on()
 
async def main():
    await read_stdin()
 
# Run the event loop
try:
    asyncio.run(main())
except KeyboardInterrupt:
    pass
    #print("\nProgram terminated by user")
