#!/usr/bin/env python3

import serial
import sys

port = "/dev/ttyUSB0"
baud = 115200

# The command to send
# Get device information
get_info_cmd = bytes([0x55, 0x01, 0x00, 0x00, 0x00, 0x00, 0xD3, 0xAA])

# Set to single measurement mode
single_mode_cmd = bytes([0x55, 0x0D, 0x00, 0x00, 0x00, 0x01, 0xC3, 0xAA])
start_measurement_cmd = bytes([0x55, 0x05, 0x00, 0x00, 0x00, 0x00, 0xCC, 0xAA])

try:
    ser = serial.Serial(port, baud, timeout=1)
except Exception as e:
    print(f"Error opening {port}: {e}")
    sys.exit(1)

# Send the command
ser.write(single_mode_cmd)
ser.flush()

ser.write(start_measurement_cmd)
ser.flush()

print("Command sent. Listening for data (Ctrl-C to stop)...")

try:
    while True:
        b = ser.read(1)   # read one byte
        if b:
            # Print as hex with a space, stay on same line
            print(f"{b.hex().upper()} ", end="", flush=True)
except KeyboardInterrupt:
    print("\nExiting.")
finally:
    ser.close()
