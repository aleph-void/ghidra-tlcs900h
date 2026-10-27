#!/usr/bin/env python3
"""compare.py <ghidra.txt> <unidasm.txt> <corpus.bin> [--detail] [--show N] [--slot S]: module vs MAME unidasm.
Spelling is normalised (case, number radix, register-bank suffixes); see norm()."""
import collections
import re
import sys

S = int(sys.argv[sys.argv.index('--slot') + 1]) if '--slot' in sys.argv else 8


def num(m):
    return 'n%x' % int(m.group(0), 0)


CC = {'pe/ov': 'ov', 'm/mi': 'mi', 'po/nov': 'nov', 'p/pl': 'pl'}
B2W = {}
for b, w in (('a', 'wa'), ('c', 'bc'), ('e', 'de'), ('l', 'hl'), ('ixl', 'ix'), ('iyl', 'iy'), ('izl', 'iz'), ('spl', 'sp'),
             ('qa', 'qwa'), ('qc', 'qbc'), ('qe', 'qde'), ('ql', 'qhl'), ('qixl', 'qix'), ('qiyl', 'qiy'), ('qizl', 'qiz'), ('qspl', 'qsp')):
    B2W[b] = w
for n in ('0', '1', '2', '3', '_p'):
    for b, w in (('ra', 'rwa'), ('rc', 'rbc'), ('re', 'rde'), ('rl', 'rhl'), ('qa', 'qwa'), ('qc', 'qbc'), ('qe', 'qde'), ('ql', 'qhl')):
        B2W[b + n] = w + n
W2L = {'wa': 'xwa', 'bc': 'xbc', 'de': 'xde', 'hl': 'xhl', 'ix': 'xix', 'iy': 'xiy', 'iz': 'xiz', 'sp': 'xsp'}
for n in ('0', '1', '2', '3', '_p'):
    for w, l in (('rwa', 'xwa'), ('rbc', 'xbc'), ('rde', 'xde'), ('rhl', 'xhl')):
        W2L[w + n] = l + n
NOOPS = ('ldi', 'ldir', 'ldd', 'lddr', 'ldiw', 'ldirw', 'lddw', 'lddrw', 'cpi', 'cpir', 'cpd', 'cpdr', 'cpiw', 'cpirw', 'cpdw', 'cpdrw')


def sdisp(m):
    """unidasm prints the d8/d16 displacements unsigned"""
    h = m.group(2)
    v = int(h, 16)
    bits = 8 if len(h) == 2 else 16
    if v >= 1 << (bits - 1):
        return '%s-0x%x' % (m.group(1), (1 << bits) - v)
    return '%s+0x%x' % (m.group(1), v)


def norm(t, ref=False):
    t = t.strip().lower()
    t = re.sub(r'\s+', ' ', t)
    if ref:
        t = re.sub(r'([a-z0-9\']+)\+0x([0-9a-f]{2}|[0-9a-f]{4})\b', sdisp, t)
    t = re.sub(r':(0x)?[124]\b', '', t)               # module: explicit (r+)/(-r) step
    t = re.sub(r'\b([a-z]+)-1\b', r'\1_p', t)        # previous bank: XWA-1 (unidasm) = XWA_P (module)
    t = re.sub(r'(?<![\w])(0x[0-9a-f]+|\d+)(?![\w])', num, t)
    t = re.sub(r'_(\d)\b', r'\1', t)           # XWA_0 (module) = XWA0 (unidasm)
    t = t.replace(', ', ',')
    mn, _, ops = t.partition(' ')
    ol = ops.split(',') if ops else []
    ol = [CC.get(o, o) for o in ol]
    if mn in NOOPS:
        ol = []
    if mn in ('jp', 'call') and ol and ol[-1].startswith('(') and ol[-1].endswith(')'):
        ol[-1] = ol[-1][1:-1]
    if ref and mn in ('retd', 'link') and ol and ol[-1].startswith('n'):
        v = int(ol[-1][1:], 16)
        if v >= 0x8000:
            ol[-1] = '-n%x' % (0x10000 - v)
    if mn == 'ldar':
        mn = 'lda'
    if ref and mn in ('inc', 'dec', 'incw', 'decw') and ol and ol[0] == 'n0':
        ol[0] = 'n8'
    if ref and mn in ('rlc', 'rrc', 'rl', 'rr', 'sla', 'sra', 'sll', 'srl') and len(ol) == 2 and ol[0] == 'n0':
        ol[0] = 'n10'
    if ref and re.match(r'm(inc|dec)[124]$', mn) and ol:
        ol[0] = 'n%x' % (int(ol[0][1:], 16) + int(mn[-1]))      # unidasm prints the encoded # - n
    return mn + (' ' + ','.join(ol) if ol else '')



def key(t, ref=False):
    t = norm(t, ref)
    mn, _, ops = t.partition(' ')
    return mn, tuple(o.strip() for o in ops.split(',')) if ops else ()


def load(p):
    d = {}
    for l in open(p):
        if l.startswith('    '):
            continue
        i, ln, t = (l.rstrip('\n').split(' ', 2) + [''])[:3]
        d[int(i)] = (int(ln), t)
    return d


def wordsize(b):
    """True when the instruction bytes b are a word-sized operation without a register operand naming the size"""
    if b[0] in (0x0a, 0x0b):
        return True
    if 0x90 <= b[0] <= 0x9f or 0xd0 <= b[0] <= 0xd5:
        return True
    return False


def classify(gl, gt, ul, ut, b=b''):
    if gt == 'BAD' or gl == 0:
        return 'both undefined' if ul == 0 else 'module undefined, unidasm decodes'
    if ul == 0:
        return 'unidasm undefined, module decodes'
    gk, uk = key(gt), key(ut, True)
    if gl == ul and gk == uk:
        return 'exact'
    if gl == ul and gk[0] == uk[0] and gk[0] in ('mul', 'muls', 'div', 'divs', 'mula') and uk[1]:
        # unidasm names the byte register r of MUL rr,# (and the word r of MULA) where the module names rr
        x = uk[1][0]
        if gk[1][0] in (B2W.get(x), W2L.get(x)) and gk[1][1:] == uk[1][1:]:
            return 'exact'
    if gl != ul:
        return 'length differs'
    if gk[0] != uk[0] and gk[0] in (uk[0] + 'w', uk[0][:-1]) and gk[1] == uk[1] and wordsize(b):
        return 'exact'        # unidasm adds or drops the W of word operations
    if gk[0] != uk[0] and b and (0xb0 <= b[0] <= 0xbf or 0xf0 <= b[0] <= 0xf5) and gk[0] == uk[0] + 'w' and gk[1] == uk[1]:
        return 'exact'
    if gk[0] != uk[0]:
        return 'mnemonic differs'
    return 'operands differ'


def main():
    g, u = load(sys.argv[1]), load(sys.argv[2])
    data = open(sys.argv[3], 'rb').read()
    show = int(sys.argv[sys.argv.index('--show') + 1]) if '--show' in sys.argv else 1
    b = collections.Counter()
    ex = collections.defaultdict(list)
    for i in sorted(g):
        gl, gt = g[i]
        ul, ut = u[i]
        c = classify(gl, gt, ul, ut, data[S * i:S * i + S])
        b[c] += 1
        if c not in ('exact', 'both undefined'):
            ex[c].append((i, data[S * i:S * i + S].hex(), gt, gl, ut, ul))
    for c, k in b.most_common():
        print(f'   {k:7d} {c}')
    print(f'   {len(g)} slots')
    if '--detail' in sys.argv:
        for c in ex:
            seen = collections.Counter()
            print('==', c)
            for i, h, gt, gl, ut, ul in ex[c]:
                kk = (key(gt)[0], key(ut)[0], h[:2] if c != 'mnemonic differs' else '')
                seen[kk] += 1
                if seen[kk] <= show:
                    print(f'   {h}  module: {gt} ({gl})   unidasm: {ut} ({ul})')
            print('   classes:', len(seen))


if __name__ == '__main__':
    main()
