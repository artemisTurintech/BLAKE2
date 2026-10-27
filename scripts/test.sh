#!/bin/sh
# Run the sse/ known-answer self-tests (keyed KATs for all six variants).
set -e
cd "$(dirname "$0")/.."
. scripts/env.sh

make -C sse CFLAGS="$BLAKE2_CFLAGS" check
