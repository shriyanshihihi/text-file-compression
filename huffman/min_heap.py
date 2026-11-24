"""Custom binary Min-Heap (written from scratch, no `heapq`).

A binary heap is a complete binary tree stored in a plain Python list:
    parent of index i  -> (i - 1) // 2
    children of index i -> 2*i + 1  and  2*i + 2
Rule ("heap property"): every parent is <= its children, so the smallest
item is always at index 0.

Costs:  push = O(log n)   pop = O(log n)   peek = O(1)
Why Huffman needs it: at every step we must pull out the TWO smallest-
frequency nodes. A heap gives that in O(log n) instead of re-sorting (O(n log n))
or scanning (O(n)) on every step.
"""
from __future__ import annotations


class MinHeap:
    """Min-heap of any objects that support the `<` operator."""

    def __init__(self) -> None:
        self._a: list = []

    def __len__(self) -> int:
        return len(self._a)

    def peek(self):
        """Return (without removing) the smallest item. O(1)."""
        if not self._a:
            raise IndexError("peek from empty heap")
        return self._a[0]

    def push(self, item) -> None:
        """Add an item at the end, then let it float UP to its place. O(log n)."""
        self._a.append(item)
        self._sift_up(len(self._a) - 1)

    def pop(self):
        """Remove and return the smallest item. O(log n).

        Trick: move the LAST item to the root (keeps the tree complete),
        then let it sink DOWN to its correct position.
        """
        a = self._a
        if not a:
            raise IndexError("pop from empty heap")
        smallest = a[0]
        last = a.pop()
        if a:                       # heap not empty after removing last item
            a[0] = last
            self._sift_down(0)
        return smallest

    # ---- internal helpers -------------------------------------------------
    def _sift_up(self, i: int) -> None:
        a = self._a
        item = a[i]
        while i > 0:
            parent = (i - 1) // 2
            if item < a[parent]:    # child smaller than parent -> swap upward
                a[i] = a[parent]
                i = parent
            else:
                break
        a[i] = item

    def _sift_down(self, i: int) -> None:
        a = self._a
        n = len(a)
        item = a[i]
        while True:
            child = 2 * i + 1       # left child
            if child >= n:
                break
            right = child + 1
            if right < n and a[right] < a[child]:   # pick the smaller child
                child = right
            if a[child] < item:     # smaller child beats us -> move it up
                a[i] = a[child]
                i = child
            else:
                break
        a[i] = item
