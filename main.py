from picozero import pico_led
import sys
import asyncio
from picozero import Servo

MOTOR_LOOKUP = {}
gpio_pins = [0,1,2,3,4,5,6,7,8]

current_char = " "

for i in gpio_pins:
    MOTOR_LOOKUP[i] = Servo(i, min_pulse_width=0.0011, max_pulse_width=0.0019)
    #MOTOR_LOOKUP[i] = Servo(i)


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
                MOTOR_LOOKUP[motor_idx].value = speed
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
