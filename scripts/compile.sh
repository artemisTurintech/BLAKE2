#!/bin/sh
# Build the sse/ self-test binaries and the Artemis benchmark harness.
set -e
cd "$(dirname "$0")/.."
. scripts/env.sh

make -C sse -B CFLAGS="$BLAKE2_CFLAGS" blake2s blake2b blake2sp blake2bp blake2xs blake2xb
gcc -O3 -march=native -Wall -Wextra -o bench/artemis_bench \
  bench/artemis_bench.c sse/blake2b.c sse/blake2s.c sse/blake2bp.c sse/blake2sp.c -lm
