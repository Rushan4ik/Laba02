import json
from pathlib import Path

from streamstats.analysis import Analyzer


def build_report(analis: Analyzer) -> dict:
    return {
        "total_events": analis.total,
        "by_level": dict(analis.by_level),
        "by_source": dict(analis.by_source),
        "top_error_sources": [
            {"source": src, "count": cnt} for src, cnt in analis.error_sources.most_common(5)
        ],
        "first_timestamp": analis.first_ts.isoformat() if analis.first_ts else None,
        "last_timestamp": analis.last_ts.isoformat() if analis.last_ts else None,
        "skipped_lines": analis.skipped,
    }


def write_report(report: dict, path: Path | None) -> None:
    if path is not None:
        with open(path, 'w', encoding='utf-8') as rep:
            json.dump(report, rep, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))




