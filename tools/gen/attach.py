# emits the 8-bit register-code attach tables (manual: register map "r", maximum mode)
cur8 = 'A W QA QW C B QC QB E D QE QD L H QL QH'.split()
idx8 = 'IXL IXH QIXL QIXH IYL IYH QIYL QIYH IZL IZH QIZL QIZH SPL SPH QSPL QSPH'.split()
cur16 = 'WA QWA BC QBC DE QDE HL QHL'.split()
idx16 = 'IX QIX IY QIY IZ QIZ SP QSP'.split()
cur32 = 'XWA XBC XDE XHL'.split()
idx32 = 'XIX XIY XIZ XSP'.split()
def bank8(n, s):
    return [('R' + x if not x.startswith('Q') else x) + s for x in cur8]
def bank16(n, s):
    return [('R' + x if not x.startswith('Q') else x) + s for x in cur16]
def tab(cur, idx, bank):
    out = []
    for b in range(16):
        if b < 4: out += bank(b, '_%d' % b)
        elif b == 0xd: out += bank(b, '_P')
        elif b == 0xe: out += cur
        elif b == 0xf: out += idx
        else: out += ['_'] * len(cur)
    return out
def emit(name, lst, per):
    s = 'attach variables [ %s ] [\n' % name
    for i in range(0, len(lst), per):
        s += '    ' + ' '.join('%-7s' % x for x in lst[i:i + per]) + '\n'
    return s + '];\n'
print(emit('xb8', tab(cur8, idx8, bank8), 16))
print(emit('xw7', tab(cur16, idx16, bank16), 8))
print(emit('xl6', tab(cur32, idx32, lambda b, s: [x + s for x in cur32]), 4))
