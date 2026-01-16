from picozero import pico_led
import sys
import asyncio
 
async def read_stdin():
    reader = asyncio.StreamReader(sys.stdin)
    while True:
        try:
            line = await reader.readline()
            if not line:  # EOF
                break
            
            # Remove trailing newline
            line = line.decode().rstrip()
            if line == "LED_ONN":
                pico_led.on()
            if line == "LED_OFF":
                pico_led.off()
            
            # Process the line here
            print(f"Received: {line}")
            
        except Exception as e:
            print(f"Error reading stdin: {e}")
            break
 
async def main():
    await read_stdin()
 
# Run the event loop
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\nProgram terminated by user")