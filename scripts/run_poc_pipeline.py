#!/usr/bin/env python3
"""Run local PoC pipeline (classical → ideal → noisy → benchmark → IBM dry-run)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    print(">>", " ".join(cmd), flush=True)
    subprocess.check_call(cmd, cwd=ROOT)


def main() -> None:
    py = str(ROOT / ".venv" / "bin" / "python")
    run([py, "scripts/run_classical.py"])
    run([py, "scripts/run_simulator.py"])
    run([py, "scripts/run_noisy_simulator.py"])
    run([py, "scripts/run_benchmark.py"])
    run([py, "scripts/run_ibm_quantum.py", "--dry-run"])
    run([py, "scripts/build_report_artifacts.py"])
    print("Local PoC pipeline finished.")


if __name__ == "__main__":
    main()
