"""Result persistence helpers."""

from __future__ import annotations

from pathlib import Path

from src.results_io import environment_snapshot, write_json


def test_write_json_and_environment(tmp_path: Path):
    payload = {"ok": True, "values": [1, 2]}
    path = tmp_path / "out.json"
    write_json(path, payload)
    assert path.exists()
    env = environment_snapshot(Path(__file__).resolve().parents[1])
    assert "versions" in env
    assert "qiskit" in env["versions"]
