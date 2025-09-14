import time
import serial  # pyserial
import logging

class LPB40B:
    START_BYTE      = 0x55
    STOP_BYTE       = 0xAA
    CRC_POLYNOMIAL  = 0x31
    CRC_START_VALUE = 0

    # commands from SEN058 communications protocol
    CMD_GET_DEVICE_INFO         = 0x01
    CMD_START_MEASUREMENT       = 0x05
    CMD_MEASUREMENT_DATA        = 0x07
    CMD_SET_MEASUREMENT_MODE    = 0x0D

    def __init__(self, ser: serial.Serial):
        if not ser.is_open:
            raise ValueError("Serial port must be open")
        self.ser = ser

        self.log = logging.getLogger(name=__class__.__name__)

    # ---------- CRC Per documentation spec ----------
    @staticmethod
    def gen_crc(msg_bytes: bytes) -> int:
        crc = LPB40B.CRC_START_VALUE
        bits_per_byte = 8
        for current_byte in msg_bytes:
            crc ^= current_byte
            for _ in range(bits_per_byte):
                if crc & 0x80:
                    crc = ((crc << 1) ^ LPB40B.CRC_POLYNOMIAL) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc

    def _add_protocol_bytes(self, msg_bytes: bytes) -> bytes:
        if len(msg_bytes) != 5:
            raise ValueError("Payload must be exactly 5 bytes")
        crc = LPB40B.gen_crc(msg_bytes)
        return bytes([LPB40B.START_BYTE]) + msg_bytes + bytes([crc, LPB40B.STOP_BYTE])

    # ---------- High-level commands ----------
    def begin(self):
        self.ser.flush()
        self.set_single_measurement_mode()

    def set_single_measurement_mode(self):
        """Put sensor into single measurement mode."""
        self.log.debug("Setting device into single measurement mode.")
        payload = bytes([self.CMD_SET_MEASUREMENT_MODE, 0x00, 0x00, 0x00, 0x01])
        self._send(payload)

        # Yes, this is needed - device hangs if you flood serial here
        #  Value of 0.01 seems to be sufficient
        time.sleep(0.01)

    def get_measurement_mm(self) -> int:
        """Take one measurement and return distance in mm."""
        payload = bytes([self.CMD_START_MEASUREMENT, 0x00, 0x00, 0x00, 0x00])
        self._send(payload)

        measurement_frame = self._read_frame()

        frame_payload = measurement_frame[1:6]

        return_cmd = frame_payload[0]

        if return_cmd != self.CMD_MEASUREMENT_DATA:
            raise ValueError(f"Measurement read invalid return data frame: {measurement_frame}")

        error_code = frame_payload[1:2]
        measurement_bytes = frame_payload[-3:] # 3 bytes at end of payload (yes, 3 byte bigendian int)
        dist_mm = int.from_bytes(measurement_bytes, byteorder="big")
        return dist_mm

    def get_device_info(self, timeout=1.0) -> tuple:
        """Fetch device info (2 frames). Returns a list of 2 raw frames."""
        payload = bytes([self.CMD_GET_DEVICE_INFO, 0x00, 0x00, 0x00, 0x00])
        self._send(payload)

        info_frame1 = self._read_frame()
        info_frame2 = self._read_frame()

        return (info_frame1, info_frame2)


    # ---------- Low-level I/O ----------
    def _send(self, payload: bytes):
        msg = self._add_protocol_bytes(payload)
        self.log.debug(f"Sending to serial: {msg.hex(' ').upper()}")
        self.ser.write(msg)

    def _read_frame(self, timeout=1.0) -> bytes:
        """Read one frame, return as bytes, or None on timeout."""
        self.ser.timeout = timeout
        frame_bytes = bytearray()

        while len(frame_bytes) < 8:
            curr_byte = self.ser.read(1)
            if not curr_byte:
                raise TimeoutError(f"Sensor did not return full frame. Bytes read: {frame_bytes}")
            else:
                frame_bytes.extend(curr_byte)

        return frame_bytes
