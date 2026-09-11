import time

import serial

from firmware.protocol import encode_commands

DEFAULT_BAUD = 115200
CONNECT_DELAY_SECONDS = 2.0


class Link:
    def __init__(self, port, baud=DEFAULT_BAUD, dry_run=False):
        self.port = port
        self.baud = baud
        self.dry_run = dry_run
        self._ser = None

    def open(self):
        if self.dry_run:
            return self
        self._ser = serial.Serial(self.port, self.baud, timeout=1)
        time.sleep(CONNECT_DELAY_SECONDS)
        return self

    def close(self):
        if self._ser is not None:
            self._ser.close()
            self._ser = None

    def send(self, updates):
        frame = encode_commands(updates)
        print(frame, end="")
        if self.dry_run:
            return
        self._ser.write(frame.encode())
        self._ser.flush()

    def __enter__(self):
        return self.open()

    def __exit__(self, *exc_info):
        self.close()
