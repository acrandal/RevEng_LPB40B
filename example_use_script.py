#
# Example demo script for using LPB40B range finder driver
#
# Author: Aaron S. Crandall <acrandal@gmail.com>
# Copyright: 2025
#


import serial
import time
import logging

from src.lpb40b import LPB40B


def main():
    # Open a serial port connected to the LPB40B
    operating_system_serial_device = "/dev/ttyUSB0"
    baud_rate=115200
    serial_timeout_sec=1
    ser = serial.Serial(operating_system_serial_device, baudrate=baud_rate, timeout=serial_timeout_sec)

    # Create LPB40B instance, pass in serial object
    lpb = LPB40B(ser)

    # Initialize hardware with default behaviors
    logging.info("Initializing LPB40B device")
    lpb.begin()

    # Example poll for device info, returns two frames
    (info_frame_1, info_frame_2) = lpb.get_device_info()

    logging.info(f"Get Device Info Frame 1: {info_frame_1.hex(' ').upper()}")
    logging.info(f"Get Device Info Frame 2: {info_frame_2.hex(' ').upper()}")


    # Go into a polling loop for measurements in millimeters
    try:
        while True:
            measurement_mm = lpb.get_measurement_mm()

            now = time.time()
            logging.info(f"{now:.3f} \t- Measurement received: {measurement_mm} mm")
            time.sleep(0.05)
    except:
        logging.info(f"Exception or interrupt recieved")

    ser.close()
    logging.info("Quitting")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    #logging.basicConfig(level=logging.DEBUG)

    main()
