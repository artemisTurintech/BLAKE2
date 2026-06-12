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
row = {"runs": REPEAT}
all_throughputs = []
all_latencies = []

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

        all_throughputs.append(tp_mean)
        all_latencies.append(lat_mean)

        prefix = f"{algo_name}_{size_label.lower()}"
        row[f"{prefix}_throughput_mb_s_mean"]        = round(tp_mean, 3)
        row[f"{prefix}_throughput_mb_s_stdev"]       = round(tp_sd, 3)
        row[f"{prefix}_throughput_mb_s_better_when"] = "higher"
        row[f"{prefix}_latency_us_mean"]              = round(lat_mean, 4)
        row[f"{prefix}_latency_us_stdev"]             = round(lat_sd, 5)
        row[f"{prefix}_latency_us_better_when"]       = "lower"

# Overall scores: geometric mean across all algorithm+size combinations.
# Geometric mean weights each combination equally regardless of scale.
def _geomean(values):
    log_mean = sum(math.log(v) for v in values) / len(values)
    return math.exp(log_mean)

overall_tp = _geomean(all_throughputs)
_, overall_tp_sd = _mean_stdev(all_throughputs)

overall_lat = _geomean(all_latencies)
_, overall_lat_sd = _mean_stdev(all_latencies)

print(f"\nOverall throughput score : {overall_tp:.1f} MB/s (geometric mean)")
print(f"Overall latency score    : {overall_lat:.3f} µs  (geometric mean)")

row["overall_throughput_mb_s_mean"]        = round(overall_tp, 3)
row["overall_throughput_mb_s_stdev"]       = round(overall_tp_sd, 3)
row["overall_throughput_mb_s_better_when"] = "higher"
row["overall_latency_us_mean"]              = round(overall_lat, 4)
row["overall_latency_us_stdev"]             = round(overall_lat_sd, 4)
row["overall_latency_us_better_when"]       = "lower"

# ---------------------------------------------------------------------------
# Persist — write to repo root regardless of where this script lives
# ---------------------------------------------------------------------------
repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
output_path = os.path.join(repo_root, "artemis_results.json")
with open(output_path, "w") as f:
    json.dump([row], f, indent=2)

print(f"\nResults written to {output_path}")
