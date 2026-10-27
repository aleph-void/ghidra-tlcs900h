#!/usr/bin/env python3
"""emu_tests.py <workdir>: write emu.bin (the cases of emu_cases.py, 0x40 bytes apart from 0x1000) and tests.txt for
EmuCheck.java. Each case runs from its first byte to the end of its code."""
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import emu_cases  # noqa: E402

STRIDE, BASE = 0x40, 0x1000
FLAGS = (('SF', 7), ('ZF', 6), ('HF', 4), ('VF', 2), ('NF', 1), ('CF', 0))


def flags(items):
    """F=hh (flag byte S Z - H - V N C) -> the module's flag registers SF ZF HF VF NF CF"""
    out = []
    for kv in items.split(','):
        if kv.startswith('F='):
            v = int(kv[2:], 16)
            out += ['%s=%x' % (n, (v >> b) & 1) for n, b in FLAGS]
        else:
            out.append(kv)
    return ','.join(out)

work = sys.argv[1]
os.makedirs(work, exist_ok=True)
img = bytearray(0x4000)
tests = []
for n, (name, code, init, expect) in enumerate(emu_cases.CASES):
    a = BASE + n * STRIDE
    raw = bytes.fromhex(code)
    assert len(raw) < STRIDE - 8 and a + STRIDE <= 0x2000
    img[a:a + len(raw)] = raw
    expect = re.sub(r'@([0-9a-f]+)', lambda m: '%08x' % (a + int(m.group(1), 16)), expect)
    init = re.sub(r'@([0-9a-f]+)', lambda m: '%08x' % (a + int(m.group(1), 16)), init)
    tests.append(f'{name} {a:x} {a + len(raw):x} {flags(init)} {flags(expect)}')
open(os.path.join(work, 'emu.bin'), 'wb').write(img)
open(os.path.join(work, 'tests.txt'), 'w').write('\n'.join(tests) + '\n')
print(len(tests), 'cases')
