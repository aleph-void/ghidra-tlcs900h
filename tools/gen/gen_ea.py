import sys
# writes the memory-operand subtables. Every addressing form is its own one-constructor subtable
# (smB_Rd8 = byte source (R+d8), dmA_n = destination (#8), ...): SLEIGH cannot constrain the
# operation byte behind a variable-length operand, and a subtable with several constructors of
# different shapes does not pass its first-byte pattern up to the instruction, so the instruction
# constructors are repeated for each form (see gen_ins.py).
lines = []
def L(s):
    lines.append(s)
L('d8d: "+"^xs is xs & x_7=0 { export *[const]:4 xs; }')
L('d8d: "-"^nd is xs & x_7=1 [ nd = -xs; ] { export *[const]:4 xs; }')
L('d16d: "+"^v  is xa ; xbs & x_7=0 [ v = (xbs << 8) | xa; ] { export *[const]:4 v; }')
L('d16d: "-"^nd is xa ; xbs & x_7=1 [ nd = -((xbs << 8) | xa); ] { local v:4 = -nd; export v; }')
L('i16e: v is xa ; xb [ v = (xb << 8) | xa; ] { export *[const]:4 v; }')
L('i24e: v is xa ; xb ; xc [ v = (xc << 16) | (xb << 8) | xa; ] { export *[const]:4 v; }')
L('')
FORMS = [  # name, display, pattern after "op_7=1 & op_sz=S & ", p-code computing `a` (address)
    ('R',    'R32',                       'op_6=0 & op_3=0 & R32',                                   'local a:4 = R32;'),
    ('Rd8',  'R32^d8d',                   'op_6=0 & op_3=1 & R32 ; d8d',                             'local a:4 = R32 + d8d;'),
    ('n',    'xa',                        'op_6=1 & op_lo=0 ; xa',                                   'local a:4 = xa;'),
    ('nn',   'i16e',                      'op_6=1 & op_lo=1 ; i16e',                                 'local a:4 = i16e;'),
    ('nnn',  'i24e',                      'op_6=1 & op_lo=2 ; i24e',                                 'local a:4 = i24e;'),
    ('r',    'xrLm',                      'op_6=1 & op_lo=3 ; x_01=0 & xrLm',                        'local a:4 = xrLm;'),
    ('rd16', 'xrLm^d16d',                 'op_6=1 & op_lo=3 ; x_01=1 & xrLm ; d16d',                 'local a:4 = xrLm + d16d;'),
    ('rr8',  'xrL^"+"^xrB',               'op_6=1 & op_lo=3 ; x=0x03 ; xrL ; xrB',                   'local a:4 = xrL + sext(xrB);'),
    ('rr16', 'xrL^"+"^xrW',               'op_6=1 & op_lo=3 ; x=0x07 ; xrL ; xrW',                   'local a:4 = xrL + sext(xrW);'),
    ('dec',  '"-"^xrLm^":"^stp',          'op_6=1 & op_lo=4 ; x_01<3 & x_01 & xrLm [ stp = 1 << x_01; ]', 'xrLm = xrLm - stp; local a:4 = xrLm;'),
    ('inc',  'xrLm^"+:"^stp',             'op_6=1 & op_lo=5 ; x_01<3 & x_01 & xrLm [ stp = 1 << x_01; ]', 'local a:4 = xrLm; xrLm = xrLm + stp;'),
]
for sz, tag, n in ((0, 'smB', 1), (1, 'smW', 2), (2, 'smL', 4), (3, 'dmA', 0)):
    for name, disp, pat, code in FORMS:
        if n:
            L(f'{tag}_{name}: "("^{disp}^")" is op_7=1 & op_sz={sz} & {pat} {{ {code} export *:{n} a; }}')
        else:
            L(f'{tag}_{name}: {disp} is op_7=1 & op_sz={sz} & {pat} {{ {code} export a; }}')
    L('')
open(sys.argv[1] + '/ea.sinc', 'w').write('\n'.join(lines) + '\n')
open(sys.argv[1] + '/forms.txt', 'w').write(' '.join(f[0] for f in FORMS))
