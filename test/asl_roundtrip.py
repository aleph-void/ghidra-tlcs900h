#!/usr/bin/env python3
"""asl round trip: assemble the module's disassembly with asl (Alfred Arnold's macro assembler, used as a black box;
CPU 96C141 = TLCS-900 in maximum mode) at each slot's address and compare the bytes with the corpus.
  asl_roundtrip.py asm   <ghidra.txt> <corpus.bin> <workdir> [max]   -> workdir/alt.bin (asl's bytes where they differ)
  asl_roundtrip.py check <workdir> <alt-ghidra.txt>                  -> classes; asl's different bytes must decode
                                                                         (with the module) to the same instruction
Exit status 1 if a slot is neither identical nor an equivalent encoding."""
import json
import collections
import os
import re
import subprocess
import sys

S = 8
ASL = os.environ.get('ASL', 'asl')


def to_asl(t):
    t = t.lower()
    t = re.sub(r':0x([124])\b', r':\1', t)
    t = re.sub(r'0x([0-9a-f]+)', lambda m: '0%sh' % m.group(1), t)
    t = re.sub(r'\b([a-z]+)_([0-3])\b', r'\1\2', t)
    t = re.sub(r'\br(a|w|b|c|d|e|h|l|wa|bc|de|hl)_p\b', r"\1'", t)   # previous bank: RA_P = A', RWA_P = WA'
    t = re.sub(r'\b([a-z]+)_p\b', r"\1'", t)
    return t


def main():
    if sys.argv[1] == 'check':
        return check(sys.argv[2], sys.argv[3])
    del sys.argv[1]
    g = {}
    for l in open(sys.argv[1]):
        if l.startswith('    '):
            continue
        i, ln, t = (l.rstrip('\n').split(' ', 2) + [''])[:3]
        if int(ln):
            g[int(i)] = (int(ln), t)
    data = open(sys.argv[2], 'rb').read()
    w = sys.argv[3]
    os.makedirs(w, exist_ok=True)
    keys = sorted(g)
    if len(sys.argv) > 4:
        step = max(1, len(keys) // int(sys.argv[4]))
        keys = keys[::step]
    def skip(t):
        t = t.lower()
        if 'intnest' in t:
            return True      # asl targets the 900 core (XNSP), not the 900/H
        m = re.match(r'm(inc|dec)[124] 0x([0-9a-f]+)', t)
        if m and int(m.group(2), 16) & (int(m.group(2), 16) - 1):
            return True      # MINC/MDEC modulus not a power of two (manual: 2**n): asl hangs on it
        return False
    keys = [k for k in keys if not skip(g[k][1])]
    CH = 400
    chunks = [keys[i:i + CH] for i in range(0, len(keys), CH)]
    lineof = {}

    def run(ci):
        src = ['\tcpu 96c141', '\tmaxmode on', '\tsupmode on', '\tpage 0']
        lo = {}
        for k in chunks[ci]:
            src.append('\torg 0%xh' % (S * k))
            src.append('\t' + to_asl(g[k][1]))
            lo[len(src)] = k
        a = os.path.join(w, 'rt%d.asm' % ci)
        open(a, 'w').write('\n'.join(src) + '\n')
        try:
            subprocess.run([ASL, '-q', '-L', '-olist', a[:-4] + '.lst', '-o', a[:-4] + '.p', '-maxerrors', '100000', a],
                           cwd=w, capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=120)
        except subprocess.TimeoutExpired:
            print('asl timed out on', a)
        return ci, lo
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(int(os.environ.get('JOBS', '8'))) as ex_:
        res = list(ex_.map(run, range(len(chunks))))
    got = {}
    errs = collections.defaultdict(list)
    for ci, lo in res:
        for ln, k in lo.items():
            lineof[(ci, ln)] = k
        parse(os.path.join(w, 'rt%d.lst' % ci), ci, lo, got, errs)
        for f in ('asm', 'lst', 'p'):
            try:
                os.unlink(os.path.join(w, 'rt%d.%s' % (ci, f)))
            except OSError:
                pass
    report(g, data, lineof, got, errs, w)


def parse(path, ci, lineof, got, errs):
    cur = None
    for l in open(path, errors='replace'):
        m = re.match(r'\s*(\d+)/\s*([0-9A-F]+) :((?: [0-9A-F]{2})*)', l)
        if m:
            cur = int(m.group(1))
            if cur in lineof:
                got.setdefault((ci, cur), b'')
                got[(ci, cur)] += bytes.fromhex(m.group(3).replace(' ', ''))
            continue
        m = re.match(r'\s*\(\s*(\d+)\)\s+([0-9A-F]+) :((?: [0-9A-F]{2})+)', l)   # continuation lines
        if m and cur in lineof:
            got[(ci, cur)] += bytes.fromhex(m.group(3).replace(' ', ''))
            continue
        m = re.search(r'rt\d+\.asm\((\d+)\): error: (.*)', l)
        if m and int(m.group(1)) in lineof:
            errs[(ci, int(m.group(1)))].append(m.group(2).strip())


def report(g, data, lineof, got, errs, w):
    alt = []
    cls = collections.Counter()
    ex = {}
    for ln, k in lineof.items():
        n, t = g[k]
        want = data[S * k:S * k + n]
        b = got.get(ln, b'')
        if ln in errs:
            c = 'asl error: ' + errs[ln][0]
        elif b == want:
            c = 'same bytes'
        elif not b:
            c = 'asl produced nothing'
        else:
            c = 'different bytes'
            alt.append((k, t, want.hex(), b.hex()))
        cls[c] += 1
        if c != 'same bytes':
            shape = re.sub(r'0x[0-9a-f]+', '#', t.lower())
            shape = re.sub(r'_[0-3p]\b', '_n', shape)
            ex.setdefault((c, shape), (want.hex(), b.hex(), t))
    for c, k in cls.most_common():
        print(f'   {k:7d} {c}')
    print(f'   {len(lineof)} slots assembled')
    errex = collections.defaultdict(list)
    for (c, mn), v in ex.items():
        if c != 'different bytes' and len(errex[c]) < 400:
            errex[c].append(v)
    json.dump({'classes': cls, 'alt': alt, 'errex': errex}, open(os.path.join(w, 'rt.json'), 'w'))
    img = bytearray()
    for k, t, want, b in alt:
        img += bytes.fromhex(b)[:S].ljust(S, b'\0')
    open(os.path.join(w, 'alt.bin'), 'wb').write(bytes(img))
    if '--detail' in sys.argv:
        for (c, mn), (w_, b, t) in sorted(ex.items()):
            print(f'   [{c}] {t}   corpus {w_}  asl {b}')


def check(w, altgh):
    r = json.load(open(os.path.join(w, 'rt.json')))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import compare as C
    g = C.load(altgh)
    cls = collections.Counter({k: v for k, v in r['classes'].items() if k not in ('different bytes', 'same bytes')})
    cls['same bytes'] = r['classes'].get('same bytes', 0)
    for c in list(cls):
        if c.startswith('asl error') or c == 'asl produced nothing':
            n_prev = sum(1 for v in r['errex'].get(c, []) if '_P' in v[2])
            if n_prev == len(r['errex'].get(c, [])):
                cls['asl rejects previous-bank names (A\', XWA\'...) in this position (asl syntax: \' starts a string): ' + c] = cls.pop(c)
    for c in list(cls):
        if c == 'asl error: range overflow' and all(v[2].startswith('ldf ') for v in r['errex'].get(c, [])):
            cls['LDF 4-7: asl rejects it in maximum mode (manual: RFP2 stays 0)'] = cls.pop(c)
    bad = []
    for n, (k, t, want, b) in enumerate(r['alt']):
        ln, t2 = g[n]
        same = ln == len(bytes.fromhex(b)) and norm_eq(t, t2, S * k, S * n)
        cls['equivalent encoding (asl picks another form of the same instruction)' if same else 'DIFFERENT'] += 1
        if not same:
            bad.append((t, want, b, t2))
    for c, k in sorted(cls.items(), key=lambda x: -x[1]):
        print(f'   {k:7d} {c}')
    for t, want, b, t2 in bad[:30]:
        print(f'      module: {t} ({want})   asl: {b} -> module: {t2}')
    errs = sum(v for k, v in cls.items() if k.startswith('asl error') or k == 'asl produced nothing')
    print(f'   asl rejected {errs} module texts; {len(bad)} assembled to a different instruction')
    return 1 if bad else 0


def norm_eq(a, b, abase, bbase):
    def n(t, base):
        t = t.lower()
        m = re.match(r'(jr|jrl|djnz|calr|ldar) (.*?)(0x[0-9a-f]+)$', t)
        if m:
            t = '%s %s%+d' % (m.group(1), m.group(2), int(m.group(3), 16) - base)
        t = re.sub(r'^ret t$', 'ret', t)
        t = re.sub(r'\+0x0\b', '', t)               # (XIX+0x0) = (XIX)
        t = re.sub(r'\bjp t,\((0x[0-9a-f]+)\)', r'jp \1', t)
        t = re.sub(r'\bcall t,\((0x[0-9a-f]+)\)', r'call \1', t)
        t = re.sub(r'0x0*([0-9a-f])', r'0x\1', t)
        return t
    return n(a, abase) == n(b, bbase)


if __name__ == '__main__':
    sys.exit(main())
