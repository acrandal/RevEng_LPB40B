import pytest
from src.lpb40b import LPB40B

def test_init_accepts_fake(fake_serial):
    dev = LPB40B(fake_serial)
    assert dev.ser.is_open

def test_send_and_receive(fake_serial):
    dev = LPB40B(fake_serial)
    dev.send(b"hello")
    data = dev.receive(5)
    assert data == b"hello"

def test_rejects_closed_serial(fake_serial):
    fake_serial.close()
    with pytest.raises(ValueError):
        LPB40B(fake_serial)

# ** CRC implementation testing
# ** CRC known calculated values
def test_gen_crc_known_stop_measurement_bytes():
    payload = bytes([0x06, 0x00, 0x00, 0x00, 0x00])
    crc = LPB40B.gen_crc(payload)
    assert crc == 0x88

def test_gen_crc_known_save_settings_bytes():
    payload = bytes([0x08, 0x00, 0x00, 0x00, 0x00])
    crc = LPB40B.gen_crc(payload)
    assert crc == 0x3E

    # Sanity: with only FOUR bytes, CRC differs (shows why your earlier test failed)
    four_byte_payload = bytes([0x08, 0x00, 0x00, 0x00])
    assert LPB40B.gen_crc(four_byte_payload) == 0x1C

def test_gen_crc_known_five_bytes():
    # Values taken from SEN056 documentation
    payload = bytes([0x07, 0x00, 0x00, 0x05, 0xAD])
    crc = LPB40B.gen_crc(payload)
    assert crc == 0x9C


# ** Testing CRC on different messages
def test_gen_crc_empty_message():
    """CRC of an empty byte string should be 0x00."""
    crc = LPB40B.gen_crc(b"")
    assert crc == 0x00

def test_gen_crc_known_payload():
    """CRC should be stable and reproducible for a given payload."""
    payload = bytes([0x01, 0x02, 0x03])
    crc1 = LPB40B.gen_crc(payload)
    crc2 = LPB40B.gen_crc(payload)
    assert crc1 == crc2  # deterministic
    assert isinstance(crc1, int)
    assert 0 <= crc1 <= 255

# ** Testing add_protocol_bytes for the serial transmissions
def test_add_protocol_bytes_wraps_correctly():
    payload = bytes([0x10, 0x20, 0x30])
    wrapped = LPB40B.add_protocol_bytes(payload)

    # Format should be: START + payload + CRC + STOP
    assert wrapped[0] == LPB40B.START_BYTE
    assert wrapped[-1] == LPB40B.STOP_BYTE
    assert wrapped[1:-2] == payload

    # CRC should be correct
    crc = LPB40B.gen_crc(payload)
    assert wrapped[-2] == crc

def test_add_protocol_bytes_empty_payload():
    payload = b""
    wrapped = LPB40B.add_protocol_bytes(payload)

    # Should still have start, CRC, stop (3 bytes total)
    assert len(wrapped) == 3
    assert wrapped[0] == LPB40B.START_BYTE
    assert wrapped[-1] == LPB40B.STOP_BYTE
    # CRC of empty message is 0x00
    assert wrapped[1] == 0x00

# ---- add_protocol_bytes ----

def test_add_protocol_bytes_save_settings_full_frame():
    payload = bytes([0x08, 0x00, 0x00, 0x00, 0x00])
    wrapped = LPB40B.add_protocol_bytes(payload)
    # Expected frame: 55 08 00 00 00 00 3E AA
    assert wrapped == bytes([0x55, 0x08, 0x00, 0x00, 0x00, 0x00, 0x3E, 0xAA])

def test_add_protocol_bytes_stop_measurement_full_frame():
    payload = bytes([0x06, 0x00, 0x00, 0x00, 0x00])
    wrapped = LPB40B.add_protocol_bytes(payload)
    # Expected frame: 55 06 00 00 00 00 88 AA
    assert wrapped == bytes([0x55, 0x06, 0x00, 0x00, 0x00, 0x00, 0x88, 0xAA])

def test_add_protocol_bytes_set_single_measurement():
    payload = bytes([0x0D, 0x00, 0x00, 0x00, 0x01])
    wrapped = LPB40B.add_protocol_bytes(payload)
    # Expected: 55 0D 00 00 00 01 C3 AA
    assert wrapped == bytes([0x55, 0x0D, 0x00, 0x00, 0x00, 0x01, 0xC3, 0xAA])

def test_add_protocol_bytes_always_8_bytes():
    # Try a few different payloads
    payloads = [
        bytes([0x06, 0x00, 0x00, 0x00, 0x00]),  # stop measurement
        bytes([0x08, 0x00, 0x00, 0x00, 0x00]),  # save settings
        bytes([0x0D, 0x00, 0x00, 0x00, 0x01]),  # single measurement mode
    ]

    for payload in payloads:
        wrapped = LPB40B.add_protocol_bytes(payload)
        assert len(payload) == 5, "Payload must always be 5 bytes"
        assert len(wrapped) == 8, "Wrapped message must always be 8 bytes"
        assert wrapped[0] == LPB40B.START_BYTE
        assert wrapped[-1] == LPB40B.STOP_BYTE

# ** message builders ****************************************************************

# ** 0x01 - Obtain Device Information
def test_gen_obtaining_equipment_information_message():
    """Verify that the 'Obtain Equipment Information' message is built correctly."""
    expected = bytes([0x55, 0x01, 0x00, 0x00, 0x00, 0x00, 0xD3, 0xAA])
    result = LPB40B.gen_obtaining_equipment_information_message()
    assert result == expected, f"Expected {expected.hex(' ')}, got {result.hex(' ')}"

def test_gen_obtaining_temperature_information_message():
    """Verify that the 'Obtain Temperature Information' message is built correctly."""
    expected = bytes([0x55, 0x02, 0x00, 0x00, 0x00, 0x00, 0x97, 0xAA])
    result = LPB40B.gen_obtaining_temperature_information_message()
    assert result == expected, f"Expected {expected.hex(' ')}, got {result.hex(' ')}"


# ** 0x03 Set Measurement Frequency Tests ********************************************

def test_gen_set_measurement_frequency_message_valid():
    """Check building a valid frequency message."""
    result = LPB40B.gen_set_measurement_frequency_message(10)
    # freq=10 → 0x0A 00 00 00 in little-endian
    expected = bytes([0x55, 0x03, 0x00, 0x00, 0x00, 0x0A, 0x9F, 0xAA])
    assert result == expected, f"Expected {expected.hex(' ')}, got {result.hex(' ')}"

def test_gen_set_measurement_frequency_message_invalid_low():
    """Frequency < 1 should raise ValueError."""
    with pytest.raises(ValueError):
        LPB40B.gen_set_measurement_frequency_message(0)

def test_gen_set_measurement_frequency_message_invalid_high():
    """Frequency > 2000 should raise ValueError."""
    with pytest.raises(ValueError):
        LPB40B.gen_set_measurement_frequency_message(3000)


# ** 0x04 Set Data Format Tests **************************************************
def test_gen_set_data_format_byte_message():
    msg = LPB40B.gen_set_data_format_byte()
    # Expected wrapped message from documentation
    expected = bytes([0x55, 0x04, 0x00, 0x00, 0x00, 0x01, 0x2E, 0xAA])
    assert msg == expected, f"Expected {expected.hex()}, got {msg.hex()}"
    # Sanity checks
    assert msg[0] == LPB40B.START_BYTE
    assert msg[-1] == LPB40B.STOP_BYTE
    assert len(msg) == 8

# ** 0x04 Set Data Format Tests **************************************************
def test_gen_set_data_format_pixhawk_message():
    msg = LPB40B.gen_set_data_format_pixhawk()
    # Expected wrapped message from documentation
    expected = bytes([0x55, 0x04, 0x00, 0x00, 0x00, 0x02, 0x7D, 0xAA])
    assert msg == expected, f"Expected {expected.hex()}, got {msg.hex()}"
    # Sanity checks
    assert msg[0] == LPB40B.START_BYTE
    assert msg[-1] == LPB40B.STOP_BYTE
    assert len(msg) == 8




