# TLCS900H in Ghidra-Rare

Toshiba TLCS-900/H, the CPU of the Neo Geo Pocket / Color (TMP95C061) and of the TMP95C063 family: maximum mode,
four 32-bit register banks, 16 MB linear address space. Language `TLCS900H:LE:32:default`, extension name
`TLCS900H`. The module is nevesnunes' (MIT); what Ghidra-Rare changed is listed in [CREDITS.md](CREDITS.md).

## Status

| Area | Result |
|---|---|
| Decode | 491,520 random and structured slots plus 271,291 enumerated slots (every addressing prefix form x every operation byte) against MAME `unidasm -arch tlcs900`. 355,187 + 179,514 agree exactly (after spelling normalisation), 171,860 are undefined in both, 1 + 80 are the INTNEST/"unknown" spelling, and the rest are classified by `test/check_explained.py` (classes below): **0 unexplained**. The asl round trip covers the 354,693 decoded slots that asl can express (skipped: 1 INTNEST and 494 MINC/MDEC whose modulus is not a power of two). 350,669 give identical bytes and 3,579 an equivalent encoding that asl prefers, which the module re-decodes to the same instruction. asl cannot parse the previous-bank names in 426 of them, and rejects LDF 4-7 in 19; **0 differ**. Constructors reached: **2037/2037**. |
| Semantics | Loads and stores in every addressing mode (including (r32+r8/r16) signed index, (-r)/(r+) steps), ADD/ADC/SUB/SBC/CP/NEG/INC/DEC flags, logic + parity, all rotates/shifts incl. count 0 = 16 and through-carry, MUL/MULS/DIV/DIVS (incl. /0), MULA, MINC/MDEC, BS1F/BS1B, DAA, RLD/RRD, bit operations, LDIR/CPIR/CPD, LINK/UNLK/RETD, CALR/RET/RETI/DJNZ/JR, LDF/INCF/DECF/POP SR bank switching and explicit bank-register access, EX F,F', PUSH F, LDX, LDC, LDAR: **63 hand-computed emulator cases pass**, broken expectation detected. |
| Real code | Stargunner (Tixul, MIT, cc900) and Pengu (underscore42, MIT), imported raw at 200000H with `NeoGeoPocketCartridge.java`: 4,851 / 4,365 instructions, 109 / 96 functions, **0 decompile failures**; listing vs unidasm at the same addresses **4,851/4,851 and 4,365/4,365 exact**. Bookmarks: Stargunner 1 bad-instruction (see Doesn't work), Pengu 0. |
| Builds | Ghidra 12.1.3, 12.1.4, 12.2 (`tools/build-module.sh --standard --name TLCS900H`); `tlcs900h.sla` 151,877 bytes. |

### Works
- Full TLCS-900/H instruction set per the manual's code maps, including LDX, LDAR, MINC/MDEC, MULA, LINK/UNLK,
  BS1F/BS1B, MIRR, PAA, LDC with the DMA registers and INTNEST, and the extended register forms (C7/D7/E7 + code) with
  every bank, previous-bank and index-register code.
- Register banks: XWA..XHL are the current bank; codes for banks 0-3 and the previous bank resolve against RFP at run
  time; LDF/INCF/DECF/POP SR/RETI store and load banks.
- Decompiler-friendly flags (separate registers), cc900 stack convention, unconditional cc=T branches.
- `ghidra_scripts/NeoGeoPocketCartridge.java` for Neo Geo Pocket cartridge images.

### Doesn't work
- Stargunner's jump table at 211390H: the switch index is bounded through a byte compare on a second path, and
  Ghidra's jump-table recovery reads past the 15 table entries. This produces one bad-instruction bookmark at
  2121A5H. It is a decompiler heuristic; the p-code of the bounds checks is correct (the emulator cases cover the
  flags involved).
- HALT is a pcodeop (CPU state). Interrupts, micro-DMA and the 900's NORMAL/MAX mode bits are not modelled: they are
  hardware state that the 900/H does not change by instruction, apart from MAX, which is set and has no effect.

### Unverified
- Flags that the manual marks undefined (X): H after 32-bit operations, S/V after BIT/TSET, H after CCF/ZCF. The
  module computes H as for 8/16-bit operations and leaves the others unchanged.
- DAA's H flag (the module follows the usual BCD rule; the manual only says "changes").
- The previous bank of bank 0 is taken as bank 3 (RFP-1 mod 4). The manual defines RFP-1 but not the wrap.
- INTNEST as control register 3CH: the 900 book has XNSP at 3CH and says the 900/H has INTNEST instead; unidasm shows
  "unknown" there.
- Division overflow results (V=1): the manual leaves the result undefined; the module stores the truncated quotient.
- No real hardware: all results come from the manual, unidasm, asl and the emulator.

## Reference-tool bugs and differences (all confirmed against the manual)
- unidasm decodes LDX (F7) as a 1-byte "ldx". The manual and asl give 6 bytes, F7 00 n 00 # 00.
- unidasm accepts register codes that the register maps leave undefined (40H-CFH, odd word codes, long codes not a
  multiple of 4) and prints them as rXX. It also accepts (-r)/(r+) increment code 11, undefined (r32) sub-modes
  (printed as "unknown" or "()"), the 13H (PC+d16) mode outside LDAR, RET cc after any destination prefix, LDI/LDIR
  with any register, CP r,#3 on 32-bit registers, byte MUL/DIV with an even R (printed "??"), MUL rr,# whose r is not
  the low half of rr, #3/#4 fields with high bits set, bit numbers 8-15 on byte registers, EI/LDF operands above 7, and
  undefined LDC control register codes (printed "unknown").
- Spelling differences that the comparison normalises: unidasm drops the W of word operations (ld/push/add... for
  ldw/pushw/addw...), prints displacements unsigned, prints MINCn/MDECn with the encoded # - n, shows 0 for counts
  that mean 8 or 16, names the byte r of MUL rr,# instead of rr, and writes the previous bank as XWA-1.
- asl (CPU 96C141, i.e. the 900 core) rejects LDF 4-7 in maximum mode, cannot parse previous-bank names (XWA') inside
  memory operands, and hangs on MINC/MDEC with a modulus that is not a power of two (`test/asl_roundtrip.py` skips
  those).

## How to test

```sh
export GHIDRA_INSTALL_DIR=/path/to/ghidra_12.1.4_PUBLIC PROJ_DIR=/path/without/dot/dirs
ASL=/path/to/asl test/run-tests.sh /tmp/tlcs-work [--real]
```

`test/run-tests.sh` checks that the generator reproduces the sinc, compiles the spec, runs both unidasm decode
differentials with `check_explained.py`, the reach check, the asl round trip and the emulator cases. With `--real` it
fetches the two MIT games (`test/fetch-real.sh`, pinned SHA-256) and runs the real-code checks. It needs MAME's
`unidasm` and asl on PATH (or `UNIDASM`/`ASL`). `test/emu_assemble.py` regenerates `emu_cases.py` from
`emu_cases.src` with asl. `tools/gen/build.sh` regenerates `data/languages/tlcs900h.sinc`.
