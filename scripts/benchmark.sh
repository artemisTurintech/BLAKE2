#!/bin/sh
# Time the sse/ BLAKE2 implementations and write artemis_results.json.
# Expects scripts/compile.sh to have built bench/artemis_bench.
set -e
cd "$(dirname "$0")/.."

rm -f artemis_results.json artemis_results.json.tmp
./bench/artemis_bench artemis_results.json.tmp
mv artemis_results.json.tmp artemis_results.json
