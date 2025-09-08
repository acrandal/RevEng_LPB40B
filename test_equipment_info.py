import serial
from src.lpb40b import LPB40B
import time
import sys

def main():
    # Open serial port
    ser = serial.Serial("/dev/ttyUSB0", baudrate=115200, timeout=1)

    # Create LPB40B instance
    lpb = LPB40B(ser)

    # Generate "Get Equipment Information" message
    msg = lpb.gen_obtaining_equipment_information_message()
    temperature_msg = lpb.gen_obtaining_temperature_information_message()
    measure_msg = lpb.gen_set_measurement_frequency_message(10)

    # print(f"Sending message: {msg.hex(' ')}")
    # ser.write(msg)
    # data = ser.read(16)
    # if data:
    #     print(f"RX: {data.hex(' ')}")

    start_measurement_cmd = bytes([0x55, 0x05, 0x00, 0x00, 0x00, 0x00, 0xCC, 0xAA])
    print(f"Sending message: {start_measurement_cmd.hex(' ')}")
    ser.write(start_measurement_cmd)

    print("Reading from sensor (Ctrl+C to stop)...")
    try:
        while True:
            data = ser.read(8)  # read up to 64 bytes at a time
            if data:
                print(f"RX: {data.hex(' ')}")
    except KeyboardInterrupt:
        print("\nStopped by user.")

    sys.exit()  ######

    print(f"Sending message: {msg.hex(' ')}")
    ser.write(msg)
    data = ser.read(16)
    if data:
        print(f"RX: {data.hex(' ')}")

    print(f"Sending TEMP message: {temperature_msg.hex(' ')}")
    ser.write(temperature_msg)
    data = ser.read(8)  # read up to 64 bytes at a time
    if data:
        print(f"RX: {data.hex(' ')}")


    print(f"Sending message: {measure_msg.hex(' ')}")
    ser.write(measure_msg)

    start_measurement_cmd = bytes([0x55, 0x05, 0x00, 0x00, 0x00, 0x00, 0xCC, 0xAA])
    print(f"Sending message: {start_measurement_cmd.hex(' ')}")
    ser.write(start_measurement_cmd)

    print("Reading from sensor (Ctrl+C to stop)...")
    try:
        while True:
            data = ser.read(8)  # read up to 64 bytes at a time
            if data:
                print(f"RX: {data.hex(' ')}")
    except KeyboardInterrupt:
        print("\nStopped by user.")

    ser.close()

if __name__ == "__main__":
    main()
