import pytest
from pprint import pprint


from .MockLidarSerial import MockLidarSerial

VALID_GET_INFO_FRAME_CMD=bytes([0x55, 0x01, 0x00, 0x00, 0x00, 0x00, 0xD3, 0xAA])
VALID_SET_SINGLE_MEASUREMENT_MODE_CMD=bytes([0x55, 0x0D, 0x00, 0x00, 0x00, 0x01, 0xC3, 0xAA])
VALID_SET_CONTINUOUS_MEASUREMENT_MODE_CMD=bytes([0x55, 0x0D, 0x00, 0x00, 0x00, 0x00, 0xF2, 0xAA])
VALID_START_MEASUREMENT=bytes([0x55, 0x05, 0x00, 0x00, 0x00, 0x00, 0xCC, 0xAA])


@pytest.fixture
def lidar():
    return MockLidarSerial(distance_mm=2500)

def test_valid_get_info_cmd(lidar):
    lidar.write(VALID_GET_INFO_FRAME_CMD)

    expected_frame_1 = bytes([0x55, 0x01, 0x89, 0x03, 0x01, 0x03, 0xC8, 0xAA])
    actual_frame_1 = lidar.read(8)

    expected_frame_2 = bytes([0x55, 0x01, 0x01, 0x01, 0x00, 0x64, 0x71, 0xAA])
    actual_frame_2 = lidar.read(8)

    assert actual_frame_1 == expected_frame_1 
    assert actual_frame_2 == expected_frame_2

def test_set_single_measurement_mode(lidar):
    lidar.write(VALID_SET_SINGLE_MEASUREMENT_MODE_CMD)
    lidar.write(VALID_GET_INFO_FRAME_CMD)
    info_frame_1 = lidar.read(8)
    info_frame_2 = lidar.read(8)

    measurement_mode_expected = 0x01
    measurement_mode_actual = info_frame_2[3]

    assert measurement_mode_actual == measurement_mode_expected

def test_set_continuous_measurement_mode(lidar):
    lidar.write(VALID_SET_CONTINUOUS_MEASUREMENT_MODE_CMD)
    lidar.write(VALID_GET_INFO_FRAME_CMD)
    info_frame_1 = lidar.read(8)
    info_frame_2 = lidar.read(8)

    measurement_mode_expected = 0x00
    measurement_mode_actual = info_frame_2[3]

    print(info_frame_2)

    assert measurement_mode_actual == measurement_mode_expected


def test_get_single_measurement_default_2500mm(lidar):
    lidar.write(VALID_SET_SINGLE_MEASUREMENT_MODE_CMD)
    lidar.write(VALID_START_MEASUREMENT)

    measurement_frame = lidar.read(8)

    error_code = measurement_frame[2]
    dist_bytes = measurement_frame[3:6]
    actual_measurement_mm = int.from_bytes(dist_bytes, byteorder="big")

    expected_measurement_mm = 2500

    assert actual_measurement_mm == expected_measurement_mm


