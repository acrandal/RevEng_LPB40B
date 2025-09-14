import pytest
from pprint import pprint


from MockLidarSerial import MockLidarSerial

VALID_GET_INFO_FRAME_CMD=bytes([0x55, 0x01, 0x00, 0x00, 0x00, 0x00, 0xD3, 0xAA])



if __name__ == "__main__":
    print("Testing serial mocking")
    lidar = MockLidarSerial()

    lidar.write(VALID_GET_INFO_FRAME_CMD)
    print(lidar)

    pprint(lidar.read(8))

    print(lidar)