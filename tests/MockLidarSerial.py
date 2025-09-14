import queue
import struct

class MockLidarSerial:
    def __init__(self, distance_mm=1234):

        self.START_BYTE = bytes([0x55])
        self.STOP_BYTE = bytes([0xAA])

        # Mock interface
        is_open = True   # Faking an open serial port

        # Internal state
        self.continuous_mode = False
        self.distance_mm = distance_mm

        # Internal queue of bytes to return on read()
        self._rx_queue = queue.Queue()

        # Jump table of commands
        self._handlers = {
            0x01: self._handle_get_info,
            0x0D: self._handle_set_measurement_mode,
            0x05: self._handle_start_measurement,
        }

    def write(self, data: bytes):
        """Receive exactly 8 bytes, decode, and queue response if needed."""
        if len(data) != 8:
            raise ValueError(f"Expected 8 bytes, got {len(data)}")

        if data[0] != 0x55 or data[-1] != 0xAA:
            raise ValueError("Bad frame: must start with 0x55 and end with 0xAA")

        command = data[1]
        payload = data[2:6]
        crc = data[6]

        # Calc CRC for message
        expected_crc = self._calc_crc(data[1:6])

        if crc != expected_crc:
            raise ValueError(f"CRC mismatch: expected {expected_crc:#x}, got {crc:#x}")

        # Dispatch to handler if known
        handler = self._handlers.get(command)
        if handler:
            handler(payload)
        else:
            raise ValueError(f"Instruction had unimplemented/invalid command: {command}")
            # Unknown command: ignore silently or could raise
            pass

    def read(self, size: int = 1) -> bytes:
        """Read up to `size` bytes from queue. Returns fewer if queue is short."""
        data = bytearray()
        for _ in range(size):
            try:
                b = self._rx_queue.get_nowait()
                data.append(b)
            except queue.Empty:
                break
        return bytes(data)
    

    def _calc_crc(self, data: bytes) -> int:
        """Follows Sensor CRC spec (polynomial 31, start 0)"""
        crc = 0
        for b in data:
            crc ^= b
            for _ in range(8):
                if crc & 0x80:
                    crc = ((crc << 1) ^ 0x31) & 0xFF
                else:
                    crc = (crc << 1) & 0xFF
        return crc

    # ---- Command Handlers ----

    # 0x01 - Get Info Command
    def _handle_get_info(self, response_1_payload: bytes):
        """Respond with the two bytes of a get info request
            Quick instruction reference: 55 01 00 00 00 00 D3 AA
                Value content description:
                    Value content is empty.
            Return data:
                A total of two frames of data are returned:
                The first frame: 55 01 AA BB BB BB JY AA
                    AA: current device model
                    BB: current firmware version number
                    JY: check bit
                The second frame: 55 01 AA BB CC JY AA
                    AA: data format of current device output:
                        01: byte format
                        02: pixhawk format
                    BB: measurement mode of current equipment:
                        00: continuous measurement mode-power on
                        01: Single measurement mode
                        02: continuous measurement mode-starting without starting
                    CC: measurement frequency set by current equipment.
                        NOTE: Manual errata: CC is 2 bytes long, not one
                    JY: parity bit
        """
        response_instruction = bytes([0x01])

        device_model_num = bytes([0x89])
        firmware_version = bytes([0x03, 0x01, 0x03])
        response_1_payload = response_instruction + device_model_num + firmware_version
        response_1_crc = bytes([self._calc_crc(response_1_payload)])
        response_frame_1 = self.START_BYTE + response_1_payload + response_1_crc + self.STOP_BYTE

        data_format = bytes([0x01])  #byte format (pixhawk doens't seem to work)

        if self.continuous_mode:
            measurement_mode = bytes([0x00])
        else:
            measurement_mode = bytes([0x01])
        measurement_frequency = bytes([0x00, 0x64]) # Adaptive - but should be in Mock state

        response_2_payload = response_instruction + data_format + measurement_mode + measurement_frequency
        response_2_crc = bytes([self._calc_crc(response_2_payload)])
        response_frame_2 = self.START_BYTE + response_2_payload + response_2_crc + self.STOP_BYTE

        self._enqueue_outgoing_frame(response_frame_1)
        self._enqueue_outgoing_frame(response_frame_2)

    def _handle_set_measurement_mode(self, payload: bytes) -> None:
        CONTINUOUS_MODE_PAYLOAD=bytes([0x00, 0x00, 0x00, 0x00])
        SINGLE_MEASURE_MODE_PAYLOAD=bytes([0x00, 0x00, 0x00, 0x01])

        if payload == CONTINUOUS_MODE_PAYLOAD:
            self.continuous_mode = True
        elif payload == SINGLE_MEASURE_MODE_PAYLOAD:
            self.continuous_mode = False
        else:
            raise ValueError(f"Invalid measurement mode payload: {payload}")
        # No return data response - no enqueue

    def _handle_start_measurement(self, payload: bytes) -> None:
        if self.continuous_mode:
            raise NotImplementedError(f"Continuous mode Mocking not implmented yet.")
        
        # Else, queue up a measurement

        ret_command = bytes([0x07])
        ret_measurement_error_code = bytes([0x00])  # See 4 types of errors - could use for modeling situations
        ret_measurement = struct.pack(">I", self.distance_mm)

        # Yes, that's how it's done - 3 bytes for an int! (geez), first byte is the error code 
        ret_measurement = ret_measurement[1:]

        ret_payload = ret_command + ret_measurement_error_code + ret_measurement
        ret_crc = bytes([self._calc_crc(ret_payload)])
        
        ret_frame = self.START_BYTE + ret_payload + ret_crc + self.STOP_BYTE

        self._enqueue_outgoing_frame(ret_frame)


    def _queue_measurement(self) -> None:
        """Push a fake measurement frame into rx queue."""
        dist_bytes = struct.pack(">I", self.distance_mm)  # 2 bytes little endian
        frame = bytes([0x55, 0x81]) + dist_bytes + b"\x00\x00"  # payload (4 bytes)
        crc = self._calc_crc(frame)
        frame += bytes([crc, 0xAA])
        for b in frame:
            self._rx_queue.put(b)

    def _enqueue_outgoing_frame(self, outgoing_frame: bytes) -> None:
        for curr_byte in outgoing_frame:
            self._rx_queue.put(curr_byte)

    def __str__(self):
        queued = list(self._rx_queue.queue)
        return (f"<MockLidarSerial mode={'CONT' if self.continuous_mode else 'SINGLE'} "
                f"distance={self.distance_mm}mm "
                f"qsize={len(queued)} "
                f"queue={[hex(b) for b in queued]}>")

