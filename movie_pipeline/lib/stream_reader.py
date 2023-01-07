from io import BufferedReader, BytesIO
import struct


class StreamReader:
    def __init__(self, base_stream: BufferedReader | BytesIO) -> None:
        self._base_stream = base_stream
        self._base_stream.seek(0)

    def read_fmt(self, fmt: str, length: int):
        return struct.unpack(fmt, self._base_stream.read(length))[0]

    def read_uchar(self) -> int:
        return self.read_fmt('B', 1)

    def read_int(self) -> int:
        integer = 0
        offset = 0

        while True:
            try:
                value = self.read_uchar()
                integer = integer | (value & 0x7f) << offset
                offset += 7
                if value & 0x80 == 0:
                    break
            except EOFError:
                break
        return integer

    def read_bytes(self) -> BytesIO:
        length = self.read_int()
        return BytesIO(self._base_stream.read(length))

    def read_str(self) -> str:
        return self.read_bytes().getvalue().decode('utf-8')
