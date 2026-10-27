#!/usr/bin/env bash
# Decode a corpus of fixed-size slots with the module, in pieces loaded at their own offset (so relative branch
# targets are those of the whole corpus loaded at address 0).
#   decode-corpus.sh <language-id> <corpus.bin> <out.txt> <slot-size> [Script.java]
# Output: "<slot> <length> <text>" per slot (global slot numbers); with Reach.java the sorted constructor list.
set -euo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
export LANG_ID=$1 SLOT=$4 SCRIPT=${5:-DumpSlots.java} HERE
CORPUS=$2 OUT=$3
JOBS=${JOBS:-4}
D=$(mktemp -d "${TMPDIR:-/tmp}/decode-corpus.XXXXXX")
trap 'rm -rf "$D"' EXIT
PIECE=$((262144 / SLOT * SLOT))
split -b "$PIECE" -d -a 4 "$CORPUS" "$D/p."
for f in "$D"/p.????; do printf "%s 0x%x\n" "$f" $((10#${f##*.} * PIECE)); done |
	xargs -P "$JOBS" -n 2 bash -c 'BASE_ADDR=$1 "$HERE/ghidra-script.sh" raw "$LANG_ID" "$0" "$SCRIPT" "$0.out" "$SLOT"'
if [[ $SCRIPT == Reach.java ]]; then
	cat "$D"/p.????.out | sort -u > "$OUT"
	exit 0
fi
: > "$OUT"
for f in "$D"/p.????; do
	python3 -I -c '
import sys
off = int(sys.argv[2])
for l in open(sys.argv[1]):
    if l.startswith("    "):
        sys.stdout.write(l); continue
    i, rest = l.split(" ", 1)
    sys.stdout.write(f"{int(i) + off} {rest}")' "$f.out" $((10#${f##*.} * PIECE / SLOT)) >> "$OUT"
done
