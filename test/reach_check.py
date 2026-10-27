#!/usr/bin/env python3
"""reach_check.py <sinc> <reach.txt>: every constructor (instruction or subtable) of the .sinc decodes at least once."""
import os
import re
import sys

sinc = sys.argv[1]
name = os.path.basename(sinc)
cons = []
for n, l in enumerate(open(sinc), 1):
    if re.match(r'^(:|[A-Za-z_][A-Za-z0-9_]*:\s)', l) and ' is ' in l:
        cons.append((n, l.strip()))
seen = set()
for l in open(sys.argv[2]):
    f, _, ln = l.strip().rpartition(':')
    if os.path.basename(f) == name:
        seen.add(int(ln))
miss = [(n, l) for n, l in cons if n not in seen]
print(f'   constructors reached: {len(cons) - len(miss)}/{len(cons)}')
for n, l in miss[:40]:
    print(f'      line {n}: {l[:110]}')
sys.exit(1 if miss else 0)
