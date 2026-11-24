"""Huffman tree: node type, frequency counting, tree building, code table,
and tree (de)serialisation for the file header."""
from __future__ import annotations

from .bitio import BitReader, BitWriter
from .min_heap import MinHeap


class CorruptFileError(ValueError):
    """Raised when a compressed file is damaged or not in our format."""


class Node:
    """A tree node. Leaf = has a `symbol` (a byte value 0-255). Internal = has two children."""

    __slots__ = ("freq", "symbol", "left", "right", "order")

    def __init__(self, freq=0, symbol=None, left=None, right=None, order=0):
        self.freq = freq
        self.symbol = symbol
        self.left = left
        self.right = right
        self.order = order      # creation counter -> deterministic tie-breaking

    def is_leaf(self) -> bool:
        return self.left is None and self.right is None

    def __lt__(self, other: "Node") -> bool:
        # Smaller frequency first; if equal, the older node first.
        # Without the tie-break, equal-frequency nodes could be merged in a
        # different order on different runs -> different (but equally optimal) trees.
        return (self.freq, self.order) < (other.freq, other.order)


# --------------------------------------------------------------------------
# Step 1: count how often each byte occurs            -> O(n)
# --------------------------------------------------------------------------
def count_frequencies(data: bytes) -> list:
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    return freq


# --------------------------------------------------------------------------
# Step 2: build the tree with the min-heap             -> O(k log k), k = distinct symbols
# --------------------------------------------------------------------------
def build_tree(freq: list):
    """Greedy Huffman: repeatedly merge the two least-frequent nodes."""
    heap = MinHeap()
    order = 0
    for symbol, f in enumerate(freq):
        if f > 0:
            heap.push(Node(f, symbol=symbol, order=order))
            order += 1
    if len(heap) == 0:
        return None
    while len(heap) > 1:
        first = heap.pop()      # smallest
        second = heap.pop()     # second smallest
        heap.push(Node(first.freq + second.freq, left=first, right=second, order=order))
        order += 1
    return heap.pop()


# --------------------------------------------------------------------------
# Step 3: walk the tree to get a code for each byte    -> O(k)
# --------------------------------------------------------------------------
def build_codes(root) -> dict:
    """Return {symbol: (code_value, code_length)}. Left edge = 0, right edge = 1."""
    if root is None:
        return {}
    if root.is_leaf():                  # file with only ONE distinct byte
        return {root.symbol: (0, 1)}    # give it the 1-bit code '0'
    codes = {}
    stack = [(root, 0, 0)]              # (node, bits_so_far, length)
    while stack:
        node, value, length = stack.pop()
        if node.is_leaf():
            codes[node.symbol] = (value, length)
        else:
            stack.append((node.right, (value << 1) | 1, length + 1))
            stack.append((node.left, value << 1, length + 1))
    return codes


def code_string(value: int, length: int) -> str:
    """Human-readable form, e.g. (5, 3) -> '101'. Used only for display."""
    return format(value, "0{}b".format(length))


# --------------------------------------------------------------------------
# Step 4: store / restore the tree inside the compressed file
# --------------------------------------------------------------------------
def write_tree(root, writer: BitWriter) -> None:
    """Pre-order walk: internal node -> bit 0 ; leaf -> bit 1 + 8 bits of symbol.
    Size = (2k - 1) structure bits + 8k symbol bits.  Time O(k)."""
    stack = [root]
    while stack:
        node = stack.pop()
        if node.is_leaf():
            writer.write_bit(1)
            writer.write_bits(node.symbol, 8)
        else:
            writer.write_bit(0)
            stack.append(node.right)    # pushed first -> visited second
            stack.append(node.left)


def read_tree(reader: BitReader):
    """Rebuild the tree from the bit stream in ONE pass -> O(number of nodes) = O(k).
    Iterative (explicit stack) so a corrupted file cannot overflow Python's recursion limit."""
    pending = []                # internal nodes still waiting for children
    leaves = 0
    while True:
        if reader.read_bit() == 1:                      # leaf
            leaves += 1
            if leaves > 256:
                raise CorruptFileError("tree has more than 256 leaves")
            node = Node(symbol=reader.read_bits(8))
            while True:                                 # hand the finished node to its parent
                if not pending:
                    return node                         # no parent -> this is the root
                parent = pending[-1]
                if parent.left is None:
                    parent.left = node
                    break
                parent.right = node
                pending.pop()
                node = parent                           # parent is now complete too
        else:                                           # internal node
            pending.append(Node())
