"""MedPerf's confidential computing glue.

`medperf_cc` knows nothing about benchmarks, datasets or models. This layer
translates: entity configuration into the components that act on it, benchmark
associations into the workloads an asset owner permits, and the client's own
storage, encryption and UI conventions into what those components are handed.
"""
