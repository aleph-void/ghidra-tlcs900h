#!/usr/bin/env python3
"""unidasm_slots.py <corpus.bin> <out.txt> [jobs] [arch] [slot]: MAME's unidasm (black box) on each slot, at its own
address (slot n at n*slot). Output "<slot> <length> <text>" for the first instruction of the slot; unidasm's "db"
(undefined) gives length 0."""
import os
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

data = open(sys.argv[1], 'rb').read()
jobs = int(sys.argv[3]) if len(sys.argv) > 3 else 8
arch = sys.argv[4] if len(sys.argv) > 4 else 'tlcs900'
S = int(sys.argv[5]) if len(sys.argv) > 5 else 8
unidasm = os.environ.get('UNIDASM', 'unidasm')
tmp = tempfile.mkdtemp(prefix='unidasm.', dir=os.environ.get('TMPDIR'))
BATCH = 512


def batch(k):
    """unidasm on each slot of a batch of BATCH slots, one process per slot"""
    res = []
    for n in range(k, min(k + BATCH, len(data) // S)):
        p = os.path.join(tmp, f'{n}.bin')
        open(p, 'wb').write(data[S * n:S * n + S])
        rr = subprocess.run([unidasm, p, '-arch', arch, '-basepc', hex(S * n), '-count', '1'], capture_output=True, text=True)
        os.unlink(p)
        line = rr.stdout.splitlines()[0] if rr.stdout.strip() else ''
        try:
            addr, rest = line.split(':', 1)
            toks = rest.split()
            if toks and toks[-1] == 'db' and all(len(t) == 2 for t in toks):
                res.append((n, 0, 'db'))      # undefined ("db" is also two hex digits)
                continue
            nb = 0
            while nb < len(toks) and len(toks[nb]) == 2 and all(c in '0123456789abcdef' for c in toks[nb]):
                nb += 1
            text = ' '.join(rest.split()[nb:])
            if text == 'db' or text.startswith('db '):
                nb = 0
            res.append((n, nb, text))
        except ValueError:
            res.append((n, 0, 'ERR ' + (rr.stdout + rr.stderr)[:60]))
    return res


with ThreadPoolExecutor(jobs) as ex, open(sys.argv[2], 'w') as f:
    for res in ex.map(batch, range(0, len(data) // S, BATCH)):
        for n, ln, text in res:
            f.write(f'{n} {ln} {text}\n')
os.rmdir(tmp)
