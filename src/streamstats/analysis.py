from collections import Counter
from datetime import datetime

from streamstats.models import Event


class Analyzer:
    def __init__(self) -> None:
        self.total: int = 0

        self.by_level: Counter[str] = Counter()
        self.by_source: Counter[str] = Counter()

        self.error_sources: Counter[str] = Counter()

        self.first_ts: datetime = None
        self.last_ts: datetime = None

        self.skipped: int = 0


    def add(self, event: Event) -> None:
        self.total += 1

        self.by_level[event.level] += 1
        self.by_source[event.source] += 1

        if event.level in ("ERROR", "CRITICAL"):
            self.error_sources[event.source] += 1

        if self.first_ts is None or event.timestamp < self.first_ts:
            self.first_ts = event.timestamp
        if self.last_ts is None or event.timestamp > self.last_ts:
            self.last_ts = event.timestamp

    def skip(self) -> None:
        self.skipped += 1


