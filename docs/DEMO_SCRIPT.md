# 2-minute demo script

**0:00 - Open** the project folder in the editor. Show the tree: `huffman/` (4 modules), `main.py`, `tests/`, `sample_data/`.

**0:15 - Run** `python main.py demo`

**0:20 - Part 1 of the output (abracadabra).** Point at the code table: `a` (most frequent) gets 1 bit, `c`/`d` get 3 bits.
Say: "88 bits became 23 bits. Frequent symbols get short codes; no code is the start of another, so decoding is unambiguous."

**0:50 - Part 2 of the output (real-ish files).** Point at the table: XML / JSON / source / text, % smaller, ratio, and the "lossless: SHA-256 match" column.
Say: "Every file is decompressed and compared byte-for-byte using a hash - that is how I verify the lossless claim."

**1:10 - Open `huffman/min_heap.py`.** Show `push` / `_sift_up` and `pop` / `_sift_down`. "Custom min-heap, no heapq. O(log n) per operation."

**1:30 - Open `huffman/tree.py` -> `build_tree`.** "Pop two smallest, merge, push back, until one node is left. Tie-break on creation order for deterministic output."

**1:45 - Open `huffman/codec.py`.** Show the header layout in the docstring. "Magic, original length, serialised tree, encoded bits. Original length tells the decoder when to stop."

**1:55 - Optional live run:** `python main.py stats sample_data/users.json` -> show entropy vs Huffman average bits/symbol ("within 1 bit of the theoretical limit").

**Decisions to mention:** byte-level (works on any file), tree stored in header (smaller than a frequency table), min-heap (O(log n) extract-min), deterministic tie-break, honest about limits (header cost on small files; not as strong as gzip).
