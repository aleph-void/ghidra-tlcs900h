#!/usr/bin/env python3
"""real_compare.py <listing> <rom> <base-hex> [jobs]: compare the module's analysed listing ("<addr> <bytes> <text>",
from RealCheck.java) with MAME's unidasm (black box) decoding the ROM at the same addresses. Differences must be in a
class of check_explained.py. Exit status 1 on an unexplained difference."""
import collections
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare as C  # noqa: E402
import check_explained as E  # noqa: E402

lst, rom, base = sys.argv[1], open(sys.argv[2], 'rb').read(), int(sys.argv[3], 16)
jobs = int(sys.argv[4]) if len(sys.argv) > 4 else 8
rows = []
for l in open(lst):
    a, h, t = l.rstrip('\n').split(' ', 2)
    rows.append((int(a, 16), h, t))
tmp = tempfile.mkdtemp(dir=os.environ.get('TMPDIR'))


def uni(row):
    a, h, t = row
    p = os.path.join(tmp, '%x.bin' % a)
    open(p, 'wb').write(rom[a - base:a - base + 8])
    r = subprocess.run([os.environ.get('UNIDASM', 'unidasm'), p, '-arch', 'tlcs900', '-basepc', '%x' % a, '-count', '1'],
                       capture_output=True, text=True)
    os.unlink(p)
    line = r.stdout.splitlines()[0] if r.stdout.strip() else ''
    _, _, rest = line.partition(':')
    toks = rest.split()
    if toks and toks[-1] == 'db' and all(len(x) == 2 for x in toks):
        return 0, 'db'
    nb = 0
    while nb < len(toks) and len(toks[nb]) == 2 and all(c in '0123456789abcdef' for c in toks[nb]):
        nb += 1
    return nb, ' '.join(toks[nb:])


with ThreadPoolExecutor(jobs) as ex:
    res = list(ex.map(uni, rows))
os.rmdir(tmp)
cls = collections.Counter()
bad = []
for (a, h, t), (ul, ut) in zip(rows, res):
    b = rom[a - base:a - base + 8]
    c = C.classify(len(h) // 2, t, ul, ut, b)
    if c not in ('exact',):
        r = E.reason(b) if c == 'module undefined, unidasm decodes' else None
        if c == 'length differs' and b[0] == 0xf7:
            r = 'LDX (unidasm bug)'
        if c == 'operands differ' and 'intnest' in t.lower():
            r = 'INTNEST'
        c = r or 'UNEXPLAINED ' + c
        if not r:
            bad.append((a, h, t, ut))
    cls[c] += 1
for c, n in cls.most_common():
    print(f'   {n:6d} {c}')
for a, h, t, ut in bad[:30]:
    print(f'      {a:08x} {h}  module: {t}  unidasm: {ut}')
print(f'   {len(rows)} instructions compared, {len(bad)} unexplained')
sys.exit(1 if bad else 0)
