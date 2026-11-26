#!/usr/bin/env python3
"""Benchmark + check of every CV claim.      Run:  python benchmark.py

1. compresses every file in sample_data/ (XML, JSON, source code, text) and decompresses it again
2. compares the restored bytes with the original  -> lossless check
3. compares the size with fixed-length ASCII (8 bits per character = the original file size)
4. runs edge-case tests (empty file, 1 byte, 1 symbol, all 256 bytes, random binary ...)
5. prints a verdict for each CV claim
"""
import os
import random
import re
import time
import zlib

from huffman import build_tree, compress_bytes, count_frequencies, decompress_bytes

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "sample_data")
KIND = {".xml": "XML", ".json": "JSON", ".py": "source code", ".txt": "text"}

# ---------------------------------------------------------------- 1-3: real files
rows = []
for name in sorted(os.listdir(DATA)):
    data = open(os.path.join(DATA, name), "rb").read()
    t0 = time.perf_counter()
    blob = compress_bytes(data)
    t1 = time.perf_counter()
    restored = decompress_bytes(blob)
    t2 = time.perf_counter()
    k = sum(1 for f in count_frequencies(data) if f)
    rows.append(dict(name=name, kind=KIND[os.path.splitext(name)[1]], orig=len(data), comp=len(blob),
                     red=100 * (1 - len(blob) / len(data)), ratio=len(data) / len(blob),
                     zlib=len(data) / len(zlib.compress(data, 9)), k=k, ok=(restored == data),
                     t_enc=t1 - t0, t_dec=t2 - t1))

print("%-28s %-11s %8s %8s %8s %7s %5s %9s" % ("file", "type", "original", "huffman", "smaller", "ratio", "k", "lossless"))
for r in rows:
    print("%-28s %-11s %8d %8d %7.1f%% %6.2fx %5d %9s" % (r["name"], r["kind"], r["orig"], r["comp"], r["red"], r["ratio"], r["k"], "yes" if r["ok"] else "NO"))
print("\nAverage per file type (fixed-length ASCII = 8 bits/char, ratio 1.00x by definition):")
for kind in ("XML", "JSON", "source code", "text"):
    g = [r for r in rows if r["kind"] == kind]
    print("  %-12s %d files   %.1f%% smaller   ratio %.2fx   (zlib, for context only: %.2fx)" % (
        kind, len(g), sum(r["red"] for r in g) / len(g), sum(r["ratio"] for r in g) / len(g), sum(r["zlib"] for r in g) / len(g)))
avg_red = sum(r["red"] for r in rows) / len(rows)
avg_ratio = sum(r["ratio"] for r in rows) / len(rows)
print("  %-12s %d files   %.1f%% smaller   ratio %.2fx" % ("ALL", len(rows), avg_red, avg_ratio))

# ---------------------------------------------------------------- 4: edge cases
rnd = random.Random(1)
cases = {"empty file": b"", "one byte": b"a", "one repeated symbol": b"z" * 1000, "two symbols": b"ab" * 50 + b"a",
         "all 256 byte values": bytes(range(256)) * 4, "random binary 20 KB": bytes(rnd.getrandbits(8) for _ in range(20000)),
         "UTF-8 text": "नमस्ते café 日本語\n".encode("utf-8") * 40,
         "deepest tree (Fibonacci counts)": b"".join(bytes([i]) * f for i, f in enumerate([1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89]))}
print("\nEdge cases (compress -> decompress -> identical?):")
edge_ok = True
for label, data in cases.items():
    ok = decompress_bytes(compress_bytes(data)) == data
    edge_ok &= ok
    print("  %-34s %s" % (label, "PASS" if ok else "FAIL"))
try:
    decompress_bytes(compress_bytes(b"hello world" * 50)[:-10])
    print("  truncated file                     FAIL (no error raised)"); edge_ok = False
except ValueError:
    print("  truncated file                     PASS (clear error raised)")

# ---------------------------------------------------------------- 5: CV claim check
src = open(os.path.join(HERE, "huffman.py")).read()
imports = sorted(set(re.findall(r"^(?:import|from)\s+(\w+)", src, re.M)))
all_ok = all(r["ok"] for r in rows) and edge_ok
kinds = sorted({r["kind"] for r in rows})
print("\n================ CV CLAIM CHECK ================")
print("Implemented Huffman Coding from scratch ....... imports used: %s -> %s" % (", ".join(imports), "PASS" if not {"heapq", "zlib", "gzip", "bz2", "lzma"} & set(imports) else "FAIL"))
print("... via a custom Min-Heap ..................... class MinHeap in huffman.py (push/pop with sift up/down)")
print("45%% average file size reduction ............... measured %.1f%% over %d files -> %s" % (avg_red, len(rows), "CONSISTENT" if abs(avg_red - 45) <= 3 else "DIFFERENT"))
print("O(n log n) encoding / O(n) tree rebuild ....... see complexity table in huffman.py; k<=256 distinct bytes, tree has 2k-1 nodes")
print("100%% lossless data recovery across files ...... %d/%d files + %d edge cases -> %s" % (sum(r["ok"] for r in rows), len(rows), len(cases), "PASS" if all_ok else "FAIL"))
print("Benchmarked across XML, JSON & source code .... file types tested: %s -> %s" % (", ".join(kinds), "PASS" if {"XML", "JSON", "source code"} <= set(kinds) else "FAIL"))
print("Outperforming fixed-length ASCII by 2x ........ measured %.2fx average ratio -> %s" % (avg_ratio, "REACHED" if avg_ratio >= 2.0 else "NOT REACHED (45%% smaller = 1.82x; honest wording: about %.1fx)" % avg_ratio))
