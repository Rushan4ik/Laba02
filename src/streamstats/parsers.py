import csv
import json
from collections.abc import Iterator
from pathlib import Path

from streamstats.constants import REQUIRED_FIELDS
from streamstats.errors import InvalidEventError, UnsupportedFormatError
from streamstats.models import Event


def parse_jsonl(path: Path) -> Iterator[tuple[int, Event | InvalidEventError]]:
    try:
        with open(path, 'r', encoding='utf-8-sig') as file:
            for line_num, line in enumerate(file, start=1):
                line = line.strip()
                if not line: continue
                try:
                    data = json.loads(line)
                    event = Event.from_dict(data)
                except json.JSONDecodeError as e:
                    yield (line_num, InvalidEventError(f'некорректный JSON: {e.msg}'))
                except InvalidEventError as e:
                    yield (line_num, e)
                else:
                    yield (line_num, event)
    except UnicodeDecodeError as e:
        raise InvalidEventError(f"Битый файл или неверная кодировка: {path.name}") from e
        

def parse_csv(path: Path) -> Iterator[tuple[int, Event | InvalidEventError]]:
    try:
        with open(path, 'r', encoding='utf-8-sig', newline='') as file:
            reader = csv.DictReader(file)
            if reader.fieldnames is None: 
                return #"Пустой файл" #InvalidEventError(f'Пустой файл')
            missing_header = [f for f in sorted(REQUIRED_FIELDS) if f not in reader.fieldnames]
            if missing_header:
                raise InvalidEventError(f'в файле {path!s} в заголовке нет колонок: {", ".join(missing_header)}')
            try:
                for row in reader:
                    try:
                        event = Event.from_dict(row)
                        yield (reader.line_num, event)
                    except InvalidEventError as e:
                        yield (reader.line_num, e)
            except csv.Error as e:
                raise InvalidEventError(f"Ошибка чтения CSV в файле {path!s}: {e}") from e

    except UnicodeDecodeError as e:
        raise InvalidEventError(f"Битый файл или неверная кодировка: {path.name}") from e

PARSERS = {
    "csv": parse_csv,
    "jsonl": parse_jsonl,
}

def get_parser(fmt: str):
        if fmt not in PARSERS:
            raise UnsupportedFormatError(f"Неподдерживаемый формат: {fmt}")
        return PARSERS[fmt]


