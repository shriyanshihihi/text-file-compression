#!/usr/bin/env python3
"""Command-line entry point.

    python main.py demo                      # 2-minute demo (start here)
    python main.py compress  in.txt out.huf
    python main.py decompress out.huf back.txt
    python main.py stats     in.txt          # entropy, avg code length, code table
"""
import argparse
import hashlib
import os
import sys

from huffman import (CorruptFileError, analyse, compress_bytes, compress_file,
                     decompress_bytes, decompress_file)
from huffman.codec import human_symbol

HERE = os.path.dirname(os.path.abspath(__file__))


def cmd_compress(a):
    compress_file(a.src, a.dst)
    o, c = os.path.getsize(a.src), os.path.getsize(a.dst)
    print("%s: %d -> %d bytes (%.1f%% smaller, ratio %.2fx)" % (a.src, o, c, 100 * (1 - c / o) if o else 0, o / c if c else 0))


def cmd_decompress(a):
    decompress_file(a.src, a.dst)
    print("restored %s (%d bytes)" % (a.dst, os.path.getsize(a.dst)))


def cmd_stats(a):
    with open(a.src, "rb") as f:
        data = f.read()
    s = analyse(data)
    if not s["n"]:
        print("empty file"); return
    print("size %d B | distinct symbols %d | entropy %.3f bits/sym | Huffman avg %.3f bits/sym | fixed-length %d bits/sym"
          % (s["n"], s["distinct"], s["entropy_bits"], s["avg_code_len"], s["fixed_bits"]))
    print("compressed %d B (tree/header ~%d B) -> %.1f%% smaller, ratio %.2fx"
          % (s["compressed"], s["tree_bytes"] + 12, s["reduction_pct"], s["ratio"]))
    print("\n symbol   freq   code")
    for sym in sorted(s["codes"], key=lambda x: (len(s["codes"][x]), -s["freq"][x]))[:a.top]:
        print(" %-7s %6d   %s" % (human_symbol(sym), s["freq"][sym], s["codes"][sym]))


def cmd_demo(_):
    print("=== PART 1: tiny example, so you can SEE the algorithm ===")
    text = b"abracadabra"
    s = analyse(text)
    print("text:", text.decode(), "| 11 chars x 8 bits = 88 bits")
    for sym in sorted(s["codes"], key=lambda x: len(s["codes"][x])):
        print("  %s  freq=%d  code=%s" % (chr(sym), s["freq"][sym], s["codes"][sym]))
    bits = "".join(s["codes"][b] for b in text)
    print("encoded bits:", bits, "(%d bits)" % len(bits))
    print("round trip OK:", decompress_bytes(compress_bytes(text)) == text)
    print("(file is bigger than 11 bytes: header + tree dominate for tiny inputs)\n")

    print("=== PART 2: real(ish) files from sample_data/ ===")
    d = os.path.join(HERE, "sample_data")
    out = os.path.join(HERE, "sample_output")
    os.makedirs(out, exist_ok=True)
    if not os.path.isdir(d) or not os.listdir(d):
        sys.exit("sample_data/ is empty - run: python generate_sample_data.py")
    print("%-18s %9s %11s %9s %7s  lossless" % ("file", "original", "compressed", "smaller", "ratio"))
    for name in sorted(os.listdir(d)):
        src = os.path.join(d, name)
        comp = os.path.join(out, name + ".huf")
        back = os.path.join(out, name + ".restored")
        compress_file(src, comp)
        decompress_file(comp, back)
        h = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
        o, c = os.path.getsize(src), os.path.getsize(comp)
        print("%-18s %9d %11d %8.1f%% %6.2fx  %s" % (name, o, c, 100 * (1 - c / o), o / c, "YES (SHA-256 match)" if h(src) == h(back) else "NO!!"))
        os.remove(back)
    print("\ncompressed files written to sample_output/")


def main():
    p = argparse.ArgumentParser(description="Huffman text file compressor")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name, fn in (("compress", cmd_compress), ("decompress", cmd_decompress)):
        sp = sub.add_parser(name); sp.add_argument("src"); sp.add_argument("dst"); sp.set_defaults(fn=fn)
    sp = sub.add_parser("stats"); sp.add_argument("src"); sp.add_argument("--top", type=int, default=15); sp.set_defaults(fn=cmd_stats)
    sp = sub.add_parser("demo"); sp.set_defaults(fn=cmd_demo)
    a = p.parse_args()
    try:
        a.fn(a)
    except FileNotFoundError as e:
        sys.exit("error: file not found: %s" % e.filename)
    except CorruptFileError as e:
        sys.exit("error: corrupt input: %s" % e)


if __name__ == "__main__":
    main()
