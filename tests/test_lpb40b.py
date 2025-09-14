import pytest
import serial
from typing import cast

from src.lpb40b import LPB40B
from .MockLidarSerial import MockLidarSerial

CMD_GET_INFO = 0x01

@pytest.fixture
def lpb40():
    mock_serial = cast(serial.Serial, MockLidarSerial(distance_mm=2500))

    lpb40device = LPB40B(mock_serial)
    return lpb40device


# ** **********************************************************************************
# ** Main tests ***********************************************************************
# ** **********************************************************************************
def test_instantiate_lpb40(lpb40):
    lpb40.begin()

def test_get_device_info(lpb40):
    lpb40.begin()
    (info_frame_1, info_frame_2) = lpb40.get_device_info()

    # Verifying that both frames are info responses
    assert info_frame_1[1] == CMD_GET_INFO
    assert info_frame_2[1] == CMD_GET_INFO

def test_get_measurement_mm_2500(lpb40):
    lpb40.begin()

    expected_measurment_mm = 2500
    actual_measurement_mm = lpb40.get_measurement_mm()

    assert actual_measurement_mm == expected_measurment_mm
