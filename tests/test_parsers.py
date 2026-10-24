import pytest
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Callable

from streamstats import errors, models, parsers, analysis


FILES = Path(__file__).parent / "files"


def collect(parser, path, analyzer = None):
    if analyzer is None:
        analyzer = analysis.Analyzer()
    for line, item in parser(path):
        if isinstance(item, errors.InvalidEventError):
            analyzer.skip()
        else:
            analyzer.add(item)
    return analyzer
# Valid jsonl|csv
def check_valid(analyzer):
    assert analyzer.total == 5
    assert analyzer.by_level == Counter({"DEBUG": 1, "INFO": 1, "WARNING": 1, "ERROR": 1, "CRITICAL": 1})
    assert analyzer.by_source == Counter({ "auth-service": 2, "api-gateway": 1,"db-pool": 1, "payment-service": 1})
    assert analyzer.error_sources == Counter({"auth-service": 1, "payment-service": 1})
    assert analyzer.first_ts == datetime.fromisoformat("2023-10-24T10:00:00+00:00")
    assert analyzer.last_ts == datetime.fromisoformat("2023-10-24T10:04:00+00:00")
    assert analyzer.skipped == 0
def test_valid_jsonl():
    check_valid(collect(parsers.parse_jsonl, FILES / "valid.jsonl"))
def test_valid_csv():
    check_valid(collect(parsers.parse_csv, FILES / "valid.csv"))


# >=2 files tests
def test_two_files_united():
    analyzer = analysis.Analyzer()
    collect(parsers.parse_jsonl, FILES/"valid.jsonl", analyzer)
    collect(parsers.parse_jsonl, FILES/"valid2.jsonl", analyzer)
    assert analyzer.total == 8
    assert analyzer.by_level == Counter({"DEBUG": 2, "INFO": 2, "ERROR": 2, "WARNING": 1, "CRITICAL": 1})
    assert analyzer.by_source == Counter({"auth-service": 2, "db-pool": 1, "cache-layer": 1, "notification-worker": 1, "metrics-collector": 1, "api-gateway": 1, "payment-service": 1})
    assert analyzer.error_sources == Counter({"auth-service": 1, "payment-service": 1, "notification-worker": 1})
    assert analyzer.first_ts == datetime.fromisoformat("2023-10-24T10:00:00+00:00")
    assert analyzer.last_ts == datetime.fromisoformat("2023-10-24T11:10:00+00:00")
    assert analyzer.skipped == 0

# check mix
def check_mix(analyzer, skipped):
    assert analyzer.total == 2
    assert analyzer.skipped == skipped
    assert analyzer.by_level == Counter({"INFO": 2})
    assert analyzer.by_source == Counter({"mix-test": 2})
    assert analyzer.error_sources == Counter()      # единственное ERROR-событие плохое
    assert analyzer.first_ts == datetime.fromisoformat("2023-10-24T12:00:00+00:00")
    assert analyzer.last_ts == datetime.fromisoformat("2023-10-24T12:03:00+00:00")
def test_mix_jsonl_counts():
    check_mix(collect(parsers.parse_jsonl, FILES / "mix.jsonl"), skipped=3)
def test_mix_csv_counts():
    check_mix(collect(parsers.parse_csv, FILES / "mix.csv"), skipped=2)
def test_mix_jsonl_items():
    items = list(parsers.parse_jsonl(FILES / "mix.jsonl"))
    assert [n for n, _ in items] == [1, 2, 3, 5, 6]
    bad = [n for n, item in items if isinstance(item, errors.InvalidEventError)]
    assert bad == [2, 3, 5]
def test_mix_csv_items():
    items = list(parsers.parse_csv(FILES / "mix.csv"))

    # заголовок это строка 1, поэтому данные идут с 2
    assert [n for n, _ in items] == [2, 3, 4, 5]
    bad = [n for n, item in items if isinstance(item, errors.InvalidEventError)]
    assert bad == [3, 4]

# Unicode test
def check_unicode(analyzer):
    assert analyzer.total == 2
    assert analyzer.skipped == 0
    assert analyzer.by_level == Counter({"ERROR": 1, "INFO": 1})
    assert analyzer.by_source == Counter({"сервис-Ёж": 2})
    assert analyzer.error_sources == Counter({"сервис-Ёж": 1})
    # 14:00+03:00 это 11:00 UTC
    assert analyzer.first_ts == datetime.fromisoformat("2023-10-24T11:00:00+00:00")
    assert analyzer.last_ts == datetime.fromisoformat("2023-10-24T11:01:00+00:00")
def test_unicode_jsonl_counts():
    check_unicode(collect(parsers.parse_jsonl, FILES / "unicode.jsonl"))
def test_unicode_csv_counts():
    check_unicode(collect(parsers.parse_csv, FILES / "unicode.csv"))
def check_unicode_messages(items):
    events = [item for _, item in items]
    assert [e.source for e in events] == ["сервис-Ёж", "сервис-Ёж"]
    assert events[0].message == "Ошибка подключения к БД: таймаут"
    assert events[1].message == "Повторное подключение успешно"
def test_unicode_jsonl_messages():
    check_unicode_messages(list(parsers.parse_jsonl(FILES / "unicode.jsonl")))
def test_unicode_csv_messages():
    check_unicode_messages(list(parsers.parse_csv(FILES / "unicode.csv")))


# empty files
def check_empty(analyzer):
    assert analyzer.total == 0
    assert analyzer.skipped == 0
    assert analyzer.by_level == Counter()
    assert analyzer.by_source == Counter()
    assert analyzer.error_sources == Counter()
    assert analyzer.first_ts is None
    assert analyzer.last_ts is None
def test_empty_jsonl():
    assert list(parsers.parse_jsonl(FILES / "empty.jsonl")) == []
    check_empty(collect(parsers.parse_jsonl, FILES / "empty.jsonl"))
def test_empty_csv():
    assert list(parsers.parse_csv(FILES / "empty.csv")) == []
    check_empty(collect(parsers.parse_csv, FILES / "empty.csv"))
def test_csv_header_only(tmp_path):
    path = tmp_path / "header_only.csv"
    path.write_text("timestamp,level,source,message\n", encoding="utf-8")
    assert list(parsers.parse_csv(path)) == []
    check_empty(collect(parsers.parse_csv, path))
def test_jsonl_only_blank_lines(tmp_path):
    path = tmp_path / "blank.jsonl"
    path.write_text("\n   \n\n", encoding="utf-8")

    assert list(parsers.parse_jsonl(path)) == []
    check_empty(collect(parsers.parse_jsonl, path))
