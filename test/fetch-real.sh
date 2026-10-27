#!/usr/bin/env bash
# Fetch the freely licensed (MIT) Neo Geo Pocket Color homebrew used by the real-code check, at pinned commits with
# pinned SHA-256. Nothing fetched here is committed.
#   test/fetch-real.sh <dir>
set -euo pipefail
D=${1:?dir}
mkdir -p "$D"
get() {   # url sha256 name
	[[ -f $D/$3 ]] || curl -sSfL -o "$D/$3" "$1"
	echo "$2  $D/$3" | sha256sum -c --quiet
}
# Stargunner, Tixul (MIT, https://github.com/Tixul/Stargunner), built with Toshiba cc900
get https://raw.githubusercontent.com/Tixul/Stargunner/de49e240e7b715f1d1f666931b1ad082adff5069/Stargunner.ngc \
	089e2d9520dc2f84d34a33b1dfa1710eb9a429d90b3b0a195a06ccab89c9022f Stargunner.ngc
# Pengu, Steven MacDonald / underscore42 (MIT, https://github.com/underscore42/pengu)
get https://raw.githubusercontent.com/underscore42/pengu/acf16c8878bd2074f0b9969623c38b5987c08b0a/releases/pengu.ngp \
	7167463d0c0badddcd4eea3aee7b6d4d647e8e86b7b0e6c62ea7215f87ad696b pengu.ngp
