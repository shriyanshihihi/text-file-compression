"""High-level compress / decompress + file I/O + statistics.

Compressed file layout (all in one bit stream after a fixed 12-byte header):

    +----------+-----------------+--------------------+---------------------+
    | "HUF1"   | original length | serialised tree    | encoded data bits   | (+ zero padding)
    | 4 bytes  | 8 bytes (uint64)| (2k-1) + 8k bits   | sum(freq*codelen)   |
    +----------+-----------------+--------------------+---------------------+

The ORIGINAL LENGTH tells the decoder exactly when to stop, so the padding
bits at the end can never be mistaken for data.
"""
from __future__ import annotations

import math
import os
import struct

from .bitio import BitReader, BitWriter
from .tree import (CorruptFileError, build_codes, build_tree, code_string,
                   count_frequencies, read_tree, write_tree)

MAGIC = b"HUF1"
_HEADER = struct.Struct(">4sQ")      # big-endian: 4-byte magic + unsigned 64-bit length


# ---------------------------------------------------------------------------
# Core: bytes -> bytes
# ---------------------------------------------------------------------------
def compress_bytes(data: bytes) -> bytes:
    header = _HEADER.pack(MAGIC, len(data))
    if not data:
        return header
    root = build_tree(count_frequencies(data))
    codes = build_codes(root)
    # Lookup lists are faster than dict lookups in the hot loop.
    values = [0] * 256
    lengths = [0] * 256
    for sym, (val, length) in codes.items():
        values[sym], lengths[sym] = val, length

    writer = BitWriter()
    write_tree(root, writer)                       # part 1: the tree
    for b in data:                                 # part 2: the data, O(n)
        writer.write_bits(values[b], lengths[b])
    return header + writer.getvalue()


def decompress_bytes(blob: bytes) -> bytes:
    if len(blob) < _HEADER.size:
        raise CorruptFileError("file too short to be a Huffman archive")
    magic, size = _HEADER.unpack_from(blob)
    if magic != MAGIC:
        raise CorruptFileError("bad magic number - not a file made by this tool")
    if size == 0:
        return b""
    reader = BitReader(blob, _HEADER.size)
    try:
        root = read_tree(reader)                   # rebuild the tree, O(k)
        if root.is_leaf():                         # only one distinct byte in the original
            return bytes([root.symbol]) * size
        out = bytearray()
        node = root
        while len(out) < size:                     # walk: 0 = left, 1 = right
            node = node.right if reader.read_bit() else node.left
            if node.is_leaf():                     # reached a symbol -> emit, restart at root
                out.append(node.symbol)
                node = root
        return bytes(out)
    except EOFError:
        raise CorruptFileError("file is truncated") from None


# ---------------------------------------------------------------------------
# File I/O wrappers
# ---------------------------------------------------------------------------
def compress_file(src: str, dst: str) -> None:
    with open(src, "rb") as f:                     # 'rb' = raw bytes -> works for ANY file type
        data = f.read()
    with open(dst, "wb") as f:
        f.write(compress_bytes(data))


def decompress_file(src: str, dst: str) -> None:
    with open(src, "rb") as f:
        blob = f.read()
    with open(dst, "wb") as f:
        f.write(decompress_bytes(blob))


# ---------------------------------------------------------------------------
# Statistics (used by `stats`, `demo` and the benchmark)
# ---------------------------------------------------------------------------
def analyse(data: bytes) -> dict:
    """Numbers an interviewer may ask about: entropy, average code length, sizes."""
    n = len(data)
    if n == 0:
        return {"n": 0}
    freq = count_frequencies(data)
    root = build_tree(freq)
    codes = build_codes(root)
    k = len(codes)
    entropy = -sum((f / n) * math.log2(f / n) for f in freq if f)
    avg_len = sum(freq[s] * l for s, (_, l) in codes.items()) / n
    fixed_bits = max(1, math.ceil(math.log2(k)))   # fixed-length code just big enough for k symbols
    compressed = len(compress_bytes(data))
    return {
        "n": n, "distinct": k, "entropy_bits": entropy, "avg_code_len": avg_len,
        "fixed_bits": fixed_bits, "compressed": compressed,
        "tree_bytes": math.ceil(((2 * k - 1) + 8 * k) / 8),
        "reduction_pct": 100.0 * (1 - compressed / n),
        "ratio": n / compressed,
        "codes": {s: code_string(v, l) for s, (v, l) in codes.items()},
        "freq": freq,
    }


def human_symbol(b: int) -> str:
    return {10: "\\n", 32: "' '", 9: "\\t", 13: "\\r"}.get(b, chr(b) if 33 <= b < 127 else "0x%02X" % b)
