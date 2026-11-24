"""Run:  python -m unittest discover -s tests -v"""
import math
import os
import random
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from huffman import (CorruptFileError, MinHeap, analyse, build_codes, build_tree, compress_bytes,
                     compress_file, count_frequencies, decompress_bytes, decompress_file)


def rt(data):
    return decompress_bytes(compress_bytes(data))


class TestMinHeap(unittest.TestCase):
    def test_pops_in_sorted_order(self):
        rnd = random.Random(1)
        xs = [rnd.randint(0, 1000) for _ in range(500)]
        h = MinHeap()
        for x in xs:
            h.push(x)
        self.assertEqual([h.pop() for _ in xs], sorted(xs))

    def test_empty_pop_raises(self):
        with self.assertRaises(IndexError):
            MinHeap().pop()


class TestRoundTrip(unittest.TestCase):
    def test_empty(self): self.assertEqual(rt(b""), b"")
    def test_one_byte(self): self.assertEqual(rt(b"a"), b"a")
    def test_single_repeated_symbol(self): self.assertEqual(rt(b"z" * 1000), b"z" * 1000)
    def test_two_symbols(self): self.assertEqual(rt(b"ab" * 77 + b"a"), b"ab" * 77 + b"a")
    def test_all_256_bytes(self): self.assertEqual(rt(bytes(range(256)) * 3), bytes(range(256)) * 3)
    def test_random_binary(self):
        d = random.Random(2).randbytes(20000); self.assertEqual(rt(d), d)
    def test_unicode_text(self):
        d = "नमस्ते दुनिया — café ✓ 日本語\n".encode("utf-8") * 50; self.assertEqual(rt(d), d)
    def test_skewed_deep_tree(self):          # Fibonacci-like frequencies -> maximally deep tree
        d = b"".join(bytes([i]) * f for i, f in enumerate([1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144]))
        self.assertEqual(rt(d), d)
    def test_deterministic(self):
        d = b"the quick brown fox jumps over the lazy dog" * 10
        self.assertEqual(compress_bytes(d), compress_bytes(d))


class TestProperties(unittest.TestCase):
    def setUp(self):
        self.data = open(os.path.join(os.path.dirname(__file__), "test_huffman.py"), "rb").read()

    def test_prefix_free(self):
        codes = ["{:0{}b}".format(v, l) for v, l in build_codes(build_tree(count_frequencies(self.data))).values()]
        for a in codes:
            for b in codes:
                if a != b:
                    self.assertFalse(b.startswith(a))

    def test_close_to_entropy(self):          # Shannon: H <= avg length < H + 1
        s = analyse(self.data)
        self.assertGreaterEqual(s["avg_code_len"] + 1e-9, s["entropy_bits"])
        self.assertLess(s["avg_code_len"], s["entropy_bits"] + 1)

    def test_frequent_symbols_get_shorter_codes(self):
        s = analyse(self.data); f = s["freq"]; c = s["codes"]
        most = max(c, key=lambda x: f[x]); least = min(c, key=lambda x: f[x])
        self.assertLessEqual(len(c[most]), len(c[least]))


class TestErrors(unittest.TestCase):
    def test_bad_magic(self):
        with self.assertRaises(CorruptFileError): decompress_bytes(b"NOPE" + bytes(20))
    def test_too_short(self):
        with self.assertRaises(CorruptFileError): decompress_bytes(b"HU")
    def test_truncated(self):
        blob = compress_bytes(b"hello world " * 100)
        with self.assertRaises(CorruptFileError): decompress_bytes(blob[:-20])
    def test_garbage_tree_does_not_crash_with_recursion(self):
        with self.assertRaises(CorruptFileError): decompress_bytes(b"HUF1" + (50).to_bytes(8, "big") + bytes(5000))


class TestFiles(unittest.TestCase):
    def test_file_round_trip(self):
        with tempfile.TemporaryDirectory() as d:
            src, c, out = (os.path.join(d, n) for n in ("a.txt", "a.huf", "b.txt"))
            open(src, "wb").write(b'{"key": "value"}\n' * 500)
            compress_file(src, c); decompress_file(c, out)
            self.assertEqual(open(src, "rb").read(), open(out, "rb").read())
            self.assertLess(os.path.getsize(c), os.path.getsize(src))


if __name__ == "__main__":
    unittest.main()
