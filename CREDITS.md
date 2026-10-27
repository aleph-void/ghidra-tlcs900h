# Credits and provenance: TLCS900H module

| | |
|---|---|
| Source | https://github.com/nevesnunes/ghidra-tlcs900h, HEAD `4679796` ("Closes #1", 2026-10-27; 45 commits, 2023-08-02 .. 2026-10-27) |
| License | MIT (`LICENSE`, added by the author on 2026-10-27 in answer to https://github.com/nevesnunes/ghidra-tlcs900h/issues/1) |
| Original author | nevesnunes (GitHub @nevesnunes; all 45 commits): SLEIGH module, register and bank model, macros, disassembly and ares-trace verification scripts (`scripts/`), README and figures |

Other implementations: `gh search repos` for "ghidra tlcs900", "tlcs900 sleigh", "ghidra tlcs-900", "tlcs900h", "tlcs-900"
found no other Ghidra module (only disassemblers, emulators and toolchains: jounikor/ngdis, Tixul/NgpCraft_Disasm,
felipesanches/binutils-tlcs900, FluBBaOfWard/TLCS900H, jotego/jt900h, SingleStepTests/tlcs900h).

## Ghidra-Rare changes
1. The instruction tables are restructured and generated (`tools/gen/`). Upstream wrote each constructor once per
   addressing mode in `tlcs900h.sinc`, `src_mem.sinc`, `dst_mem.sinc` and `reg.sinc`. The generated tables use one
   register-prefix subtable per form and one memory-operand subtable per addressing form, and repeat each instruction
   per form, because SLEIGH cannot constrain the operation byte that follows a variable-length operand. The macros
   keep upstream's structure. Decode fixes (all found by the differential tests below and checked against the manual):
   - JRL/CALR targets no longer wrap inside a 64 KB page.
   - LDX is 6 bytes (F7 00 n 00 # 00).
   - MUL/MULS/DIV/DIVS name the double-size register RR. Byte forms take an odd R only. The long-word forms,
     which do not exist, are no longer decoded.
   - RET cc is B0 F0+cc only.
   - LD (mem),(#16) with code 16H is a word load.
   - LDI/LDD/LDIR/LDDR are decoded only for 83+zz and 85+zz.
   - CPI/CPD/CPIR/CPDR show their 32-bit pointer register.
   - SCC/CPL/NEG/EX R,r/CP r,#3 have no 32-bit form.
   - Undefined register codes are rejected: 40H-CFH; odd word codes; long codes that are not a multiple of 4;
     (-r)/(r+) increment code 11; (r32) sub-modes other than r32+d16/r32+r8/r32+r16; #3/#4 fields with high bits set.
   - (r32+r8) and (r32+r16) take the index as signed.
   - LDAR (F3 13 d16) is new.
   - MINCn/MDECn show and use the encoded # - n correctly.
   - Control register 3CH is INTNEST, which replaces XNSP on the 900/H.
   - JP/CALL/RET/JR/JRL with cc=T are unconditional.
2. Semantics. Memory operands of every size had been read and written as 32 bits. LDI/LDD copied 4 bytes and
   incremented before the copy. STCF could not clear a bit, and CHG cleared the register. Multi-bit RL/RR ignored the
   carry. Shift counts did not treat 0 as 16, and the A-register count used all of A. DIV by zero divided by zero.
   CPx updated the wrong register. DAA, RLD/RRD, MULA, BS1F/BS1B, MIRR, MINC/MDEC, LINK/UNLK, SWI (vector at
   FFFF00H + 4n), RETI and LDAR were rewritten from the manual.
3. Register banks. Banks 0-3 and the previous bank were separate storage that never aliased the current bank. The
   explicit bank codes (00H-3FH, D0H-DFH) are now resolved against RFP at run time, and LDF/INCF/DECF/POP SR/RETI
   store and load the banks.
4. Flags. The flags are separate registers (SF ZF HF VF NF CF) that PUSH/POP SR/F, EX F,F', SWI and RETI pack into
   F, which lets the decompiler read the conditions. V for ADD/SUB/CP uses scarry/sborrow.
5. cspec: the cc900 stack convention (results in L/HL/XHL; XIX/XIY/XIZ preserved). pspec: register groups.
6. `ghidra_scripts/NeoGeoPocketCartridge.java`: header labels, read-only cartridge block and start address for
   Neo Geo Pocket images imported raw at 200000H.
7. The compiled `tlcs900h.sla` is no longer tracked. Build files (`build.gradle`, `extension.properties`, extension
   name `TLCS900H`), `test/`, `GHIDRA-RARE.md` and this file are added, and the README is updated (limitations, Ghidra
   version, install).

## Sources and tools
- Toshiba "TLCS-900 CPU" core book, covering the 900, 900/L and 900/H cores: Appendix A (register maps, memory
  addressing mode codes), Appendix B (instruction lists) and Appendix C (code maps). The TLCS-900/H2 CPU book was
  used for the 900/H-only details and the per-instruction pages. Both are on bitsavers
  (http://bitsavers.org/components/toshiba/_dataSheet/TLCS900hv-is.pdf and TLCS900h2-is.pdf). They are not
  redistributed here.
- MAME's `unidasm -arch tlcs900` (mame-tools 0.285), used as a black box; MAME source not read.
- asl, Alfred Arnold's macro assembler (1.42 Bld 315, CPU 96C141), used as a black box. It assembled the emulator
  test cases and checked the module's disassembly round trip. asl source not read for encodings.
- Real code: Stargunner (Tixul, MIT) and Pengu (Steven MacDonald / underscore42, MIT), Neo Geo Pocket Color homebrew,
  fetched by `test/fetch-real.sh` at pinned commits and SHA-256. Not committed.
