
from src.lpb40b import LPB40B
import serial

import sys

port = "/dev/ttyUSB0"
baud = 115200

try:
    ser = serial.Serial(port, baud, timeout=1)
except Exception as e:
    print(f"Error opening {port}: {e}")
    sys.exit(1)


print("Starting testing")

lpb40 = LPB40B(ser)
lpb40.set_measurement_mode_continuous_startup()
lpb40.start_measuring()

print("Done testing")

