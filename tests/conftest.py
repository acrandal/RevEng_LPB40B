import pytest
from io import BytesIO

class FakeSerial:
    def __init__(self):
        self.buffer = BytesIO()
        self.is_open = True

    def write(self, data: bytes):
        self.buffer.write(data)

    def read(self, n: int) -> bytes:
        self.buffer.seek(0)
        return self.buffer.read(n)

    def close(self):
        self.is_open = False

@pytest.fixture
def fake_serial():
    return FakeSerial()

