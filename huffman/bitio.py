"""Bit-level I/O. Files store whole bytes, but Huffman codes are 1..N bits long,
so we need to pack several codes into one byte (and unpack them again)."""
from __future__ import annotations


class BitWriter:
    """Collects bits and emits full bytes. Last partial byte is zero-padded."""

    def __init__(self) -> None:
        self._buf = bytearray()
        self._acc = 0       # bits waiting to be written
        self._n = 0         # how many bits are waiting (always < 8 between calls)

    def write_bits(self, value: int, length: int) -> None:
        self._acc = (self._acc << length) | value
        self._n += length
        while self._n >= 8:                       # a full byte is ready
            self._n -= 8
            self._buf.append((self._acc >> self._n) & 0xFF)
        self._acc &= (1 << self._n) - 1           # keep only the unwritten bits

    def write_bit(self, bit: int) -> None:
        self.write_bits(bit, 1)

    def getvalue(self) -> bytes:
        out = bytearray(self._buf)
        if self._n:                               # pad the last byte with zeros on the right
            out.append((self._acc << (8 - self._n)) & 0xFF)
        return bytes(out)


class BitReader:
    """Reads bits MSB-first from a bytes object, starting at byte offset `start`."""

    def __init__(self, data: bytes, start: int = 0) -> None:
        self._data = data
        self._pos = start * 8                     # position in BITS
        self._end = len(data) * 8

    def read_bit(self) -> int:
        if self._pos >= self._end:
            raise EOFError("ran out of bits")
        byte = self._data[self._pos >> 3]
        bit = (byte >> (7 - (self._pos & 7))) & 1
        self._pos += 1
        return bit

    def read_bits(self, n: int) -> int:
        value = 0
        for _ in range(n):
            value = (value << 1) | self.read_bit()
        return value
