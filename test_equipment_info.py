import serial
from src.lpb40b import LPB40B
import time
import sys
import logging


def main():
    # Open serial port
    ser = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=1)

    # Create LPB40B instance
    lpb = LPB40B(ser)

    lpb.begin()

    (info_frame_1, info_frame_2) = lpb.get_device_info()

    print(info_frame_1)
    print(info_frame_2)

    try:
        while True:
            measurement_mm = lpb.get_measurement_mm()

            print(f"{measurement_mm} mm")
            time.sleep(0.05)
    except:
        pass

    ser.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    main()
