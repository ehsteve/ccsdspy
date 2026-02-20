"""Benchmark variable-length packet parsing with and without Cython helper."""

from __future__ import annotations

import argparse
import os
import time
from contextlib import contextmanager

import ccsdspy
import ccsdspy.decode as decode
from ccsdspy import PacketArray, PacketField, VariableLength


def _default_data_path() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(
        root,
        "ccsdspy",
        "tests",
        "data",
        "var_length",
        "var_length_packets_double_varfield_with_footer.bin",
    )


def _build_packet() -> VariableLength:
    return VariableLength(
        [
            PacketField(name="data1_len", data_type="uint", bit_length=8),
            PacketArray(name="data1", data_type="uint", bit_length=16, array_shape="data1_len"),
            PacketField(name="data2_len", data_type="uint", bit_length=8),
            PacketArray(name="data2", data_type="uint", bit_length=16, array_shape="data2_len"),
            PacketField(name="footer", data_type="uint", bit_length=16),
        ]
    )


@contextmanager
def _force_scanner(mode: str):
    original_loader = decode._load_cython_packet_starts

    if mode == "python":
        decode._load_cython_packet_starts = lambda: None
    elif mode == "cython":
        cython_impl = original_loader()
        if cython_impl is None:
            raise RuntimeError("Cython scanner is not available in this environment.")
        decode._load_cython_packet_starts = lambda: cython_impl
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    try:
        yield
    finally:
        decode._load_cython_packet_starts = original_loader


def _time_mode(path: str, iterations: int, warmup: int, mode: str):
    packet = _build_packet()

    with _force_scanner(mode):
        for _ in range(warmup):
            packet.load(path, include_primary_header=False)

        start = time.perf_counter()
        for _ in range(iterations):
            arrays = packet.load(path, include_primary_header=False)
        elapsed = time.perf_counter() - start

    npackets = len(arrays["footer"])
    return elapsed, npackets


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file",
        default=_default_data_path(),
        help="Path to variable-length packet file",
    )
    parser.add_argument("--iterations", type=int, default=300, help="Measured iterations per mode")
    parser.add_argument("--warmup", type=int, default=20, help="Warmup iterations per mode")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        raise FileNotFoundError(f"Data file does not exist: {args.file}")

    py_seconds, npackets = _time_mode(args.file, args.iterations, args.warmup, "python")
    py_us = py_seconds / args.iterations * 1e6

    print(f"ccsdspy version: {ccsdspy.__version__}")
    print(f"file: {args.file}")
    print(f"packets per iteration: {npackets}")
    print(f"iterations: {args.iterations} (warmup={args.warmup})")
    print()
    print(f"python scanner: {py_us:.2f} us/iter")

    try:
        cy_seconds, _ = _time_mode(args.file, args.iterations, args.warmup, "cython")
    except RuntimeError as exc:
        print(f"cython scanner: unavailable ({exc})")
        return

    cy_us = cy_seconds / args.iterations * 1e6
    speedup = py_seconds / cy_seconds if cy_seconds > 0 else float("inf")
    print(f"cython scanner: {cy_us:.2f} us/iter")
    print(f"speedup: {speedup:.2f}x")


if __name__ == "__main__":
    main()
