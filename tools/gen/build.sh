#!/usr/bin/env bash
# Regenerates data/languages/tlcs900h.sinc from the pieces in this directory:
#   head.sinc    tokens and register-code attach tables (the attach tables come from attach.py)
#   body1.sinc   register-code and prefix subtables; @@EA@@ is replaced by the memory-operand subtables (gen_ea.py)
#   macros.sinc  operation macros
#   gen_ins.py   instruction constructors, repeated for every prefix form
#   build.sh [out.sinc]   (default: ../../data/languages/tlcs900h.sinc)
set -euo pipefail
cd "$(dirname "$0")"
OUT=$(readlink -m "${1:-../../data/languages/tlcs900h.sinc}")
T=$(mktemp -d "${TMPDIR:-/tmp}/tlcs900h-gen.XXXXXX")
trap 'rm -rf "$T"' EXIT
python3 -I gen_ea.py "$T"
python3 -I gen_ins.py "$T" >/dev/null
python3 -I - "$T" "$OUT" <<'PY'
import sys
t, out = sys.argv[1:]
b = open('body1.sinc').read().replace('@@EA@@\n', open(t + '/ea.sinc').read())
open(out, 'w').write(open('head.sinc').read() + b + open('macros.sinc').read() + open(t + '/ins.sinc').read())
PY
