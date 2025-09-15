#!/usr/bin/env python3

import serial
import sys
import time

port = "/dev/ttyUSB0"
baud = 115200

# The command to send
# Get device information
get_info_cmd = bytes([0x55, 0x01, 0x00, 0x00, 0x00, 0x00, 0xD3, 0xAA])

# Set to single measurement mode
single_mode_cmd = bytes([0x55, 0x0D, 0x00, 0x00, 0x00, 0x01, 0xC3, 0xAA])
start_measurement_cmd = bytes([0x55, 0x05, 0x00, 0x00, 0x00, 0x00, 0xCC, 0xAA])
set_baud_rate_cmd = bytes([0x55, 0x12, 0x00, 0x00, 0x00, 0x0C, 0x96, 0XAA])
stop_measurement_cmd = bytes([0x55, 0x06, 0x00, 0x00, 0x00, 0x00, 0x88, 0xAA])

try:
    ser = serial.Serial(port, baud, timeout=1.0)
except Exception as e:
    print(f"Error opening {port}: {e}")
    sys.exit(1)

#ser.flush()
#ser.write(set_baud_rate_cmd)
#set_rate_res = ser.read(8)
#print(set_rate_res)
#time.sleep(0.25)
#ser.flush()

# Send the command
#ser.flush()

#ser.write(single_mode_cmd)
#time.sleep(0.01)
#ser.write(stop_measurement_cmd)

ser.write(get_info_cmd)
#ser.flush()
#ser.write(start_measurement_cmd)
#ser.write(start_measurement_cmd)
#ser.read(16)
#ser.flush()

#info_read = ser.read(8)
#print(info_read)

#ser.write(single_mode_cmd)
#time.sleep(0.01)
#ser.write(start_measurement_cmd)
#ser.flush()

print("Command sent. Listening for data (Ctrl-C to stop)...")
counter = 0
try:
    while True:
        print(".", end="", flush=True)
        b = ser.read(1)   # read one byte
        counter += 1
        if counter % 64 == 0:
            ser.write(get_info_cmd)
        elif counter % 8 == 0:
            ser.write(start_measurement_cmd)
        if b:
            # Print as hex with a space, stay on same line
            print(f"{b.hex().upper()} ", end="", flush=True)
            if b == b'\xAA':
                print(counter)
                #time.sleep(0.25)
except KeyboardInterrupt:
    print("\nExiting.")
finally:
    ser.close()
