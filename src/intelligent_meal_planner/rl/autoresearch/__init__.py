"""Autoresearch module for DQN training loop automation."""

from .benchmark import (
    BenchmarkCase,
    get_default_benchmark_cases,
    compute_score,
    generate_report,
)

__all__ = [
    "BenchmarkCase",
    "get_default_benchmark_cases",
    "compute_score",
    "generate_report",
]
