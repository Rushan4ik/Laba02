import json
import os
import subprocess
import sys
from pathlib import Path

SRC = Path(__file__).parent.parent / "src"
FILES = Path(__file__).parent / "files"   # там лежат for_cli.jsonl и for_cli.csv
BAD_LINE = {"jsonl": 2, "csv": 3}         # номер плохой строки в for_cli.*


def run_cli(*args):
    """Запускает настоящий процесс `python -m streamstats ...`."""
    env = {**os.environ, "PYTHONPATH": str(SRC), "PYTHONUTF8": "1"}
    return subprocess.run(
        [sys.executable, "-m", "streamstats", *map(str, args)],
        capture_output=True, text=True, encoding="utf-8", env=env,
    )


def test_default_mode_stops_on_bad_line(tmp_path):
    for fmt in ("jsonl", "csv"):
        out = tmp_path / f"report_{fmt}.json"

        result = run_cli("analyze", FILES / f"for_cli.{fmt}", "--format", fmt, "--output", out)

        assert result.returncode == 2, fmt
        assert f"строка {BAD_LINE[fmt]}" in result.stderr, fmt
        assert not out.exists(), fmt


def test_skip_invalid_and_unicode(tmp_path):
    for fmt in ("jsonl", "csv"):
        out = tmp_path / f"report_{fmt}.json"

        result = run_cli("analyze", FILES / f"for_cli.{fmt}", "--format", fmt,
                         "--output", out, "--skip-invalid")

        raw = out.read_text(encoding="utf-8")
        report = json.loads(raw)
        assert result.returncode == 0, fmt
        assert report["total_events"] == 2, fmt
        assert report["skipped_lines"] == 1, fmt
        assert report["by_source"] == {"сервис-Ёж": 1, "db": 1}, fmt
        assert "сервис-Ёж" in raw and "\\u04" not in raw, fmt   # кириллица записана читаемо
        assert result.stderr.count("WARNING") == 1, fmt


def test_two_files_are_united(tmp_path):
    src = FILES / "for_cli.jsonl"
    out = tmp_path / "report.json"

    result = run_cli("analyze", src, src, "--format", "jsonl", "--output", out, "--skip-invalid")

    report = json.loads(out.read_text(encoding="utf-8"))
    assert result.returncode == 0
    assert report["total_events"] == 4
    assert report["skipped_lines"] == 2
    assert report["by_source"] == {"сервис-Ёж": 2, "db": 2}


def test_empty_file(tmp_path):
    src = tmp_path / "empty.jsonl"
    src.write_text("", encoding="utf-8")
    out = tmp_path / "report.json"

    result = run_cli("analyze", src, "--format", "jsonl", "--output", out)

    report = json.loads(out.read_text(encoding="utf-8"))
    assert result.returncode == 0
    assert report["total_events"] == 0
    assert report["first_timestamp"] is None


def test_errors_that_always_stop(tmp_path):
    no_level = tmp_path / "no_level.csv"
    no_level.write_text("timestamp,source,message\n", encoding="utf-8")

    assert run_cli("analyze", FILES / "for_cli.jsonl", "--format", "xml").returncode == 2
    assert run_cli("analyze", tmp_path / "nope.jsonl", "--format", "jsonl").returncode == 2
    assert run_cli("analyze", no_level, "--format", "csv", "--skip-invalid").returncode == 2