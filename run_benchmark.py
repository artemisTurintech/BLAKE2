"""
Benchmark hashlib.blake2b and hashlib.blake2s across message sizes.

Metrics
-------
throughput_mb_s  : megabytes hashed per second  (higher is better)
latency_us       : microseconds per single hash call (lower is better)

Both metrics are reported as mean ± stdev across REPEAT trials.
"""

import hashlib
import json
import math
import os
import secrets
import timeit

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
NUMBER = 1_000   # hash calls per trial
REPEAT = 7       # number of trials

# Message sizes exercising short-message overhead through bulk throughput
DATA_SIZES = {
    "64B":  64,
    "1KB":  1_024,
    "64KB": 65_536,
    "1MB":  1_048_576,
}

ALGORITHMS = {
    "blake2b": hashlib.blake2b,
    "blake2s": hashlib.blake2s,
}

# ---------------------------------------------------------------------------
# Prepare input data once — excluded from timing
# ---------------------------------------------------------------------------
payloads = {label: secrets.token_bytes(size) for label, size in DATA_SIZES.items()}


def _mean_stdev(values):
    n = len(values)
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / (n - 1)
    return mean, math.sqrt(variance)


def run_one(algo_fn, data):
    """Return (throughput_mb_s_mean, stdev, latency_us_mean, stdev)."""
    size = len(data)

    # timeit.repeat returns total wall-time for NUMBER calls, repeated REPEAT times
    raw = timeit.repeat(
        stmt=lambda: algo_fn(data).digest(),
        number=NUMBER,
        repeat=REPEAT,
    )

    # seconds per single call → microseconds
    latencies_us = [t / NUMBER * 1e6 for t in raw]
    # bytes per second → megabytes per second
    throughputs_mb_s = [NUMBER * size / t / 1e6 for t in raw]

    lat_mean, lat_sd = _mean_stdev(latencies_us)
    tp_mean, tp_sd = _mean_stdev(throughputs_mb_s)
    return tp_mean, tp_sd, lat_mean, lat_sd


# ---------------------------------------------------------------------------
# Run benchmarks
# ---------------------------------------------------------------------------
rows = []

print(f"BLAKE2 Python benchmark  (number={NUMBER}, repeat={REPEAT})\n")
header = f"{'algorithm':<10} {'size':<6}  {'MB/s mean':>12}  {'MB/s ±':>10}  {'µs/hash mean':>14}  {'µs/hash ±':>10}"
print(header)
print("-" * len(header))

for algo_name, algo_fn in ALGORITHMS.items():
    for size_label, data in payloads.items():
        tp_mean, tp_sd, lat_mean, lat_sd = run_one(algo_fn, data)

        print(
            f"{algo_name:<10} {size_label:<6}  "
            f"{tp_mean:>12.1f}  {tp_sd:>10.1f}  "
            f"{lat_mean:>14.3f}  {lat_sd:>10.4f}"
        )

        rows.append(
            {
                "algorithm": algo_name,
                "message_size": size_label,
                "message_size_bytes": DATA_SIZES[size_label],
                "number": NUMBER,
                "repeat": REPEAT,
                "throughput_mb_s": round(tp_mean, 3),
                "throughput_mb_s_stdev": round(tp_sd, 3),
                "latency_us": round(lat_mean, 4),
                "latency_us_stdev": round(lat_sd, 5),
            }
        )

# ---------------------------------------------------------------------------
# Persist
# ---------------------------------------------------------------------------
output_path = os.path.join(os.path.dirname(__file__), "artemis_results.json")
with open(output_path, "w") as f:
    json.dump(rows, f, indent=2)

print(f"\nResults written to {output_path}")
