from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Literal

from streamstats.constants import LEVELS, REQUIRED_FIELDS
from streamstats.errors import InvalidEventError, InvalidTimestampError


@dataclass(frozen=True, slots=True)
class Event:
    timestamp: datetime
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    source: str
    message: str

    @classmethod
    def from_dict(cls, data: object) -> "Event":
        if not isinstance(data, dict): 
            raise InvalidEventError("Данные события должны быть словарём")

        for field in sorted(REQUIRED_FIELDS):
            if field not in data:
                raise InvalidEventError(f"Отсутсвует обязательное поле: {field}")
            
        if not isinstance(data.get("level"), str) or data["level"] not in LEVELS:
            raise InvalidEventError(f"Недопустимые значения {sorted(LEVELS)}")
        
        if not isinstance(data.get("source"), str) or not data["source"].strip():
            raise InvalidEventError('Поле "source" не может быть пустым или отсутствовать')
        
        if not isinstance(data["message"], str):
            raise InvalidEventError('Поле "message" должно быть строкой')

        ts = data["timestamp"]
        if isinstance(ts, datetime):
            dt = ts
        elif isinstance(ts, str):
            if ts and ts[-1] == "Z": ts = ts[:-1] + "+00:00"
            try:
                dt = datetime.fromisoformat(ts)
            except (ValueError, TypeError) as e:
                raise InvalidTimestampError("Некорректный формат времени (Ожидается ISO8601)") from e
        else:
            raise InvalidTimestampError("Время должно быть строкой или datetime")

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        
        
        return cls(timestamp = dt, 
        level = data["level"],
        source = data["source"], 
        message = data["message"])



