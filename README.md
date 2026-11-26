# Text File Compression - Huffman Coding, Min-Heap, File I/O

A small course-style project: compress any text file with **Huffman coding** (custom **Min-Heap**, raw **file I/O**) and get the exact file back.

```
python huffman.py compress   sample_data/poetry_schema.json  out.huf
python huffman.py decompress out.huf                         restored.json
python benchmark.py          # benchmark on XML / JSON / source code / text + checks every CV claim
```
Python 3.8+, standard library only. **Files:** `huffman.py` (the whole algorithm, ~200 lines including comments), `benchmark.py`, `sample_data/` (10 real files), `benchmark_results.txt` (saved output).

## How it works
```
compress:    bytes -> count frequencies -> Min-Heap builds Huffman tree -> code table -> header + tree + encoded bits
decompress:  read header -> rebuild tree from the stored bits -> walk tree bit by bit (0 = left, 1 = right) -> bytes
file layout: "HUF1" | original length (8 bytes) | tree (pre-order bits) | data bits | zero padding
```

## CV line -> where it is justified

| CV words | Where / how it is justified |
|---|---|
| **Huffman Coding**, "from scratch" | `huffman.py` imports only `os`, `struct`, `sys` (`benchmark.py` checks this). No zlib/gzip/heapq. |
| **custom Min-Heap** | `class MinHeap` in `huffman.py`: array heap, `push` (sift up) and `pop` (sift down), both O(log n). Used by `build_tree`. |
| **45% average file size reduction** on text datasets | `benchmark.py` prints % smaller per file and on average. Real files, size on disk **including header + tree**. Result: **44.8%** over 10 files. |
| **O(n log n) Huffman encoding** | Tree build = ~2k heap operations, each O(log k) -> O(k log k), where **n = k = number of distinct bytes (at most 256)**. Counting and encoding the file are O(m) for m bytes. |
| **O(n) tree reconstruction** | `read_tree` reads each of the 2k-1 nodes exactly once from the header, no heap needed -> O(n), where **n = number of tree nodes**. |
| **100% lossless data recovery** | `benchmark.py` decompresses every file and compares bytes with the original (10/10 identical), plus 8 edge cases (empty, 1 byte, 1 symbol, all 256 byte values, random binary, UTF-8, deepest tree, truncated file). |
| **XML, JSON & source code files** | `sample_data/`: 3 XML, 3 JSON, 3 Python source files (+1 text file). |
| outperforming **fixed-length ASCII** by **2x** on average compression ratio | Fixed-length ASCII = 8 bits per character = original size (ratio 1.00x). Huffman average ratio measured: **1.82x**. Exactly 2x needs 50% reduction, which these files do not reach - see the note below. |

### Honest note about "2x"
A 45% reduction means the file is 55% of its size, which is a ratio of 1/0.55 = **1.82x**, not 2.0x. On the sample files the ratio ranges from 1.71x to 1.95x (average 1.82x). If your own measurement said 2x, check how it was calculated; otherwise write **"about 1.8x (45% smaller)"**.

### Other things to know (limitations)
- Byte-level Huffman only uses how often each byte occurs, so it cannot exploit repeated words/tags. zlib (LZ77 + Huffman) gets 3-7x on the same files; `benchmark.py` prints it for context.
- Tiny files can get bigger (12-byte header + tree). Whole file is read into memory. Bits are handled as Python strings for readability, so it is slow for big files.

### Sample data (real files, not generated)
Chosen by size (12-52 KB) and permissive licence, not by compression result.
ImageMagick `english.xml`, `type-apple.xml` (ImageMagick licence) · liblangtag `currency.xml` · Poetry `poetry-schema.json` (MIT) · iso-codes `iso_3166-1.json`, `iso_4217.json` (LGPL) · Python standard library `json/decoder.py`, `shlex.py`, `textwrap.py` (PSF licence) · Apache License 2.0 text.
