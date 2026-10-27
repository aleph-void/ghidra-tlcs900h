#!/usr/bin/env python3
"""gen_corpus.py <out.bin>: decode corpus of 8-byte slots (an instruction is at most 7 bytes long).
  A: every first/second byte pair, 4 random tails each              (262,144 slots)
  B: every memory-prefix byte 0x80-0xff x 0..4 extension bytes x every operation byte, random tail (163,840)
  C: 65,536 fully random slots
Deterministic (fixed seed)."""
import random
import sys

r = random.Random(0x900)
out = bytearray()


def slot(b):
    b = bytes(b) + bytes(r.getrandbits(8) for _ in range(8 - len(b)))
    out.extend(b[:8])


for b0 in range(256):
    for b1 in range(256):
        for _ in range(4):
            slot([b0, b1])
for b0 in range(0x80, 0x100):
    for ext in range(5):
        for op in range(256):
            slot([b0] + [r.getrandbits(8) for _ in range(ext)] + [op])
for _ in range(65536):
    slot([])
open(sys.argv[1], 'wb').write(out)
print(len(out) // 8, 'slots')
