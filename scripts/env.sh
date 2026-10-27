# Shared settings for compile.sh, test.sh and benchmark.sh. Source, don't run.
# Puts the scoop mingw toolchain on PATH when present (Windows runner).
if [ -d "$HOME/scoop/apps/mingw/current/bin" ]; then
  PATH="$HOME/scoop/apps/mingw/current/bin:$PATH"
fi
export PATH

# Tests and benchmark build the sse/ code with the same flags so both
# exercise the same SIMD code paths.
BLAKE2_CFLAGS="-O3 -march=native -I../testvectors -Wall -Wextra -std=c89 -pedantic -Wno-long-long"
