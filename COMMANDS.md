# Build, test and benchmark commands

Run every command from the repository root in a POSIX shell (on Windows, Git Bash).

| Phase | Command | Typical time |
|---|---|---|
| Compile | `sh scripts/compile.sh` | ~9 s |
| Test | `sh scripts/test.sh` | ~5 s |
| Benchmark | `sh scripts/benchmark.sh` | ~17 s |

Run them in this order: the benchmark uses the program that the compile step builds.

## Prerequisites

- `gcc`, `make` and `sh` on PATH. On Windows, `scripts/env.sh` adds the scoop mingw toolchain (`~/scoop/apps/mingw/current/bin`) to PATH when it is installed.
- An x86 CPU with SSE2 or later. The code is built with `-march=native`.

## Compile

```sh
sh scripts/compile.sh
```

Builds the six `sse/` self-test programs (`blake2s`, `blake2b`, `blake2sp`, `blake2bp`, `blake2xs`, `blake2xb`) and the benchmark program `bench/artemis_bench`, all with `-O3 -march=native`.

## Test

```sh
sh scripts/test.sh
```

Runs `make -C sse check`. Each self-test checks its variant against the known-answer test vectors in `testvectors/` and prints `ok`. A wrong result makes the command exit non-zero.

## Benchmark

```sh
sh scripts/benchmark.sh
```

Times the `sse/` implementations of blake2b, blake2s, blake2bp and blake2sp on 64 B, 1 KB, 64 KB and 1 MB messages. Each measurement is the median of 9 timed runs, after a warm-up. The script deletes any old `artemis_results.json`, then writes a new one in the repository root:

| Metric | Meaning | Better |
|---|---|---|
| `<algo>_<size>_mb_s` | Throughput in MB/s (1 MB = 10^6 bytes), e.g. `blake2b_1kb_mb_s` | Higher |
| `overall_mb_s` | Geometric mean of all 16 throughputs | Higher |
| `overall_ns_per_byte` | `1000 / overall_mb_s` | Lower |

Because of `-march=native`, compare results only between runs on the same machine.

### Key metric: `overall_mb_s`

`overall_mb_s` is the number that ranks versions: how fast the repository's own `sse/` C code hashes data, in MB/s. Higher is better. The baseline on the development machine is about 549 MB/s. `overall_ns_per_byte` reports the same thing inverted, so use only one of the two.

It is the geometric mean of 16 results: 4 algorithms (blake2b, blake2s, blake2bp, blake2sp), each at 4 message sizes (64 B, 1 KB, 64 KB, 1 MB). Each of the 16 has equal weight, so a 10% gain on any one of them raises the score by the same amount. The score therefore rewards two kinds of improvement:

- **Short messages (64 B)** are dominated by the fixed cost of each call: setting up state and padding the last block. blake2bp and blake2sp are slowest here (about 50–77 MB/s, against about 420–540 MB/s for blake2b and blake2s) because they set up 4 or 8 internal hash states even for a tiny input. These results are the easiest to improve.
- **Large messages (64 KB, 1 MB)** measure the speed of the compression function: about 1000 MB/s for blake2b and 725 MB/s for blake2s. Gains here come from the SIMD round code in `sse/blake2b-round.h` and `sse/blake2s-round.h`.

If only one case matters, for example hashing large files, rank versions by that case's metric (such as `blake2b_1mb_mb_s`) instead of `overall_mb_s`, or remove the 64 B size from `SIZES` in `bench/artemis_bench.c`. Otherwise, changes that only speed up short messages can raise the score without helping that case.

## Artemis Script

```sh
artemis project scripts create --project "<project-uuid>" --name "BLAKE2 sse" \
  --setup-cmd "sh scripts/compile.sh" \
  --setup-cmd "sh scripts/test.sh" \
  --benchmark-cmd "sh scripts/benchmark.sh" \
  --measure none
```
