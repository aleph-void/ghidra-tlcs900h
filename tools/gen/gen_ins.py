import sys
# writes the instruction constructors of the TLCS-900/H module (see the manual's Appendix B/C)
S = {
    'B': dict(r='rB', sm='smB', R='R8',  n=1, w=8,  imm='imm8',  zz=0, sfx=''),
    'W': dict(r='rW', sm='smW', R='R16', n=2, w=16, imm='imm16', zz=1, sfx='w'),
    'L': dict(r='rL', sm='smL', R='R32', n=4, w=32, imm='imm32', zz=2, sfx='l'),
}
o = []
def c(line):
    o.append(line)

c('\n# ---------------------------------------------------------------- 1-byte op codes')
c(':nop        is op=0x00 { }')
c('# NORMAL and MAX exist on the TLCS-900 core; the 900/H always runs in system and maximum mode')
c(':normal     is op=0x01 { $(SYSM) = 0; }')
c(':push SR    is op=0x02 & SR { push16(SR); }')
c(':pop SR     is op=0x03 & SR { local old:1 = $(RFP); pop16(SR); switch_bank(old); }')
c(':max        is op=0x04 { $(MAX) = 1; }')
c(':halt       is op=0x05 { halt(); }')
c(':ei imm3d   is op=0x06 ; d8_37=0 & imm3d { $(IFF) = imm3d; }')
c(':reti       is op=0x07 { local old:1 = $(RFP); pop16(SR); switch_bank(old); local t:4 = 0; pop32(t); INTNEST = INTNEST - 1; return [t]; }')
c(':ld (n8a),imm8    is op=0x08 ; n8a ; imm8  { *:1 n8a = imm8; }')
c(':push imm8        is op=0x09 ; imm8  { local v:1 = imm8; push8(v); }')
c(':ldw (n8a),imm16  is op=0x0a ; n8a ; imm16 { *:2 n8a = imm16; }')
c(':pushw imm16      is op=0x0b ; imm16 { local v:2 = imm16; push16(v); }')
c(':incf       is op=0x0c { local old:1 = $(RFP); $(RFP) = $(RFP) + 1; switch_bank(old); }')
c(':decf       is op=0x0d { local old:1 = $(RFP); $(RFP) = $(RFP) - 1; switch_bank(old); }')
c(':ret        is op=0x0e { local t:4 = 0; pop32(t); return [t]; }')
c(':retd simm16 is op=0x0f ; simm16 { local t:4 = 0; pop32(t); XSP = XSP + simm16; return [t]; }')
c(':rcf        is op=0x10 { $(H_flag) = 0; $(N_flag) = 0; $(C_flag) = 0; }')
c(':scf        is op=0x11 { $(H_flag) = 0; $(N_flag) = 0; $(C_flag) = 1; }')
c('# CCF/ZCF leave H undefined (manual: X); it is left unchanged here')
c(':ccf        is op=0x12 { $(N_flag) = 0; $(C_flag) = !$(C_flag); }')
c(':zcf        is op=0x13 { $(N_flag) = 0; $(C_flag) = !$(Z_flag); }')
c(':push A     is op=0x14 & A { push8(A); }')
c(':pop A      is op=0x15 & A { pop8(A); }')
c(':ex F,"F\'" is op=0x16 & F { local t:1 = F; F = F_I; F_I = t; }')
c(':ldf imm3d  is op=0x17 ; d8_37=0 & imm3d { local old:1 = $(RFP); $(RFP) = imm3d; switch_bank(old); }')
c(':push F     is op=0x18 & F { push8(F); }')
c(':pop F      is op=0x19 & F { pop8(F); }')
c('a16: imm16 is imm16 { export *:4 imm16; }')
c('a24: imm24 is imm24 { export *:4 imm24; }')
c(':jp a16     is op=0x1a ; a16 { goto a16; }')
c(':jp a24     is op=0x1b ; a24 { goto a24; }')
c(':call a16   is op=0x1c ; a16 { push32(&:4 inst_next); call a16; }')
c(':call a24   is op=0x1d ; a24 { push32(&:4 inst_next); call a24; }')
c(':calr rel16 is op=0x1e ; rel16 { push32(&:4 inst_next); call rel16; }')
c(':ld R8,imm8    is op_hi=0x2 & op_3=0 & R8  ; imm8  { R8 = imm8; }')
c(':push R16      is op_hi=0x2 & op_3=1 & R16 { push16(R16); }')
c(':ld R16,imm16  is op_hi=0x3 & op_3=0 & R16 ; imm16 { R16 = imm16; }')
c(':push R32      is op_hi=0x3 & op_3=1 & R32 { push32(R32); }')
c(':ld R32,imm32  is op_hi=0x4 & op_3=0 & R32 ; imm32 { R32 = imm32; }')
c(':pop R16       is op_hi=0x4 & op_3=1 & R16 { pop16(R16); }')
c(':pop R32       is op_hi=0x5 & op_3=1 & R32 { pop32(R32); }')
c(':jr cc,rel8    is op_hi=0x6 & cc ; rel8  { if (cc) goto rel8; }')
c(':jrl cc,rel16  is op_hi=0x7 & cc ; rel16 { if (cc) goto rel16; }')
c('z0a: is x=0 { }\nz0b: is x=0 { }\nz0c: is x=0 { }')
c(':ldx (n8a),imm8 is op=0xf7 ; z0a ; n8a ; z0b ; imm8 ; z0c { *:1 n8a = imm8; }')
c(':swi imm3      is op_hi=0xf & op_3=1 & imm3 {')
c('    push32(&:4 inst_next); push16(SR);')
c('    local va:4 = 0xffff00 + imm3 * 4; local h:4 = *:4 va;')
c('    call [h];')
c('}')

c('\n# ---------------------------------------------------------------- first byte: reg (C8+zz+r, C7+zz r)')
for z, d in S.items():
    r, R, w, imm = d['r'], d['R'], d['w'], d['imm']
    c(f'# {z}')
    c(f':ld {r},{imm}   is (op_7=1 & {r}) ... ; op=0x03 ; {imm} {{ {r} = {imm}; }}')
    c(f':push {r}       is (op_7=1 & {r}) ... ; op=0x04 {{ push{w}({r}); }}')
    c(f':pop {r}        is (op_7=1 & {r}) ... ; op=0x05 {{ pop{w}({r}); }}')
    if z != 'L':
        c(f':cpl {r}    is (op_7=1 & {r}) ... ; op=0x06 {{ {r} = ~{r}; $(H_flag) = 1; $(N_flag) = 1; }}')
        c(f':neg {r}    is (op_7=1 & {r}) ... ; op=0x07 {{ local z = {r}; z = 0; subf(z, {r}, 0, {r}); }}')
        c(f':djnz {r},rel8 is (op_7=1 & {r}) ... ; op=0x1c ; rel8 {{ {r} = {r} - 1; if ({r} != 0) goto rel8; }}')
        for k, (mn, mac) in enumerate([('andcf', 'C & b'), ('orcf', 'C | b'), ('xorcf', 'C ^ b'), ('ldcf', 'b')]):
            expr = mac.replace('C', '$(C_flag)')
            c(f':{mn} b4,{r}  is (op_7=1 & {r}) ... ; op=0x{0x20 + k:02x} ; b4 {{ local b:1 = (({r} >> b4) & 1) != 0; $(C_flag) = {expr}; }}')
            c(f':{mn} A,{r}   is (op_7=1 & {r}) ... ; op=0x{0x28 + k:02x} & A {{ local n:1 = A & 0xf; local b:1 = (({r} >> n) & 1) != 0; $(C_flag) = {expr}; }}')
        c(f':stcf b4,{r}  is (op_7=1 & {r}) ... ; op=0x24 ; b4 {{ local m = {r}; m = 1 << b4; {r} = ({r} & ~m) | (m * zext($(C_flag))); }}')
        c(f':stcf A,{r}   is (op_7=1 & {r}) ... ; op=0x2c & A {{ local n:1 = A & 0xf; local m = {r}; m = 1 << n; {r} = ({r} & ~m) | (m * zext($(C_flag))); }}')
        c(f':res b4,{r}   is (op_7=1 & {r}) ... ; op=0x30 ; b4 {{ local m = {r}; m = 1 << b4; {r} = {r} & ~m; }}')
        c(f':set b4,{r}   is (op_7=1 & {r}) ... ; op=0x31 ; b4 {{ local m = {r}; m = 1 << b4; {r} = {r} | m; }}')
        c(f':chg b4,{r}   is (op_7=1 & {r}) ... ; op=0x32 ; b4 {{ local m = {r}; m = 1 << b4; {r} = {r} ^ m; }}')
        c(f'# BIT/TSET: S and V undefined (manual: X), left unchanged')
        c(f':bit b4,{r}   is (op_7=1 & {r}) ... ; op=0x33 ; b4 {{ $(Z_flag) = (({r} >> b4) & 1) == 0; $(H_flag) = 1; $(N_flag) = 0; }}')
        c(f':tset b4,{r}  is (op_7=1 & {r}) ... ; op=0x34 ; b4 {{ $(Z_flag) = (({r} >> b4) & 1) == 0; $(H_flag) = 1; $(N_flag) = 0; local m = {r}; m = 1 << b4; {r} = {r} | m; }}')
        c(f':scc cc,{r}   is (op_7=1 & {r}) ... ; op_hi=0x7 & cc {{ {r} = zext(cc); }}')
        c(f':ex {R},{r}   is (op_7=1 & {r}) ... ; op_hi=0xb & op_3=1 & {R} {{ local t = {r}; {r} = {R}; {R} = t; }}')
        c(f':cp {r},imm3  is (op_7=1 & {r}) ... ; op_hi=0xd & op_3=1 & imm3 {{ local t = {r}; local k = {r}; k = imm3; subf({r}, k, 0, t); }}')
    if z == 'B':
        c(':daa rB      is (op_7=1 & rB) ... ; op=0x10 {')
        c('    local a:1 = rB; local d:1 = 0; local cy:1 = $(C_flag);')
        c('    if (($(H_flag) == 0) && ((a & 0xf) <= 9)) goto <lo>;')
        c('    d = 0x06;')
        c('<lo>')
        c('    if (($(C_flag) == 0) && (a <= 0x99)) goto <hi>;')
        c('    d = d | 0x60; cy = 1;')
        c('<hi>')
        c('    local r:1 = a + d;')
        c('    if ($(N_flag) == 0) goto <add>;')
        c('    r = a - d;')
        c('<add>')
        c('    $(H_flag) = ((a ^ r) & 0x10) != 0;')
        c('    $(C_flag) = cy; resSZ(r); parityV(r); rB = r;')
        c('}')
        c(':mul mrB,imm8  is (op_7=1 & mrB) ... ; op=0x08 ; imm8 { local s:1 = imm8; mulu8(mrB, s); }')
        c(':muls mrB,imm8 is (op_7=1 & mrB) ... ; op=0x09 ; imm8 { local s:1 = imm8; muls8(mrB, s); }')
        c(':div mrB,imm8  is (op_7=1 & mrB) ... ; op=0x0a ; imm8 { local s:1 = imm8; divu8(mrB, s); }')
        c(':divs mrB,imm8 is (op_7=1 & mrB) ... ; op=0x0b ; imm8 { local s:1 = imm8; divs8(mrB, s); }')
        c(':mul RRb,rB  is (op_7=1 & rB) ... ; op_hi=0x4 & op_3=0 & op_0=1 & RRb { mulu8(RRb, rB); }')
        c(':muls RRb,rB is (op_7=1 & rB) ... ; op_hi=0x4 & op_3=1 & op_0=1 & RRb { muls8(RRb, rB); }')
        c(':div RRb,rB  is (op_7=1 & rB) ... ; op_hi=0x5 & op_3=0 & op_0=1 & RRb { divu8(RRb, rB); }')
        c(':divs RRb,rB is (op_7=1 & rB) ... ; op_hi=0x5 & op_3=1 & op_0=1 & RRb { divs8(RRb, rB); }')
        c(':ldc crB,rB  is (op_7=1 & rB) ... ; op=0x2e ; crB { crB = rB; }')
        c(':ldc rB,crB  is (op_7=1 & rB) ... ; op=0x2f ; crB { rB = crB; }')
        c(':inc n3,rB   is (op_7=1 & rB) ... ; op_hi=0x6 & op_3=0 & n3 { local k:1 = n3; incf(rB, k); }')
        c(':dec n3,rB   is (op_7=1 & rB) ... ; op_hi=0x6 & op_3=1 & n3 { local k:1 = n3; decf(rB, k); }')
    if z == 'W':
        c(':mul mrW,imm16  is (op_7=1 & mrW) ... ; op=0x08 ; imm16 { local s:2 = imm16; mulu16(mrW, s); }')
        c(':muls mrW,imm16 is (op_7=1 & mrW) ... ; op=0x09 ; imm16 { local s:2 = imm16; muls16(mrW, s); }')
        c(':div mrW,imm16  is (op_7=1 & mrW) ... ; op=0x0a ; imm16 { local s:2 = imm16; divu16(mrW, s); }')
        c(':divs mrW,imm16 is (op_7=1 & mrW) ... ; op=0x0b ; imm16 { local s:2 = imm16; divs16(mrW, s); }')
        c(':mul R32,rW  is (op_7=1 & rW) ... ; op_hi=0x4 & op_3=0 & R32 { mulu16(R32, rW); }')
        c(':muls R32,rW is (op_7=1 & rW) ... ; op_hi=0x4 & op_3=1 & R32 { muls16(R32, rW); }')
        c(':div R32,rW  is (op_7=1 & rW) ... ; op_hi=0x5 & op_3=0 & R32 { divu16(R32, rW); }')
        c(':divs R32,rW is (op_7=1 & rW) ... ; op_hi=0x5 & op_3=1 & R32 { divs16(R32, rW); }')
        c(':bs1f A,rW   is (op_7=1 & rW) ... ; op=0x0e & A {')
        c('    local v:2 = rW; $(V_flag) = v == 0; if (v == 0) goto <done>;')
        c('    local i:1 = 0;')
        c('<loop>')
        c('    if (((v >> i) & 1) != 0) goto <found>;')
        c('    i = i + 1; goto <loop>;')
        c('<found>')
        c('    A = i;')
        c('<done>')
        c('}')
        c(':bs1b A,rW   is (op_7=1 & rW) ... ; op=0x0f & A {')
        c('    local v:2 = rW; $(V_flag) = v == 0; if (v == 0) goto <done>;')
        c('    local i:1 = 15;')
        c('<loop>')
        c('    if (((v >> i) & 1) != 0) goto <found>;')
        c('    i = i - 1; goto <loop>;')
        c('<found>')
        c('    A = i;')
        c('<done>')
        c('}')
        c(':mirr rW     is (op_7=1 & rW) ... ; op=0x16 {')
        c('    local v:2 = rW; local r:2 = 0; local i:1 = 0;')
        c('<loop>')
        c('    r = (r << 1) | ((v >> i) & 1); i = i + 1;')
        c('    if (i < 16) goto <loop>;')
        c('    rW = r;')
        c('}')
        c('# MULA rr: rr <- rr + (XDE) x (XHL) (signed 16 x 16), XHL <- XHL - 2; S Z V')
        c(':mula mrW    is (op_7=1 & mrW) ... ; op=0x19 {')
        c('    local p:4 = sext(*:2 XDE) * sext(*:2 XHL);')
        c('    local a:4 = mrW; local r:4 = a + p;')
        c('    $(V_flag) = ((a ^ r) & (p ^ r)) s< 0; resSZ(r);')
        c('    mrW = r; XHL = XHL - 2;')
        c('}')
        # MINCn/MDECn #,r: the operand is encoded as # - n (manual: D8+r :38:#-1, :39:#-2, :3A:#-4, ...)
        for k, step in ((0x38, 1), (0x39, 2), (0x3a, 4)):
            c(f':minc{step} modv,rW is (op_7=1 & rW) ... ; op=0x{k:02x} ; imm16 [ modv = imm16 + {step}; ] {{ local m:2 = imm16 + {step - 1}; if ((rW & m) == (m + 1 - {step})) goto <wrap>; rW = rW + {step}; goto inst_next; <wrap> rW = rW - (m + 1 - {step}); }}')
        for k, step in ((0x3c, 1), (0x3d, 2), (0x3e, 4)):
            c(f':mdec{step} modv,rW is (op_7=1 & rW) ... ; op=0x{k:02x} ; imm16 [ modv = imm16 + {step}; ] {{ local m:2 = imm16 + {step - 1}; if ((rW & m) == 0) goto <wrap>; rW = rW - {step}; goto inst_next; <wrap> rW = rW + (m + 1 - {step}); }}')
        c(':ldc crW,rW  is (op_7=1 & rW) ... ; op=0x2e ; crW { crW = rW; }')
        c(':ldc rW,crW  is (op_7=1 & rW) ... ; op=0x2f ; crW { rW = crW; }')
    if z == 'L':
        c(':link rL,simm16 is (op_7=1 & rL) ... ; op=0x0c ; simm16 { push32(rL); rL = XSP; XSP = XSP + simm16; }')
        c(':unlk rL     is (op_7=1 & rL) ... ; op=0x0d { XSP = rL; pop32(rL); }')
        c(':ldc crL,rL  is (op_7=1 & rL) ... ; op=0x2e ; crL { crL = rL; }')
        c(':ldc rL,crL  is (op_7=1 & rL) ... ; op=0x2f ; crL { rL = crL; }')
    if z in 'WL':
        h = {'W': 1, 'L': 2}[z]
        c(f':extz {r}   is (op_7=1 & {r}) ... ; op=0x12 {{ {r} = zext({r}:{h}); }}')
        c(f':exts {r}   is (op_7=1 & {r}) ... ; op=0x13 {{ {r} = sext({r}:{h}); }}')
        c(f':paa {r}    is (op_7=1 & {r}) ... ; op=0x14 {{ {r} = {r} + ({r} & 1); }}')
        c(f':inc n3,{r} is (op_7=1 & {r}) ... ; op_hi=0x6 & op_3=0 & n3 {{ {r} = {r} + zext(n3); }}')
        c(f':dec n3,{r} is (op_7=1 & {r}) ... ; op_hi=0x6 & op_3=1 & n3 {{ {r} = {r} - zext(n3); }}')
    # BWL register-register and immediate
    c(f':add {R},{r} is (op_7=1 & {r}) ... ; op_hi=0x8 & op_3=0 & {R} {{ addf({R}, {r}, 0, {R}); }}')
    c(f':ld {R},{r}  is (op_7=1 & {r}) ... ; op_hi=0x8 & op_3=1 & {R} {{ {R} = {r}; }}')
    c(f':adc {R},{r} is (op_7=1 & {r}) ... ; op_hi=0x9 & op_3=0 & {R} {{ addf({R}, {r}, 1, {R}); }}')
    c(f':ld {r},{R}  is (op_7=1 & {r}) ... ; op_hi=0x9 & op_3=1 & {R} {{ {r} = {R}; }}')
    c(f':sub {R},{r} is (op_7=1 & {r}) ... ; op_hi=0xa & op_3=0 & {R} {{ subf({R}, {r}, 0, {R}); }}')
    c(f':ld {r},imm3 is (op_7=1 & {r}) ... ; op_hi=0xa & op_3=1 & imm3 {{ {r} = imm3; }}')
    c(f':sbc {R},{r} is (op_7=1 & {r}) ... ; op_hi=0xb & op_3=0 & {R} {{ subf({R}, {r}, 1, {R}); }}')
    c(f':and {R},{r} is (op_7=1 & {r}) ... ; op_hi=0xc & op_3=0 & {R} {{ {R} = {R} & {r}; logf({R}, 1); }}')
    c(f':xor {R},{r} is (op_7=1 & {r}) ... ; op_hi=0xd & op_3=0 & {R} {{ {R} = {R} ^ {r}; logf({R}, 0); }}')
    c(f':or {R},{r}  is (op_7=1 & {r}) ... ; op_hi=0xe & op_3=0 & {R} {{ {R} = {R} | {r}; logf({R}, 0); }}')
    c(f':cp {R},{r}  is (op_7=1 & {r}) ... ; op_hi=0xf & op_3=0 & {R} {{ local t = {R}; subf({R}, {r}, 0, t); }}')
    c(f':add {r},{imm} is (op_7=1 & {r}) ... ; op=0xc8 ; {imm} {{ local k = {r}; k = {imm}; addf({r}, k, 0, {r}); }}')
    c(f':adc {r},{imm} is (op_7=1 & {r}) ... ; op=0xc9 ; {imm} {{ local k = {r}; k = {imm}; addf({r}, k, 1, {r}); }}')
    c(f':sub {r},{imm} is (op_7=1 & {r}) ... ; op=0xca ; {imm} {{ local k = {r}; k = {imm}; subf({r}, k, 0, {r}); }}')
    c(f':sbc {r},{imm} is (op_7=1 & {r}) ... ; op=0xcb ; {imm} {{ local k = {r}; k = {imm}; subf({r}, k, 1, {r}); }}')
    c(f':and {r},{imm} is (op_7=1 & {r}) ... ; op=0xcc ; {imm} {{ {r} = {r} & {imm}; logf({r}, 1); }}')
    c(f':xor {r},{imm} is (op_7=1 & {r}) ... ; op=0xcd ; {imm} {{ {r} = {r} ^ {imm}; logf({r}, 0); }}')
    c(f':or {r},{imm}  is (op_7=1 & {r}) ... ; op=0xce ; {imm} {{ {r} = {r} | {imm}; logf({r}, 0); }}')
    c(f':cp {r},{imm}  is (op_7=1 & {r}) ... ; op=0xcf ; {imm} {{ local k = {r}; k = {imm}; local t = {r}; subf({r}, k, 0, t); }}')
    for k, (mn, mac) in enumerate([('rlc', 'rlc_'), ('rrc', 'rrc_'), ('rl', 'rl_'), ('rr', 'rr_'), ('sla', 'sla_'), ('sra', 'sra_'), ('sll', 'sla_'), ('srl', 'srl_')]):
        args = f'{r}, n, {w}' if mac not in ('sra_', 'srl_') else f'{r}, n'
        c(f':{mn} n4,{r} is (op_7=1 & {r}) ... ; op=0x{0xe8 + k:02x} ; n4 {{ local n:1 = n4; {mac}({args}); }}')
        c(f':{mn} A,{r}  is (op_7=1 & {r}) ... ; op=0x{0xf8 + k:02x} & A {{ local n:1 = A & 0xf; n = n + 16 * (n == 0); {mac}({args}); }}')

c('\n# ---------------------------------------------------------------- first byte: src (mem)')
for z, d in S.items():
    sm, R, w, imm, sf = d['sm'], d['R'], d['w'], d['imm'], d['sfx']
    c(f'# {z}')
    c(f':ld {R},{sm}  is (op_7=1 & {sm}) ... ; op_hi=0x2 & op_3=0 & {R} {{ {R} = {sm}; }}')
    c(f':add {R},{sm} is (op_7=1 & {sm}) ... ; op_hi=0x8 & op_3=0 & {R} {{ addf({R}, {sm}, 0, {R}); }}')
    c(f':add {sm},{R} is (op_7=1 & {sm}) ... ; op_hi=0x8 & op_3=1 & {R} {{ addf({sm}, {R}, 0, {sm}); }}')
    c(f':adc {R},{sm} is (op_7=1 & {sm}) ... ; op_hi=0x9 & op_3=0 & {R} {{ addf({R}, {sm}, 1, {R}); }}')
    c(f':adc {sm},{R} is (op_7=1 & {sm}) ... ; op_hi=0x9 & op_3=1 & {R} {{ addf({sm}, {R}, 1, {sm}); }}')
    c(f':sub {R},{sm} is (op_7=1 & {sm}) ... ; op_hi=0xa & op_3=0 & {R} {{ subf({R}, {sm}, 0, {R}); }}')
    c(f':sub {sm},{R} is (op_7=1 & {sm}) ... ; op_hi=0xa & op_3=1 & {R} {{ subf({sm}, {R}, 0, {sm}); }}')
    c(f':sbc {R},{sm} is (op_7=1 & {sm}) ... ; op_hi=0xb & op_3=0 & {R} {{ subf({R}, {sm}, 1, {R}); }}')
    c(f':sbc {sm},{R} is (op_7=1 & {sm}) ... ; op_hi=0xb & op_3=1 & {R} {{ subf({sm}, {R}, 1, {sm}); }}')
    c(f':and {R},{sm} is (op_7=1 & {sm}) ... ; op_hi=0xc & op_3=0 & {R} {{ {R} = {R} & {sm}; logf({R}, 1); }}')
    c(f':and {sm},{R} is (op_7=1 & {sm}) ... ; op_hi=0xc & op_3=1 & {R} {{ local t = {sm} & {R}; {sm} = t; logf(t, 1); }}')
    c(f':xor {R},{sm} is (op_7=1 & {sm}) ... ; op_hi=0xd & op_3=0 & {R} {{ {R} = {R} ^ {sm}; logf({R}, 0); }}')
    c(f':xor {sm},{R} is (op_7=1 & {sm}) ... ; op_hi=0xd & op_3=1 & {R} {{ local t = {sm} ^ {R}; {sm} = t; logf(t, 0); }}')
    c(f':or {R},{sm}  is (op_7=1 & {sm}) ... ; op_hi=0xe & op_3=0 & {R} {{ {R} = {R} | {sm}; logf({R}, 0); }}')
    c(f':or {sm},{R}  is (op_7=1 & {sm}) ... ; op_hi=0xe & op_3=1 & {R} {{ local t = {sm} | {R}; {sm} = t; logf(t, 0); }}')
    c(f':cp {R},{sm}  is (op_7=1 & {sm}) ... ; op_hi=0xf & op_3=0 & {R} {{ local t = {R}; subf({R}, {sm}, 0, t); }}')
    c(f':cp {sm},{R}  is (op_7=1 & {sm}) ... ; op_hi=0xf & op_3=1 & {R} {{ local m = {sm}; local t = m; subf(m, {R}, 0, t); }}')
    if z == 'L':
        continue
    c(f':push{sf} {sm} is (op_7=1 & {sm}) ... ; op=0x04 {{ local v = {sm}; push{w}(v); }}')
    c(f':ld{sf} (n16a),{sm} is (op_7=1 & {sm}) ... ; op=0x19 ; n16a {{ *:{d["n"]} n16a = {sm}; }}')
    c(f':ex {sm},{R}  is (op_7=1 & {sm}) ... ; op_hi=0x3 & op_3=0 & {R} {{ local t = {sm}; {sm} = {R}; {R} = t; }}')
    for k, (mn, body) in enumerate([('add', 'addf(m, k, 0, {sm});'), ('adc', 'addf(m, k, 1, {sm});'), ('sub', 'subf(m, k, 0, {sm});'),
                                    ('sbc', 'subf(m, k, 1, {sm});'), ('and', 'local t = m & k; {sm} = t; logf(t, 1);'),
                                    ('xor', 'local t = m ^ k; {sm} = t; logf(t, 0);'), ('or', 'local t = m | k; {sm} = t; logf(t, 0);'),
                                    ('cp', 'local t = m; subf(m, k, 0, t);')]):
        c(f':{mn}{sf} {sm},{imm} is (op_7=1 & {sm}) ... ; op=0x{0x38 + k:02x} ; {imm} {{ local m = {sm}; local k = m; k = {imm}; ' + body.format(sm=sm) + ' }')
    c(f':inc{sf} n3,{sm} is (op_7=1 & {sm}) ... ; op_hi=0x6 & op_3=0 & n3 {{ local k:{d["n"]} = {"n3" if d["n"] == 1 else "zext(n3)"}; local m = {sm}; incf(m, k); {sm} = m; }}')
    c(f':dec{sf} n3,{sm} is (op_7=1 & {sm}) ... ; op_hi=0x6 & op_3=1 & n3 {{ local k:{d["n"]} = {"n3" if d["n"] == 1 else "zext(n3)"}; local m = {sm}; decf(m, k); {sm} = m; }}')
    for k, (mn, mac) in enumerate([('rlc', 'rlc_'), ('rrc', 'rrc_'), ('rl', 'rl_'), ('rr', 'rr_'), ('sla', 'sla_'), ('sra', 'sra_'), ('sll', 'sla_'), ('srl', 'srl_')]):
        args = f'm, n, {w}' if mac not in ('sra_', 'srl_') else 'm, n'
        c(f':{mn}{sf} {sm} is (op_7=1 & {sm}) ... ; op=0x{0x78 + k:02x} {{ local n:1 = 1; local m = {sm}; {mac}({args}); {sm} = m; }}')
    if z == 'B':
        c(':rld A,smB  is (op_7=1 & smB) ... ; op=0x06 & A { local m:1 = smB; local a:1 = A; A = (a & 0xf0) | (m >> 4); smB = (m << 4) | (a & 0x0f); resSZ(A); parityV(A); $(H_flag) = 0; $(N_flag) = 0; }')
        c(':rrd A,smB  is (op_7=1 & smB) ... ; op=0x07 & A { local m:1 = smB; local a:1 = A; A = (a & 0xf0) | (m & 0x0f); smB = (a << 4) | (m >> 4); resSZ(A); parityV(A); $(H_flag) = 0; $(N_flag) = 0; }')
        c(':mul RRb,smB  is (op_7=1 & smB) ... ; op_hi=0x4 & op_3=0 & op_0=1 & RRb { local s:1 = smB; mulu8(RRb, s); }')
        c(':muls RRb,smB is (op_7=1 & smB) ... ; op_hi=0x4 & op_3=1 & op_0=1 & RRb { local s:1 = smB; muls8(RRb, s); }')
        c(':div RRb,smB  is (op_7=1 & smB) ... ; op_hi=0x5 & op_3=0 & op_0=1 & RRb { local s:1 = smB; divu8(RRb, s); }')
        c(':divs RRb,smB is (op_7=1 & smB) ... ; op_hi=0x5 & op_3=1 & op_0=1 & RRb { local s:1 = smB; divs8(RRb, s); }')
    else:
        c(':mul R32,smW  is (op_7=1 & smW) ... ; op_hi=0x4 & op_3=0 & R32 { local s:2 = smW; mulu16(R32, s); }')
        c(':muls R32,smW is (op_7=1 & smW) ... ; op_hi=0x4 & op_3=1 & R32 { local s:2 = smW; muls16(R32, s); }')
        c(':div R32,smW  is (op_7=1 & smW) ... ; op_hi=0x5 & op_3=0 & R32 { local s:2 = smW; divu16(R32, s); }')
        c(':divs R32,smW is (op_7=1 & smW) ... ; op_hi=0x5 & op_3=1 & R32 { local s:2 = smW; divs16(R32, s); }')

c('\n# block transfer and search (prefix 80+zz+R / 83+zz, 85+zz)')
for z, (sf, n, acc) in {'B': ('', 1, 'A'), 'W': ('w', 2, 'WA')}.items():
    p = 0x80 if z == 'B' else 0x90
    for dreg, sreg, pr in (('XDE', 'XHL', p + 3), ('XIX', 'XIY', p + 5)):
        for k, (mn, sign, rep) in enumerate([('ldi', '+', 0), ('ldir', '+', 1), ('ldd', '-', 0), ('lddr', '-', 1)]):
            c(f':{mn}{sf} ({dreg}^"{sign}"),({sreg}^"{sign}") is op=0x{pr:02x} & {dreg} & {sreg} ; op=0x{0x10 + k:02x} {{')
            c(f'    *:{n} {dreg} = *:{n} {sreg}; {dreg} = {dreg} {sign} {n}; {sreg} = {sreg} {sign} {n}; BC = BC - 1;')
            c(f'    $(H_flag) = 0; $(N_flag) = 0; $(V_flag) = BC != 0;')
            if rep:
                c('    if (BC != 0) goto inst_start;')
            c('}')
    for k, (mn, sign, rep) in enumerate([('cpi', '+', 0), ('cpir', '+', 1), ('cpd', '-', 0), ('cpdr', '-', 1)]):
        c(f':{mn} {acc},(R32^"{sign}") is op_hi=0x{p >> 4:x} & op_3=0 & R32 ; op=0x{0x14 + k:02x} & {acc} {{')
        c(f'    local m:{n} = *:{n} R32; local t:{n} = 0; local cy:1 = $(C_flag); subf({acc}, m, 0, t); $(C_flag) = cy;')
        c(f'    R32 = R32 {sign} {n}; BC = BC - 1; $(V_flag) = BC != 0;')
        if rep:
            c('    if ((BC != 0) && ($(Z_flag) == 0)) goto inst_start;')
        c('}')

c('\n# ---------------------------------------------------------------- first byte: dst (mem)')
c(':ld (dmA),imm8     is (op_7=1 & dmA) ... ; op=0x00 ; imm8  { *:1 dmA = imm8; }')
c(':ldw (dmA),imm16   is (op_7=1 & dmA) ... ; op=0x02 ; imm16 { *:2 dmA = imm16; }')
c(':pop (dmA)         is (op_7=1 & dmA) ... ; op=0x04 { local v:1 = 0; pop8(v); *:1 dmA = v; }')
c(':popw (dmA)        is (op_7=1 & dmA) ... ; op=0x06 { local v:2 = 0; pop16(v); *:2 dmA = v; }')
c(':ld (dmA),(n16a)   is (op_7=1 & dmA) ... ; op=0x14 ; n16a { *:1 dmA = *:1 n16a; }')
c(':ldw (dmA),(n16a)  is (op_7=1 & dmA) ... ; op=0x16 ; n16a { *:2 dmA = *:2 n16a; }')
c(':lda R16,dmA       is (op_7=1 & dmA) ... ; op_hi=0x2 & op_3=0 & R16 { R16 = dmA:2; }')
c(':lda R32,dmA       is (op_7=1 & dmA) ... ; op_hi=0x3 & op_3=0 & R32 { R32 = dmA; }')
c(':ld (dmA),R8       is (op_7=1 & dmA) ... ; op_hi=0x4 & op_3=0 & R8  { *:1 dmA = R8; }')
c(':ld (dmA),R16      is (op_7=1 & dmA) ... ; op_hi=0x5 & op_3=0 & R16 { *:2 dmA = R16; }')
c(':ld (dmA),R32      is (op_7=1 & dmA) ... ; op_hi=0x6 & op_3=0 & R32 { *:4 dmA = R32; }')
for k, (mn, mac) in enumerate([('andcf', 'C & b'), ('orcf', 'C | b'), ('xorcf', 'C ^ b'), ('ldcf', 'b')]):
    expr = mac.replace('C', '$(C_flag)')
    c(f':{mn} A,(dmA)  is (op_7=1 & dmA) ... ; op=0x{0x28 + k:02x} & A {{ local n:1 = A & 0xf; local b:1 = ((*:1 dmA >> n) & 1) != 0; $(C_flag) = {expr}; }}')
    c(f':{mn} imm3,(dmA) is (op_7=1 & dmA) ... ; op_hi=0x{8 + k // 2:x} & op_3={k % 2} & imm3 {{ local b:1 = ((*:1 dmA >> imm3) & 1) != 0; $(C_flag) = {expr}; }}')
c(':stcf A,(dmA)    is (op_7=1 & dmA) ... ; op=0x2c & A { local n:1 = A & 0xf; local m:1 = 1 << n; *:1 dmA = (*:1 dmA & ~m) | (m * $(C_flag)); }')
c(':stcf imm3,(dmA) is (op_7=1 & dmA) ... ; op_hi=0xa & op_3=0 & imm3 { local m:1 = 1 << imm3; *:1 dmA = (*:1 dmA & ~m) | (m * $(C_flag)); }')
c(':tset imm3,(dmA) is (op_7=1 & dmA) ... ; op_hi=0xa & op_3=1 & imm3 { local v:1 = *:1 dmA; $(Z_flag) = ((v >> imm3) & 1) == 0; $(H_flag) = 1; $(N_flag) = 0; *:1 dmA = v | (1 << imm3); }')
c(':res imm3,(dmA)  is (op_7=1 & dmA) ... ; op_hi=0xb & op_3=0 & imm3 { *:1 dmA = *:1 dmA & ~(1 << imm3); }')
c(':set imm3,(dmA)  is (op_7=1 & dmA) ... ; op_hi=0xb & op_3=1 & imm3 { *:1 dmA = *:1 dmA | (1 << imm3); }')
c(':chg imm3,(dmA)  is (op_7=1 & dmA) ... ; op_hi=0xc & op_3=0 & imm3 { *:1 dmA = *:1 dmA ^ (1 << imm3); }')
c(':bit imm3,(dmA)  is (op_7=1 & dmA) ... ; op_hi=0xc & op_3=1 & imm3 { $(Z_flag) = ((*:1 dmA >> imm3) & 1) == 0; $(H_flag) = 1; $(N_flag) = 0; }')
c(':jp cc,(dmA)     is (op_7=1 & dmA) ... ; op_hi=0xd & cc { if (!cc) goto inst_next; goto [dmA]; }')
c(':call cc,(dmA)   is (op_7=1 & dmA) ... ; op_hi=0xe & cc { if (!cc) goto inst_next; push32(&:4 inst_next); call [dmA]; }')
c(':ret cc          is op=0xb0 ; op_hi=0xf & cc { if (!cc) goto inst_next; local t:4 = 0; pop32(t); return [t]; }')
c(':ldar R16,rel16a is op=0xf3 ; x=0x13 ; simm16 ; op_hi=0x2 & op_3=0 & R16 [ rel16a = inst_start + 4 + simm16; ] { R16 = rel16a; }')
c(':ldar R32,rel16a is op=0xf3 ; x=0x13 ; simm16 ; op_hi=0x3 & op_3=0 & R32 [ rel16a = inst_start + 4 + simm16; ] { R32 = rel16a; }')
import re
FORMS = open(sys.argv[1] + '/forms.txt').read().split()
VAR = {'rB': ['1', '2'], 'rW': ['1', '2'], 'rL': ['1', '2'], 'mrB': ['1', '2'], 'mrW': ['1', '2'],
       'smB': ['_' + f for f in FORMS], 'smW': ['_' + f for f in FORMS], 'smL': ['_' + f for f in FORMS], 'dmA': ['_' + f for f in FORMS]}
import re as _re
o = [_re.sub(r'\bb4\b', 'bn3', l) if _re.match(r':(andcf|orcf|xorcf|ldcf|stcf|res|set|chg|bit|tset) b4,rB\b', l) else l for l in o]
blocks = []
i = 0
lines = '\n'.join(o).split('\n')
while i < len(lines):
    if lines[i].startswith(':') and lines[i].rstrip().endswith('{'):
        j = i
        while lines[j] != '}':
            j += 1
        blocks.append('\n'.join(lines[i:j + 1]))
        i = j + 1
    else:
        blocks.append(lines[i])
        i += 1
out = []
for line in blocks:
    names = [n for n in VAR if re.search(r'\b%s\b' % n, line)]
    assert len(names) <= 1, line
    if not names:
        out.append(line)
        continue
    n = names[0]
    line = line.replace('(op_7=1 & %s) ... ;' % n, '%s ;' % n)
    for k in VAR[n]:
        out.append(re.sub(r'\b%s\b' % n, n + k, line))
o = out
open(sys.argv[1] + '/ins.sinc', 'w').write('\n'.join(o) + '\n')
print(len([l for l in o if l.startswith(':')]), 'constructors')
