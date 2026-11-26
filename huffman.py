#!/usr/bin/env python3
"""Text File Compression using Huffman Coding  (Min-Heap, File I/O)

Usage:
    python huffman.py compress   input.txt  output.huf
    python huffman.py decompress output.huf restored.txt

Everything is written from scratch (only `struct`, `sys` and `os` are imported):
no heapq, no zlib/gzip.  Files are handled as raw BYTES, so XML, JSON, source
code or any other file works.

Compressed file layout:
    "HUF1" (4 bytes) | original length (8 bytes) | tree bits | data bits | zero padding

Complexity  (m = bytes in the file, k = distinct byte values, k <= 256, tree has 2k-1 nodes)
    count frequencies .......... O(m)
    build tree with Min-Heap ... O(k log k)   <- the "O(n log n) Huffman encoding" (n = k)
    encode the data ............ O(m)
    rebuild tree from header ... O(2k-1) = O(n)  <- the "O(n) tree reconstruction" (n = nodes)
    decode the data ............ O(m)
"""
import os
import struct
import sys

MAGIC = b"HUF1"


# =============================================================================
# 1. Custom Min-Heap  (array-based binary heap; parent of i is (i-1)//2)
# =============================================================================
class MinHeap:
    def __init__(self):
        self.a = []

    def __len__(self):
        return len(self.a)

    def push(self, item):                       # O(log n): add at the end, move UP
        a = self.a
        a.append(item)
        i = len(a) - 1
        while i > 0 and a[i] < a[(i - 1) // 2]:
            a[i], a[(i - 1) // 2] = a[(i - 1) // 2], a[i]
            i = (i - 1) // 2

    def pop(self):                              # O(log n): take root, move last to root, sink DOWN
        a = self.a
        top = a[0]
        last = a.pop()
        if a:
            a[0] = last
            i = 0
            while True:
                left, right, small = 2 * i + 1, 2 * i + 2, i
                if left < len(a) and a[left] < a[small]:
                    small = left
                if right < len(a) and a[right] < a[small]:
                    small = right
                if small == i:
                    break
                a[i], a[small] = a[small], a[i]
                i = small
        return top


# =============================================================================
# 2. Huffman tree
# =============================================================================
class Node:
    def __init__(self, freq=0, symbol=None, left=None, right=None, order=0):
        self.freq, self.symbol, self.left, self.right, self.order = freq, symbol, left, right, order

    def is_leaf(self):
        return self.left is None and self.right is None

    def __lt__(self, other):                    # smaller frequency first; tie -> older node first
        return (self.freq, self.order) < (other.freq, other.order)


def count_frequencies(data):                    # O(m)
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    return freq


def build_tree(freq):                           # O(k log k): ~2k heap operations, each O(log k)
    heap, order = MinHeap(), 0
    for symbol, f in enumerate(freq):
        if f > 0:
            heap.push(Node(f, symbol=symbol, order=order))
            order += 1
    while len(heap) > 1:
        a = heap.pop()                          # two smallest ...
        b = heap.pop()
        heap.push(Node(a.freq + b.freq, left=a, right=b, order=order))   # ... merged
        order += 1
    return heap.pop()


def build_codes(root):                          # O(k): left edge = '0', right edge = '1'
    codes = {}

    def walk(node, code):
        if node.is_leaf():
            codes[node.symbol] = code or "0"    # only one distinct byte -> give it code "0"
        else:
            walk(node.left, code + "0")
            walk(node.right, code + "1")
    walk(root, "")
    return codes


# --- store / restore the tree inside the file (pre-order: 0 = internal node, 1 + 8 bits = leaf)
def write_tree(node, out):                      # O(2k-1)
    if node.is_leaf():
        out.append("1" + format(node.symbol, "08b"))
    else:
        out.append("0")
        write_tree(node.left, out)
        write_tree(node.right, out)


def read_tree(bits, pos):                       # O(2k-1) = O(n): every node is read exactly once
    if bits[pos] == "1":
        return Node(symbol=int(bits[pos + 1:pos + 9], 2)), pos + 9
    left, pos = read_tree(bits, pos + 1)
    right, pos = read_tree(bits, pos)
    return Node(left=left, right=right), pos


# =============================================================================
# 3. Compress / decompress  (bytes -> bytes)
# =============================================================================
def compress_bytes(data):
    header = MAGIC + struct.pack(">Q", len(data))
    if not data:
        return header
    root = build_tree(count_frequencies(data))
    codes = build_codes(root)
    tree_bits = []
    write_tree(root, tree_bits)
    bits = "".join(tree_bits) + "".join(codes[b] for b in data)     # O(m)
    bits += "0" * (-len(bits) % 8)                                  # pad the last byte with zeros
    return header + bytes(int(bits[i:i + 8], 2) for i in range(0, len(bits), 8))


def decompress_bytes(blob):
    if len(blob) < 12 or blob[:4] != MAGIC:
        raise ValueError("not a file made by this tool")
    size = struct.unpack(">Q", blob[4:12])[0]       # stored length tells us when to stop (ignores padding)
    if size == 0:
        return b""
    try:
        bits = "".join(format(b, "08b") for b in blob[12:])
        root, pos = read_tree(bits, 0)              # rebuild the tree
        if root.is_leaf():
            return bytes([root.symbol]) * size
        out, node = bytearray(), root
        while len(out) < size:                      # walk: 0 = left, 1 = right, leaf = emit byte
            node = node.right if bits[pos] == "1" else node.left
            pos += 1
            if node.is_leaf():
                out.append(node.symbol)
                node = root
        return bytes(out)
    except (IndexError, ValueError, RecursionError):
        raise ValueError("compressed file is corrupt or truncated") from None


# =============================================================================
# 4. File I/O  ('rb' / 'wb' = raw bytes, so nothing is changed by text decoding)
# =============================================================================
def compress_file(src, dst):
    with open(src, "rb") as f:
        data = f.read()
    with open(dst, "wb") as f:
        f.write(compress_bytes(data))


def decompress_file(src, dst):
    with open(src, "rb") as f:
        blob = f.read()
    with open(dst, "wb") as f:
        f.write(decompress_bytes(blob))


if __name__ == "__main__":
    if len(sys.argv) != 4 or sys.argv[1] not in ("compress", "decompress"):
        sys.exit(__doc__)
    try:
        (compress_file if sys.argv[1] == "compress" else decompress_file)(sys.argv[2], sys.argv[3])
    except (OSError, ValueError) as e:
        sys.exit("error: %s" % e)
    a, b = os.path.getsize(sys.argv[2]), os.path.getsize(sys.argv[3])
    print("%s (%d bytes) -> %s (%d bytes)" % (sys.argv[2], a, sys.argv[3], b))
