"""Persistence helpers for PoC results."""

from __future__ import annotations

import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def git_commit(repo: Path) -> str | None:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=repo, text=True, stderr=subprocess.DEVNULL
            ).strip()
        )
    except Exception:  # noqa: BLE001
        return None


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, cls=NumpyEncoder), encoding="utf-8")


def environment_snapshot(repo: Path) -> dict[str, Any]:
    versions = {"python": sys.version}
    for mod in [
        "qiskit",
        "qiskit_aer",
        "qiskit_ibm_runtime",
        "numpy",
        "scipy",
        "pandas",
        "matplotlib",
    ]:
        try:
            versions[mod] = __import__(mod).__version__
        except Exception as exc:  # noqa: BLE001
            versions[mod] = f"unavailable: {exc}"
    return {
        "captured_at_utc": utc_now(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "git_commit": git_commit(repo),
        "versions": versions,
    }
