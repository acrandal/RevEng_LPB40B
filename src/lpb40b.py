
import logging
from serial import Serial

class LPB40B:
    # Message protocol standards
    START_BYTE = 0x55
    STOP_BYTE = 0xAA
    POLY = 0x31  # x^8 + x^5 + x^4 + 1 # CRC polynomial
    CRC_START_VALUE = 0x00

    # Message type IDs (go in payload[0])
    MSG_GET_DEVICE_INFO       = 0x01
    MSG_OBTAIN_TEMPERATURE    = 0x02
    MSG_SET_MEASUREMENT_FREQ  = 0x03
    MSG_FORMAT_DATA           = 0x04
    MSG_START_MEASUREMENT     = 0x05
    MSG_STOP_MEASUREMENT      = 0x06
    MSG_MEASUREMENT_DATA_RET  = 0x07
    MSG_SAVE_SETTINGS         = 0x08
    MSG_GET_SERIAL_NUMBER     = 0x0A
    MSG_SET_MEASUREMENT_MODE  = 0x0D
    MSG_HIGHSPEED_DATA_RET    = 0x0E
    MSG_CONFIGURE_ADDRESS     = 0x11
    MSG_SET_BAUD_RATE         = 0x12

    # baud rate lookup table
    BAUD_RATE_MAP = {
        0: 0x00,      # adaptive
        300: 0x01,
        600: 0x02,
        1200: 0x03,
        2400: 0x04,
        4800: 0x05,
        9600: 0x06,
        14400: 0x07,
        19200: 0x08,
        38400: 0x09,
        56000: 0x0A,
        57600: 0x0B,
        115200: 0x0C,
        230400: 0x0D,
        256000: 0x0E,
        460800: 0x0F,
        921600: 0x10,
    }

    # ** ************************************************************************
    def __init__(self, ser: Serial):
        self.serial_port_check(ser)
        self.ser = ser

    def serial_port_check(self, ser):
        # List only what your class really needs
        required = ["write", "read", "close", "is_open"]

        for name in required:
            if not hasattr(ser, name):
                raise TypeError(f"Serial-like object missing '{name}'")

        # Optional: make sure it's actually open
        if hasattr(ser, "is_open") and not ser.is_open:
            raise ValueError("Serial port must be open")
        
    @staticmethod
    def gen_crc(msg_bytes: bytes) -> int:
        """
        Generate CRC-8 (polynomial 0x31, initial value 0x00).
        Returns a single byte (int 0-255).
        """
        crc = LPB40B.CRC_START_VALUE
        for byte in msg_bytes:
            crc ^= byte
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ LPB40B.POLY) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc
    
    @staticmethod
    def add_protocol_bytes(msg_bytes: bytes) -> bytes:
        """
        Wrap message with start, CRC, and stop bytes.
        [START][payload...][CRC][STOP]
        """
        crc = LPB40B.gen_crc(msg_bytes)
        return bytes([LPB40B.START_BYTE]) + msg_bytes + bytes([crc, LPB40B.STOP_BYTE])

    def send(self, data: bytes):
        self.ser.write(data)

    def receive(self, n: int) -> bytes:
        return self.ser.read(n)

    # ----------- message builders -----------
    @staticmethod
    def gen_obtaining_equipment_information_message() -> bytes:
        """Build 'Obtain Equipment Information' command frame."""
        payload = bytes([LPB40B.MSG_GET_DEVICE_INFO, 0x00, 0x00, 0x00, 0x00])
        return LPB40B.add_protocol_bytes(payload)

    @staticmethod
    def gen_obtaining_temperature_information_message() -> bytes:
        """
        Generate wrapped message for 'Obtain Temperature Information' (0x02).
        
        NOTE: This does not seem to get a response from the device
        """
        payload = bytes([LPB40B.MSG_OBTAIN_TEMPERATURE, 0x00, 0x00, 0x00, 0x00])
        return LPB40B.add_protocol_bytes(payload)

    @staticmethod
    def gen_set_measurement_frequency_message(freq: int) -> bytes:
        """
        Generate wrapped message for 'Set Measurement Frequency' (0x03).
        NOTE: This function caps at 500 hz to not move the sensor into high speed frame mode
   
        Parameters
        ----------
        freq : int
            Desired measurement frequency in Hz (1..500).
    
        Returns
        -------
        bytes
            Full wrapped protocol message.
    
        Raises
        ------
        ValueError
            If frequency is outside the allowed range.
        """
        if not (1 <= freq <= 500):
            raise ValueError("Measurement frequency must be in range 1..500")

        # Convert to little-endian uint32 (matches most device protocols of this style)
        freq_bytes = freq.to_bytes(4, byteorder="big", signed=False)

        # Payload: [command, b0, b1, b2, b3]
        payload = bytes([LPB40B.MSG_SET_MEASUREMENT_FREQ]) + freq_bytes
        return LPB40B.add_protocol_bytes(payload)

    @staticmethod
    def gen_set_data_format_byte() -> bytes:
        """
        Generate the message to set the sensor into BYTE format for measurements.
        """
        # payload = [CMD, 00, 00, 00, 01]
        BYTE_DATA_FORMAT_SETTING = 0x01
        payload = bytes([LPB40B.MSG_FORMAT_DATA, 0x00, 0x00, 0x00, BYTE_DATA_FORMAT_SETTING])
        crc = LPB40B.gen_crc(payload)
        return bytes([LPB40B.START_BYTE]) + payload + bytes([crc, LPB40B.STOP_BYTE])

    @staticmethod
    def gen_set_data_format_pixhawk() -> bytes:
        """
        Generate the message to set the sensor into PIXHAWK format for measurements.
        """
        # payload = [CMD, 00, 00, 00, 01]
        PIXHAWK_DATA_FORMAT_SETTING = 0x02
        payload = bytes([LPB40B.MSG_FORMAT_DATA, 0x00, 0x00, 0x00, PIXHAWK_DATA_FORMAT_SETTING])
        crc = LPB40B.gen_crc(payload)
        return bytes([LPB40B.START_BYTE]) + payload + bytes([crc, LPB40B.STOP_BYTE])

    # ** 0x0D - Setting Measurment Mode Commands ****************************************************
    @staticmethod
    def gen_set_measurement_mode_continuous_startup() -> bytes:
        """
        Generate the message to set the sensor continually measure distance at boot.
        """
        MEASURMENT_MODE_CONTINUOUS_STARTUP = 0x00
        payload = bytes([LPB40B.MSG_SET_MEASUREMENT_MODE, 0x00, 0x00, 0x00, MEASURMENT_MODE_CONTINUOUS_STARTUP])
        crc = LPB40B.gen_crc(payload)
        return bytes([LPB40B.START_BYTE]) + payload + bytes([crc, LPB40B.STOP_BYTE])

    @staticmethod
    def gen_set_measurement_mode_single() -> bytes:
        """
        Generate the message to set the sensor to only measure once when requested.
        """
        MEASURMENT_MODE_SINGLE = 0x01
        payload = bytes([LPB40B.MSG_SET_MEASUREMENT_MODE, 0x00, 0x00, 0x00, MEASURMENT_MODE_SINGLE])
        crc = LPB40B.gen_crc(payload)
        return bytes([LPB40B.START_BYTE]) + payload + bytes([crc, LPB40B.STOP_BYTE])

    @staticmethod
    def gen_set_measurement_mode_continuous_default_stopped() -> bytes:
        """
        Generate the message to set the sensor to measure continuously after being started
        """
        MEASURMENT_MODE_CONTINUOUS_DEFAULT_STOPPED = 0x02
        payload = bytes([LPB40B.MSG_SET_MEASUREMENT_MODE, 0x00, 0x00, 0x00, MEASURMENT_MODE_CONTINUOUS_DEFAULT_STOPPED])
        crc = LPB40B.gen_crc(payload)
        return bytes([LPB40B.START_BYTE]) + payload + bytes([crc, LPB40B.STOP_BYTE])

    # ** 0x05 Start Measuring Messages *****************************************************************
    @staticmethod
    def gen_start_measuring() -> bytes:
        """ Generate the message to start measuring """
        payload = bytes([LPB40B.MSG_START_MEASUREMENT, 0x00, 0x00, 0x00, 0x00])
        crc = LPB40B.gen_crc(payload)
        return bytes([LPB40B.START_BYTE]) + payload + bytes([crc, LPB40B.STOP_BYTE])

    # ** 0x06 Stop Measuring Messages *****************************************************************
    @staticmethod
    def gen_stop_measuring() -> bytes:
        """ Generate the message to stop measuring """
        payload = bytes([LPB40B.MSG_STOP_MEASUREMENT, 0x00, 0x00, 0x00, 0x00])
        crc = LPB40B.gen_crc(payload)
        return bytes([LPB40B.START_BYTE]) + payload + bytes([crc, LPB40B.STOP_BYTE])

    # ** 0x12 Set Baud Rate Messages ******************************************************************

    @staticmethod
    def gen_set_baud_rate(baud_rate: int) -> bytes:
        """ Generate the message to set the sensor's baud rate.  """

        if baud_rate not in LPB40B.BAUD_RATE_MAP:
            raise ValueError(f"Unsupported baud rate: {baud_rate}")
        
        baud_hex = LPB40B.BAUD_RATE_MAP[baud_rate]
        payload = bytes([LPB40B.MSG_SET_BAUD_RATE, 0x00, 0x00, 0x00, baud_hex])
        crc = LPB40B.gen_crc(payload)
        return bytes([LPB40B.START_BYTE]) + payload + bytes([crc, LPB40B.STOP_BYTE])



if __name__ == "__main__":
    print("Testing the driver: see pytest")
