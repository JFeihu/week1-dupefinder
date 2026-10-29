"""CLI 层测试：只验证「参数进去、结果出来」，不重复测业务逻辑。"""

from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from dupefinder.cli import app

runner = CliRunner()


def test_cli_lists_duplicates(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_bytes(b"same content")
    (tmp_path / "b.txt").write_bytes(b"same content")

    result = runner.invoke(app, ["find", str(tmp_path)])

    assert result.exit_code == 0
    assert "a.txt" in result.stdout


def test_cli_json_output(tmp_path: Path) -> None:
    (tmp_path / "a.bin").write_bytes(b"x" * 10)
    (tmp_path / "b.bin").write_bytes(b"x" * 10)

    result = runner.invoke(app, ["find", str(tmp_path), "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert len(payload) == 1
    assert payload[0]["size"] == 10
    assert payload[0]["wasted"] == 10
    assert len(payload[0]["files"]) == 2


def test_cli_exclude_skips_directory(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_bytes(b"same")
    (tmp_path / "b.txt").write_bytes(b"same")
    (tmp_path / "skip").mkdir()
    (tmp_path / "skip" / "c.txt").write_bytes(b"same")

    result = runner.invoke(app, ["find", str(tmp_path), "--exclude", "skip"])

    assert result.exit_code == 0
    assert "skip" not in result.stdout
