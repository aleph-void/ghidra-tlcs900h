#!/usr/bin/env python3
"""check_explained.py <ghidra.txt> <unidasm.txt> <corpus.bin> [--list]: every slot where the module and unidasm differ
must fall in a class explained from the TLCS-900 manual (instruction lists, code maps, register maps) or a confirmed
unidasm bug. Exit status 1 if any difference is unexplained."""
import collections
import os
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare as C  # noqa: E402

S = 8


def bad_byte_code(c):
    return 0x40 <= c <= 0xcf


def regcode_bad(c, size):
    """register code c (extension byte) undefined for an operand of `size` bytes (manual: register map, max mode)"""
    return bad_byte_code(c) or (size == 2 and c & 1) or (size == 4 and c & 3)


def mem_ext_reason(b):
    """b[0] is a C3/D3/E3/F3-style (mem) prefix: reason the extension bytes are undefined, or None"""
    lo = b[0] & 0x0f
    if lo in (4, 5):
        if b[1] & 3 == 3:
            return '(-r)/(r+) increment code 11 (manual: not defined)'
        if bad_byte_code(b[1] & 0xfc):
            return 'register code 40H-CFH (manual: not assigned in maximum mode)'
    if lo == 3:
        x = b[1]
        if x & 3 == 0 or x & 3 == 1:
            if bad_byte_code(x & 0xfc):
                return 'register code 40H-CFH (manual: not assigned in maximum mode)'
            return None
        if x == 0x13 and b[0] == 0xf3 and (b[4] & 0xf8) in (0x20, 0x30):
            return None
        if x == 0x13:
            return 'mode code 13H outside LDAR (unidasm decodes it as PC+d16 for any instruction; the manual has it only in LDAR)'
        if x not in (0x03, 0x07):
            return 'undefined (r32) sub-mode code (manual: 000000 11 = r32+r8, 000001 11 = r32+r16 only)'
        if regcode_bad(b[2], 4):
            return 'base register code not a 32-bit register (manual: multiple of 4)'
        if regcode_bad(b[3], 1 if x == 0x03 else 2):
            return 'index register code undefined (manual: register map)'
    return None


def ext_len(b):
    lo = b[0] & 0x0f
    if b[0] < 0xc0:
        return 1 + ((b[0] >> 3) & 1)
    if lo == 0: return 2
    if lo == 1: return 3
    if lo == 2: return 4
    if lo == 3:
        x = b[1]
        return 2 if x & 3 == 0 else 4
    return 2


def reason(b):
    p = b[0]
    if p in (0x06, 0x17) and b[1] > 7:
        return 'EI/LDF operand above 7 (manual: #3, a 3-bit field)'
    if p in (0xc7, 0xd7, 0xe7):
        size = {0xc7: 1, 0xd7: 2, 0xe7: 4}[p]
        if regcode_bad(b[1], size):
            return 'register code undefined for the operand size (manual: register map; word codes even, long codes multiple of 4)'
        op, rest = b[2], b[3:]
    elif p >= 0xc8 and (p & 0x0f) >= 8:
        op, rest = b[1], b[2:]
        size = {0xc: 1, 0xd: 2, 0xe: 4}.get(p >> 4)
    elif p >= 0x80 and not (p >= 0xc0 and (p & 0x0f) in (6, 7)) and p < 0xf6:
        r = mem_ext_reason(b) if p >= 0xc0 else None
        if r:
            return r
        n = ext_len(b)
        op, rest = b[n], b[n + 1:]
        if (p & 0x30) == 0x30:
            if op & 0xf0 == 0xf0:
                return 'RET cc with a memory prefix other than B0H (manual code map: "1st byte code is B0H")'
        else:
            if 0x10 <= op <= 0x13 and p not in (0x83, 0x85, 0x93, 0x95):
                return 'LDI/LDIR/LDD/LDDR with registers other than (XDE,XHL)/(XIX,XIY) (manual: 83+zz, 85+zz only)'
            if (op & 0xf0) in (0x40, 0x50) and (p & 0x30) == 0 and not op & 1:
                return 'byte MUL/DIV with an even R code (no 16-bit RR; unidasm prints ??)'
        return None
    else:
        return None
    if size and 0x20 <= op <= 0x24 or 0x30 <= op <= 0x34 or 0xe8 <= op <= 0xef:
        if rest and rest[0] & 0xf0:
            return '#4 operand with the upper four bits set (manual: 4-bit field)'
    if size == 1 and (0x20 <= op <= 0x24 or 0x30 <= op <= 0x34) and rest and 8 <= rest[0] <= 15:
        return 'bit number 8-15 on a byte register (asl rejects it)'
    if op in (0x2e, 0x2f) and rest:
        ok = {1: (0x22, 0x26, 0x2a, 0x2e), 2: (0x20, 0x24, 0x28, 0x2c, 0x3c), 4: tuple(range(0, 0x20, 4))}[size]
        if rest[0] not in ok:
            return 'LDC with a control register code undefined for the operand size (manual: control register map; unidasm prints "unknown")'
    if size == 4 and 0xd8 <= op <= 0xdf:
        return 'CP r,#3 with a 32-bit register (manual: byte and word only)'
    if size == 2 and (0x08 <= op <= 0x0b or op == 0x19) and p == 0xd7 and b[1] & 3:
        return 'word MUL/DIV rr,# or MULA whose r is not the low word of a 32-bit register'
    if size == 1 and 0x08 <= op <= 0x0b:
        if (p == 0xc7 and b[1] & 1) or (p != 0xc7 and not p & 1):
            return 'byte MUL/DIV rr,# whose r is not the low byte of a word register (asl rejects it; unidasm prints the byte register)'
    if size == 1 and (op & 0xf0) in (0x40, 0x50) and not op & 1:
        return 'byte MUL/DIV with an even R code (no 16-bit RR; unidasm prints ??)'
    return None


def main():
    g, u = C.load(sys.argv[1]), C.load(sys.argv[2])
    data = open(sys.argv[3], 'rb').read()
    cls = collections.Counter()
    ex = {}
    for i in sorted(g):
        gl, gt = g[i]
        ul, ut = u[i]
        b = data[S * i:S * i + S]
        c = C.classify(gl, gt, ul, ut, b)
        if c in ('exact', 'both undefined'):
            continue
        r = None
        if c == 'module undefined, unidasm decodes':
            r = reason(b)
            if r is None and b[0] == 0xf7:
                r = 'LDX: unidasm prints "ldx" with length 1 (confirmed unidasm bug: the manual and asl encode F7 00 n 00 # 00, 6 bytes)'
        elif c == 'length differs' and b[0] == 0xf7:
            r = 'LDX: unidasm prints "ldx" with length 1 (confirmed unidasm bug)'
        elif c == 'operands differ' and 'intnest' in gt.lower() and 'unknown' in ut:
            r = 'control register 3CH: INTNEST on the 900/H; unidasm prints "unknown"'
        key = r or ('UNEXPLAINED %s: %s' % (c, b.hex()))
        cls[r or 'UNEXPLAINED'] += 1
        if (r or 'UNEXPLAINED') not in ex or not r:
            ex.setdefault(r or 'UNEXPLAINED', []).append((b.hex(), gt, ut))
    bad = cls.get('UNEXPLAINED', 0)
    for k, n in cls.most_common():
        print(f'   {n:7d} {k}')
    if bad:
        for h, gt, ut in ex['UNEXPLAINED'][:40]:
            print(f'      {h}  module: {gt}  unidasm: {ut}')
    print(f'   unexplained differences: {bad}')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
