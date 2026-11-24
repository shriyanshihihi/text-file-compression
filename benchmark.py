#!/usr/bin/env python3
"""Benchmark every file in sample_data/ and write sample_output/benchmark_results.md

Columns
  Huffman ratio     = original size / compressed size  (includes 12-byte header + stored tree)
  Fixed-8bit ratio  = 1.00 by definition (plain ASCII/UTF-8 uses 8 bits per byte)
  Fixed-k ratio     = original / (n * ceil(log2 k) bits)  -> a smarter fixed-length code
  zlib-9 ratio      = for context only (LZ77 + Huffman, a stronger tool)
Every file is also checked with a round trip + SHA-256 comparison.
"""
import hashlib
import os
import time
import zlib

from huffman import analyse, compress_bytes, decompress_bytes

HERE = os.path.dirname(os.path.abspath(__file__))
D = os.path.join(HERE, "sample_data")


def main():
    rows, ratios, reductions = [], [], []
    for name in sorted(os.listdir(D)):
        data = open(os.path.join(D, name), "rb").read()
        t0 = time.perf_counter(); blob = compress_bytes(data); t1 = time.perf_counter()
        back = decompress_bytes(blob); t2 = time.perf_counter()
        ok = hashlib.sha256(back).hexdigest() == hashlib.sha256(data).hexdigest()
        s = analyse(data)
        fixed_k = len(data) / (len(data) * s["fixed_bits"] / 8)
        rows.append((name, len(data), len(blob), s["reduction_pct"], s["ratio"], fixed_k,
                     len(data) / len(zlib.compress(data, 9)), s["entropy_bits"], s["avg_code_len"],
                     t1 - t0, t2 - t1, ok))
        ratios.append(s["ratio"]); reductions.append(s["reduction_pct"])
    hdr = "| file | original B | compressed B | reduction | Huffman ratio | fixed-k ratio | zlib-9 ratio | entropy b/sym | Huffman b/sym | enc s | dec s | lossless |\n|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    body = "".join("| %s | %d | %d | %.1f%% | %.2fx | %.2fx | %.2fx | %.2f | %.2f | %.3f | %.3f | %s |\n"
                   % (r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], "yes" if r[11] else "NO") for r in rows)
    summary = "\n**Average reduction: %.1f%%  |  average Huffman ratio vs 8-bit ASCII: %.2fx**\n" % (sum(reductions) / len(reductions), sum(ratios) / len(ratios))
    note = "\n_Measured on the SYNTHETIC demo files in sample_data/ (plus this project's own source). Not the original CV dataset._\n"
    text = "# Benchmark results\n\n" + hdr + body + summary + note
    print(text)
    os.makedirs(os.path.join(HERE, "sample_output"), exist_ok=True)
    open(os.path.join(HERE, "sample_output", "benchmark_results.md"), "w").write(text)


if __name__ == "__main__":
    main()
