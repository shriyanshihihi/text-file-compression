#!/usr/bin/env python3
"""Creates SYNTHETIC sample files in sample_data/ (fixed random seed -> reproducible).

   *** All XML / JSON / text content below is made-up demo data. ***
   The source-code sample is this project's own real source code.

Results on these files are NOT the results from the original CV project.
"""
import json
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "sample_data")
rnd = random.Random(42)

WORDS = ("compression data file system memory process thread network server client request response "
         "buffer stream encoder decoder symbol frequency tree node heap queue sorted lossless reduction "
         "storage backup archive report analysis student course library project result value config "
         "device sensor reading battery panel module version release update install package").split()
FIRST = "Aarav Diya Rohan Meera Kabir Anaya Vikram Isha Arjun Sara Neel Riya Dev Tara Kunal Pooja".split()
LAST = "Sharma Verma Iyer Nair Singh Gupta Rao Mehta Das Patel Khan Joshi Reddy Bose".split()
CITIES = "Pune Delhi Mumbai Chennai Jaipur Kolkata Lucknow Indore Nagpur Surat".split()


def sentence(n):
    return " ".join(rnd.choice(WORDS) for _ in range(n)).capitalize() + "."


def make_xml(path, items=330):
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<catalog>"]
    for i in range(items):
        lines += ['  <product id="P%05d" category="%s">' % (rnd.randint(0, 99999), rnd.choice(WORDS)),
                  "    <name>%s %s</name>" % (rnd.choice(WORDS).title(), rnd.choice(WORDS).title()),
                  "    <price currency=\"INR\">%d.%02d</price>" % (rnd.randint(50, 9999), rnd.randint(0, 99)),
                  "    <stock>%d</stock>" % rnd.randint(0, 500),
                  "    <description>%s</description>" % sentence(rnd.randint(6, 14)),
                  "  </product>"]
    lines.append("</catalog>")
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")


def make_json(path, items=300):
    recs = []
    for i in range(items):
        recs.append({"id": rnd.randint(1000, 999999), "name": "%s %s" % (rnd.choice(FIRST), rnd.choice(LAST)),
                     "city": rnd.choice(CITIES), "age": rnd.randint(18, 70), "active": rnd.random() < 0.7,
                     "balance": round(rnd.uniform(0, 100000), 2),
                     "tags": [rnd.choice(WORDS) for _ in range(rnd.randint(1, 4))],
                     "notes": sentence(rnd.randint(5, 12))})
    json.dump({"users": recs}, open(path, "w", encoding="utf-8"), indent=2)


def make_text(path, sentences=450):
    open(path, "w", encoding="utf-8").write("\n".join(sentence(rnd.randint(8, 18)) for _ in range(sentences)) + "\n")


def make_code(path):
    """REAL source code: this project's own modules, concatenated."""
    parts = []
    for name in ("min_heap.py", "tree.py", "bitio.py", "codec.py"):
        parts.append(open(os.path.join(HERE, "huffman", name), encoding="utf-8").read())
    parts.append(open(os.path.join(HERE, "main.py"), encoding="utf-8").read())
    open(path, "w", encoding="utf-8").write("\n".join(parts))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    make_xml(os.path.join(OUT, "catalog.xml"))
    make_json(os.path.join(OUT, "users.json"))
    make_text(os.path.join(OUT, "notes.txt"))
    make_code(os.path.join(OUT, "project_source.py.txt"))
    print("wrote sample files to", OUT)
