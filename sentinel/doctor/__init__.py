"""Sentinel Instruction Doctor - graph analysis, deterministic lints, and safe rewrites."""

from sentinel.doctor.graph import build, LoadGraph, CycleError
from sentinel.doctor.lints import check_file, apply_fixes
from sentinel.doctor import gate

__all__ = ["build", "LoadGraph", "CycleError", "check_file", "apply_fixes", "gate"]
