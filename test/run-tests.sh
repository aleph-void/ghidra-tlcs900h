#!/usr/bin/env bash
# TLCS-900/H module test suite.
#
#   GHIDRA_INSTALL_DIR=<Ghidra 12.1.x/12.2> PROJ_DIR=<dir, no path component starting with '.'> test/run-tests.sh [workdir] [--real]
#
# Needs MAME's `unidasm` (black box, -arch tlcs900) on PATH or in UNIDASM, and asl (Alfred Arnold's assembler, black
# box) on PATH or in ASL for the round trip. The module must be visible to Ghidra: installed as an extension, or linked
# as $GHIDRA_INSTALL_DIR/Ghidra/Processors/TLCS900H (the suite links it there for the run if neither exists).
# 1. the generator reproduces data/languages/tlcs900h.sinc   2. the spec compiles
# 3. decode: 491,520 random/structured slots against unidasm; every difference in an explained class
# 4. decode: 271,291 slots (every prefix form x every operation byte) against unidasm; every constructor reached
# 5. asl round trip: the module's text of every decoded slot reassembles to the same bytes or an equivalent encoding
# 6. p-code: hand-computed emulator cases + one wrong expectation that must be reported
# --real: two MIT-licensed Neo Geo Pocket Color games (fetched, pinned SHA-256): headless analysis counts and the
#         listing against unidasm at the same addresses
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
MOD=$(cd "$HERE/.." && pwd)
: "${GHIDRA_INSTALL_DIR:?set GHIDRA_INSTALL_DIR}"
REAL=0
ARGS=()
for a in "$@"; do if [[ $a == --real ]]; then REAL=1; else ARGS+=("$a"); fi; done
W=$(readlink -m "${ARGS[0]:-${TMPDIR:-/tmp}/tlcs900h-tests}")
mkdir -p "$W"
export TMPDIR=$W PROJ_DIR=${PROJ_DIR:-$W} JOBS=${JOBS:-4}
UNIDASM=${UNIDASM:-$(command -v unidasm)}
ASL=${ASL:-$(command -v asl || true)}
export UNIDASM ASL
L=TLCS900H:LE:32:default
fail=0
P="$GHIDRA_INSTALL_DIR/Ghidra/Processors/TLCS900H"
if [[ ! -e $P && ! -e $GHIDRA_INSTALL_DIR/Ghidra/Extensions/TLCS900H ]]; then
	ln -s "$MOD" "$P"
	trap 'rm -f "$P"' EXIT      # a leftover link would collide with the installed extension
fi

echo "== 1. the generator reproduces tlcs900h.sinc"
"$MOD/tools/gen/build.sh" "$W/gen.sinc"
cmp -s "$W/gen.sinc" "$MOD/data/languages/tlcs900h.sinc" || { echo "   tools/gen output differs from data/languages/tlcs900h.sinc"; fail=1; }

echo "== 2. SLEIGH compiles"
"$GHIDRA_INSTALL_DIR/support/sleigh" "$MOD/data/languages/tlcs900h.slaspec" 2>&1 | grep -E "^ERROR|^Error" && exit 1 || true
sz=$(stat -c %s "$MOD/data/languages/tlcs900h.sla"); echo "   tlcs900h.sla: $sz bytes"; ((sz < 16 * 1024 * 1024))

decode() {   # corpus name
	"$HERE/decode-corpus.sh" $L "$W/$1.bin" "$W/$1.gh" 8 &
	PATH=$(dirname "$UNIDASM"):$PATH UNIDASM=$UNIDASM python3 -I "$HERE/unidasm_slots.py" "$W/$1.bin" "$W/$1.uni" 12
	wait
	python3 -I "$HERE/compare.py" "$W/$1.gh" "$W/$1.uni" "$W/$1.bin"
	python3 -I "$HERE/check_explained.py" "$W/$1.gh" "$W/$1.uni" "$W/$1.bin" || fail=1
}
echo "== 3. decode against unidasm: random and structured slots"
python3 -I "$HERE/gen_corpus.py" "$W/all.bin"
decode all

echo "== 4. decode against unidasm: every prefix form x every operation byte; every constructor reached"
python3 -I "$HERE/gen_enum.py" "$W/enum.bin"
decode enum
cat "$W/all.bin" "$W/enum.bin" > "$W/reach.bin"
"$HERE/decode-corpus.sh" $L "$W/reach.bin" "$W/reach.txt" 8 Reach.java
python3 -I "$HERE/reach_check.py" "$MOD/data/languages/tlcs900h.sinc" "$W/reach.txt" || fail=1

echo "== 5. asl round trip of the module's disassembly"
if [[ -n $ASL ]]; then
	rm -rf "$W/rt"
	python3 -I "$HERE/asl_roundtrip.py" asm "$W/all.gh" "$W/all.bin" "$W/rt" >/dev/null
	"$HERE/decode-corpus.sh" $L "$W/rt/alt.bin" "$W/rt/alt.gh" 8
	python3 -I "$HERE/asl_roundtrip.py" check "$W/rt" "$W/rt/alt.gh" || fail=1
else
	echo "   asl not found (set ASL): skipped"; fail=1
fi

echo "== 6. p-code: hand-computed emulator tests"
python3 -I "$HERE/emu_tests.py" "$W/emu"
"$HERE/ghidra-script.sh" raw $L "$W/emu/emu.bin" EmuCheck.java "$W/emu/tests.txt" "$W/emu/out.txt"
echo "   $(tail -1 "$W/emu/out.txt")"
grep -q " 0 failed" "$W/emu/out.txt" || { grep ^FAIL "$W/emu/out.txt" | head -20; fail=1; }
grep -q "[1-9][0-9]* broken expectations detected" "$W/emu/out.txt" || { echo "   the deliberately wrong expectation was not detected"; fail=1; }

if ((REAL)); then
	echo "== 7. real code: MIT-licensed Neo Geo Pocket Color homebrew"
	"$HERE/fetch-real.sh" "$W/real"
	for r in Stargunner.ngc pengu.ngp; do
		BASE_ADDR=0x200000 "$HERE/ghidra-script.sh" raw $L "$W/real/$r" RealCheck.java "$W/real/$r.lst" "$W/real/$r.rep"
		echo "   $r: $(head -1 "$W/real/$r.rep")"
		tail -n +2 "$W/real/$r.rep" | head -5
		python3 -I "$HERE/real_compare.py" "$W/real/$r.lst" "$W/real/$r" 200000 12 | tail -3 || fail=1
	done
fi
if ((fail)); then echo "FAILED"; exit 1; fi
echo "all tests passed"
